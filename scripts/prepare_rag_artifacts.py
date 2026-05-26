from __future__ import annotations

import argparse
import gc
import logging
import sys
import time
from pathlib import Path
from typing import Any


_HERE: Path = Path(__file__).resolve().parent
_PROJECT_ROOT: Path = _HERE.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.cache import CacheManager, query_id_for
from src.dataset_manager import DatasetManager
from src.pipeline import (
    PIPELINE_CONFIGS, RAGPipeline, CORPUS_DIR,
)


from scripts.run_experiments import (
    DATASET_CORPUS_MAPPING,
    DISABLED_CONFIGS,
)

logger: logging.Logger = logging.getLogger("prepare_rag_artifacts")


_BASE_CACHE_DIR: Path = _PROJECT_ROOT / ".cache" / "rag"


def _cleanup_gpu() -> None:
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    except Exception:
        pass


def _cuda_sync_if_needed() -> None:
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.synchronize()
    except Exception:
        pass


def select_configs(
    chunkers: list[str],
    retrievers: list[str],
    use_rerankers: bool,
    disabled_configs: frozenset[str] = frozenset(),
) -> list[tuple[int, str]]:

    out: list[tuple[int, str]] = []
    for opt, name in RAGPipeline.CONFIG_MAP.items():
        cfg: dict[str, Any] = PIPELINE_CONFIGS[name]
        if cfg.get("chunker") == "none":
            continue
        if cfg.get("chunker") not in chunkers:
            continue
        if cfg.get("retriever") not in retrievers:
            continue
        has_rr: bool = cfg.get("reranker", "none") != "none"
        if has_rr != use_rerankers:
            continue
        if name in disabled_configs:
            continue
        out.append((opt, name))
    return out


def prepare_for_combo(
    config_option: int,
    config_name: str,
    questions: list[str],
    query_ids: list[str],
    corpus_dir: Path,
    corpus_prefixes: list[str] | None,
    cache: CacheManager,
    retrieval_models: str,
    reranker_models: str | None,
    top_k: int,
    reranker_top_n: int,
    dataset_name: str = "",
) -> None:

    cfg: dict[str, Any] = dict(PIPELINE_CONFIGS[config_name])
    cfg["top_k"] = top_k
    cfg["reranker_top_n"] = reranker_top_n
    if cfg.get("retriever") == "faiss":
        cfg["embedder"] = retrieval_models
    if reranker_models is not None and cfg.get("reranker") not in (None, "none"):
        cfg["reranker"] = reranker_models


    pipeline: RAGPipeline = RAGPipeline.__new__(RAGPipeline)
    pipeline.config_name = config_name
    pipeline.config = cfg
    pipeline.is_indexed = False
    pipeline._chunks = []
    pipeline.cache = None
    pipeline._cache_query_ids = {}
    pipeline._cache_query_set_hash = ""
    pipeline._cache_keys = {}
    pipeline._cache_only = False
    pipeline._pending_retrieval = {}
    pipeline._pending_reranking = {}
    pipeline._pending_contexts = {}
    pipeline.chunker = pipeline._build_chunker()
    pipeline.embedder = pipeline._build_embedder()
    pipeline.retriever = pipeline._build_retriever()
    pipeline.reranker = pipeline._build_reranker()

    pipeline.llm = _NoLLM()
    from src.prompts import PromptBuilder
    pipeline.prompt_builder = PromptBuilder(version=cfg["prompt_version"])

    pipeline.attach_cache(
        cache,
        query_ids=dict(zip(questions, query_ids)),
        dataset_name=dataset_name,
    )


    pipeline._show_progress = True

    logger.info(
        "==> PREP %s (retriever=%s reranker=%s)",
        config_name, retrieval_models if cfg.get("retriever") == "faiss" else "bm25",
        reranker_models or "none",
    )
    t0: float = time.perf_counter()
    pipeline.build_index(
        corpus_dir=corpus_dir,
        corpus_file_prefixes=corpus_prefixes,
    )


    retr_key: str = pipeline._cache_keys.get("retrieval", "")
    if retr_key and cache.has("retrieval", retr_key, ["retrieved_top_k.jsonl"]):
        if not pipeline._pending_retrieval:
            pipeline._pending_retrieval = cache.load_retrieval(retr_key)
        logger.info(
            "CACHE_PRE_LOAD retrieval [%s] - %d queries available",
            config_name, len(pipeline._pending_retrieval),
        )


    rer_key: str = pipeline._cache_keys.get("reranking", "")
    if rer_key and cache.has("reranking", rer_key, ["reranked_top_n.jsonl"]):
        if not pipeline._pending_reranking:
            pipeline._pending_reranking = cache.load_reranking(rer_key)
        logger.info(
            "CACHE_PRE_LOAD reranking [%s] - %d queries available",
            config_name, len(pipeline._pending_reranking),
        )


    ctx_key: str = pipeline._cache_keys.get("contexts", "")
    if ctx_key and cache.has("contexts", ctx_key, ["contexts.jsonl"]):
        if not pipeline._pending_contexts:
            pipeline._pending_contexts = cache.load_contexts(ctx_key)
            logger.info(
                "CACHE_PRE_LOAD contexts [%s] - %d queries available",
                config_name, len(pipeline._pending_contexts),
            )


    missing_pairs: list[tuple[str, str]] = [
        (q, qid)
        for q, qid in zip(questions, query_ids)
        if qid not in pipeline._pending_contexts
    ]

    if not missing_pairs:
        logger.info(
            "CACHE_HIT [%s] - all %d queries in contexts cache, "
            "skipping query loop (%.2f s)",
            config_name, len(questions), time.perf_counter() - t0,
        )
        return

    logger.info(
        "[%s] %d/%d queries missing from contexts cache - "
        "running retrieval/reranking for missing queries",
        config_name, len(missing_pairs), len(questions),
    )


    try:
        if cfg.get("retriever") == "faiss" and missing_pairs:
            _cuda_sync_if_needed()
            _ = pipeline.embedder.embed_query(missing_pairs[0][0])
            _cuda_sync_if_needed()
            logger.info("[%s] embedder warm-up complete", config_name)


        if cfg.get("reranker") not in (None, "none") and missing_pairs:
            warm_q, warm_qid = missing_pairs[0]
            cached_rows = pipeline._pending_retrieval.get(warm_qid)
            if cached_rows:
                from src.retrieval import RetrievalResult
                warm_results: list[RetrievalResult] = [
                    pipeline._retrieval_result_from_row(r) for r in cached_rows[: min(4, len(cached_rows))]
                ]
                _cuda_sync_if_needed()
                _ = pipeline.reranker.rerank_results(query=warm_q, results=warm_results)
                _cuda_sync_if_needed()
                logger.info("[%s] reranker warm-up complete", config_name)

    except Exception as e:
        logger.warning("[%s] warm-up failed: %s", config_name, e)


    CHECKPOINT_EVERY: int = 50

    try:
        from tqdm.auto import tqdm as _tqdm
        _qiter: Any = _tqdm(
            missing_pairs,
            desc=f"retr+rr [{config_name}]",
            unit="q",
        )
    except ImportError:
        _qiter = missing_pairs

    for _i, (q, qid) in enumerate(_qiter):
        try:
            _execute_retrieval_only(pipeline, q, qid)
        except Exception as e:
            logger.error("[%s] qid=%s failed: %s", config_name, qid, e)


        if (_i + 1) % CHECKPOINT_EVERY == 0:
            pipeline.flush_cache()
            logger.debug(
                "[%s] checkpoint at query %d/%d",
                config_name, _i + 1, len(missing_pairs),
            )


    pipeline.flush_cache()
    logger.info(
        "[%s] done in %.1f s", config_name, time.perf_counter() - t0,
    )

    del pipeline
    _cleanup_gpu()


def _execute_retrieval_only(
    pipeline: RAGPipeline, query: str, qid: str,
) -> None:

    from src.retrieval import RetrievalResult
    from src.prompts import source_info_from_result

    cfg: dict[str, Any] = pipeline.config
    retriever_type: str = cfg["retriever"]
    uses_embeddings: bool = (retriever_type == "faiss")
    context_mode: str = cfg.get("context_selection_mode", "top_n")
    token_budget: int = int(cfg.get("context_token_budget", 4000))
    use_neighbor_exp: bool = bool(cfg.get("neighbor_expansion", False))


    cached_rows = pipeline._pending_retrieval.get(qid)
    if cached_rows is not None:
        retrieved: list[RetrievalResult] = [
            pipeline._retrieval_result_from_row(r) for r in cached_rows
        ]


    else:
        _cuda_sync_if_needed()
        _t0_qembed: float = time.perf_counter()
        q_emb = (
            pipeline.embedder.embed_query(query) if uses_embeddings else None
        )
        _cuda_sync_if_needed()
        t_qembed_ms: float = (time.perf_counter() - _t0_qembed) * 1000.0
        _t0_retr: float = time.perf_counter()
        retrieved = pipeline.retriever.retrieve(
            query_embedding=q_emb, query_text=query,
        )
        t_retr_ms: float = (time.perf_counter() - _t0_retr) * 1000.0
        pipeline._pending_retrieval[qid] = [
            pipeline._retrieval_result_to_row(r) for r in retrieved
        ]


        pipeline._pending_retrieval_timings[qid] = {
            "query_embedding_ms": t_qembed_ms,
            "retrieval_ms":       t_retr_ms,
            "memory_peak_mb":     pipeline._capture_memory_mb(),
        }


    cached_rr = pipeline._pending_reranking.get(qid)
    if cached_rr is not None:
        reranked: list[RetrievalResult] = [
            pipeline._retrieval_result_from_row(r) for r in cached_rr
        ]
    else:
        _cuda_sync_if_needed()
        _t0_rerank: float = time.perf_counter()
        reranked = pipeline.reranker.rerank_results(query=query, results=retrieved)
        _cuda_sync_if_needed()
        t_rerank_ms: float = (time.perf_counter() - _t0_rerank) * 1000.0
        pipeline._pending_reranking[qid] = [
            pipeline._retrieval_result_to_row(r) for r in reranked
        ]
        pipeline._pending_reranking_timings[qid] = {
            "reranking_ms":   t_rerank_ms,
            "memory_peak_mb": pipeline._capture_memory_mb(),
        }

    _t0_ctx: float = time.perf_counter()
    if context_mode == "token_budget":
        final = pipeline._select_by_token_budget(reranked, token_budget)
    else:
        final = reranked

    if use_neighbor_exp and pipeline._doc_chunk_list:
        final = pipeline._apply_neighbor_expansion(final, token_budget)
    t_ctx_ms: float = (time.perf_counter() - _t0_ctx) * 1000.0

    final_contexts: list[str] = [r.text for r in final]
    sources = [source_info_from_result(r, f"S{i+1}") for i, r in enumerate(final)]
    retrieval_score_type: str = retrieved[0].retrieval_score_type if retrieved else ""
    reranker_score_type: str = reranked[0].reranker_score_type if reranked else ""

    pipeline._pending_contexts[qid] = {
        "contexts": final_contexts,
        "sources": [s.to_dict() for s in sources],
        "retriever_type": retriever_type,
        "retrieval_score_type": retrieval_score_type,
        "reranker_score_type": reranker_score_type,
        "num_chunks_retrieved": len(retrieved),
        "num_chunks_reranked": len(reranked),
        "num_chunks_final": len(final),
        "context_chars_total": sum(len(r.text) for r in final),
        "context_tokens_est": pipeline._estimate_tokens("".join(r.text for r in final)),
        "avg_chunk_size_chars": round(
            sum(len(r.text) for r in final) / max(1, len(final)), 1,
        ),
        "source_files_used": list(dict.fromkeys(
            r.source_file for r in final if r.source_file
        )),
        "chunk_ids_final": [r.chunk_global_id for r in final if r.chunk_global_id],
        "chunker": cfg.get("chunker", ""),
        "prompt_version": cfg.get("prompt_version", ""),
        "context_selection_mode": context_mode,
        "neighbor_expansion_used": False,
        "retrieval_top_k_details": [
            {
                "rank": i + 1,
                "chunk_global_id": r.chunk_global_id,
                "doc_id": r.doc_id,
                "source_file": r.source_file,
                "chunk_index_in_doc": r.chunk_index_in_doc,
                "retrieval_score": round(r.score, 6),
                "retrieval_score_type": r.retrieval_score_type,
                "chunker_method": str(r.metadata.get("chunker_method", "")),
                "text_chars": len(r.text),
                "text_preview": r.text[:100].replace("\n", " "),
            }
            for i, r in enumerate(retrieved)
        ],
        "context_sources": [s.to_dict() for s in sources],
    }


    pipeline._pending_contexts_timings[qid] = {
        "context_selection_ms": t_ctx_ms,
        "memory_peak_mb":       pipeline._capture_memory_mb(),
    }


class _NoLLM:


    def generate(self, prompt: str):
        raise RuntimeError(
            "prepare_rag_artifacts.py must never call the LLM.  "
            "Use scripts/run_experiments.py for generation."
        )


def main() -> int:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Pre-compute deterministic RAG artifacts (cache prewarm).",
    )
    parser.add_argument("--dataset", default="rag_domain",
                        help="Dataset name registered in DATASET_CORPUS_MAPPING.")
    parser.add_argument("--max-samples", type=int, default=0,
                        help="Limit number of eval samples (0 = all).")
    parser.add_argument("--retrieval-models", nargs="+",
                        default=["BAAI/bge-base-en-v1.5",
                                 "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"],
                        help="One or more SentenceTransformer model ids used by FAISS retrievers.")
    parser.add_argument("--rerankers", nargs="+",
                        default=["cross-encoder/ms-marco-MiniLM-L-12-v2"],
                        help="One or more CrossEncoder model ids.")
    parser.add_argument("--chunkers", nargs="+",
                        default=["fixed", "semantic"],
                        choices=["fixed", "semantic"])
    parser.add_argument("--retrievers", nargs="+",
                        default=["bm25", "faiss"],
                        choices=["bm25", "faiss"])
    parser.add_argument("--top-k", type=int, default=25)
    parser.add_argument("--reranker-top-n", type=int, default=5)
    parser.add_argument(
        "--cache-dir", type=Path, default=None,
        help=(
            "Directorio raíz de la cache. "
            "Por defecto: .cache/rag/<dataset> (aislamiento automático por dataset)."
        ),
    )
    parser.add_argument("--use-cache", action="store_true",
                        help="Kept for symmetry with run_experiments.py; the cache "
                             "is always used by this script.")
    parser.add_argument("--refresh-cache", action="store_true",
                        help="Ignore existing artifacts and overwrite them.")
    parser.add_argument(
        "--ignore-disabled", action="store_true",
        help=(
            "Prepare artifacts for ALL configs, including those listed in "
            "DISABLED_CONFIGS in run_experiments.py.  By default, disabled "
            "configs are skipped so the prewarm matches the actual experiment run."
        ),
    )
    parser.add_argument("--log-level", default="INFO")
    args: argparse.Namespace = parser.parse_args()


    if args.cache_dir is None:
        args.cache_dir = _BASE_CACHE_DIR / args.dataset

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )

    ds_info: dict[str, Any] = DATASET_CORPUS_MAPPING.get(args.dataset, {})
    corpus_dir: Path = ds_info.get("corpus_dir", CORPUS_DIR)
    corpus_prefixes: list[str] | None = ds_info.get("corpus_prefixes")

    logger.info("Loading dataset '%s'...", args.dataset)
    manager: DatasetManager = DatasetManager()
    samples = manager.load(args.dataset, max_samples=args.max_samples)
    questions: list[str] = [s.question for s in samples]
    query_ids: list[str] = [query_id_for(q) for q in questions]
    logger.info("Loaded %d samples", len(samples))

    cache: CacheManager = CacheManager(args.cache_dir, refresh=args.refresh_cache)


    active_disabled: frozenset[str] = (
        frozenset() if args.ignore_disabled else DISABLED_CONFIGS
    )
    if active_disabled:
        logger.info(
            "DISABLED_CONFIGS activo - se omitirán %d configs: %s",
            len(active_disabled), ", ".join(sorted(active_disabled)),
        )
        logger.info("Usa --ignore-disabled para preparar artefactos de todas las configs.")
    else:
        logger.info("DISABLED_CONFIGS vacío (o --ignore-disabled activo) - preparando todas.")


    combos_no_rr: list[tuple[int, str]] = select_configs(
        args.chunkers, args.retrievers, use_rerankers=False,
        disabled_configs=active_disabled,
    )
    combos_rr: list[tuple[int, str]] = select_configs(
        args.chunkers, args.retrievers, use_rerankers=True,
        disabled_configs=active_disabled,
    )


    plan: list[tuple[str, str, str | None]] = []
    for rm in args.retrieval_models:
        for _, name in combos_no_rr:
            plan.append((name, rm, None))
    for rm in args.retrieval_models:
        for rr in args.rerankers:
            for _, name in combos_rr:
                plan.append((name, rm, rr))
    total_combos: int = len(plan)
    done_combos: int = 0
    plan_t0: float = time.perf_counter()
    logger.info(
        "PLAN: %d combos to prepare "
        "(%d no-rerank + %d with %d rerankers; %d retrieval models)",
        total_combos, len(combos_no_rr) * len(args.retrieval_models),
        len(combos_rr) * len(args.retrieval_models), len(args.rerankers),
        len(args.retrieval_models),
    )

    def _progress_log(name: str, rm: str, rr: str | None) -> None:

        nonlocal done_combos
        done_combos += 1
        elapsed: float = time.perf_counter() - plan_t0
        avg: float = elapsed / max(done_combos - 1, 1) if done_combos > 1 else 0.0
        eta_s: float = avg * (total_combos - done_combos + 1) if avg else 0.0
        logger.info(
            "PROGRESS [%d/%d] (%d left) elapsed=%.0fs eta=%.0fs - next: %s "
            "[retr=%s rerank=%s]",
            done_combos, total_combos, total_combos - done_combos,
            elapsed, eta_s, name,
            rm if rm else "-", rr or "none",
        )


    for rm in args.retrieval_models:
        for opt, name in combos_no_rr:
            _progress_log(name, rm, None)
            prepare_for_combo(
                config_option=opt, config_name=name,
                questions=questions, query_ids=query_ids,
                corpus_dir=corpus_dir, corpus_prefixes=corpus_prefixes,
                cache=cache,
                retrieval_models=rm,
                reranker_models=None,
                top_k=args.top_k,
                reranker_top_n=args.reranker_top_n,
                dataset_name=args.dataset,
            )


    for rm in args.retrieval_models:
        for rr in args.rerankers:
            for opt, name in combos_rr:
                _progress_log(name, rm, rr)
                prepare_for_combo(
                    config_option=opt, config_name=name,
                    questions=questions, query_ids=query_ids,
                    corpus_dir=corpus_dir, corpus_prefixes=corpus_prefixes,
                    cache=cache,
                    retrieval_models=rm,
                    reranker_models=rr,
                    top_k=args.top_k,
                    reranker_top_n=args.reranker_top_n,
                    dataset_name=args.dataset,
                )

    total_elapsed: float = time.perf_counter() - plan_t0
    logger.info(
        "DONE: %d/%d combos prepared in %.0fs (avg %.1fs/combo). "
        "Cache prewarmed under %s",
        done_combos, total_combos, total_elapsed,
        total_elapsed / max(done_combos, 1), args.cache_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
