from __future__ import annotations

import argparse
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline import RAGPipeline, PIPELINE_CONFIGS, PipelineResult, CORPUS_DIR
from src.evaluation import (
    ExperimentRunner,
    ExperimentLogV2,
    RunManifest,
    append_to_run_index,
    create_run_id,
    format_duration,
)
from src.dataset_manager import DatasetManager


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger: logging.Logger = logging.getLogger(__name__)


EXPERIMENT_ORDER: list[tuple[int, str]] = [
    (1,  "no_rag"),
    (2,  "baseline_k"),
    (3,  "baseline_s"),
    (4,  "baseline_k_rr"),
    (5,  "baseline_s_rr"),
    (6,  "baseline_k_grounded"),
    (7,  "baseline_s_grounded"),
    (8,  "baseline_k_rr_grounded"),
    (9,  "baseline_s_rr_grounded"),
    (10, "optimized_k"),
    (11, "optimized_s"),
    (12, "optimized_k_rr"),
    (13, "optimized_s_rr"),
    (14, "optimized_k_grounded"),
    (15, "optimized_s_grounded"),
    (16, "optimized_k_rr_grounded"),
    (17, "optimized_s_rr_grounded"),
]


DISABLED_CONFIGS: frozenset[str] = frozenset({

    "baseline_k",

    "baseline_k_rr",

    "baseline_k_grounded",
    "baseline_s_grounded",
    "baseline_k_rr_grounded",

    "optimized_k",

    "optimized_k_rr",

    "optimized_k_grounded",
    "optimized_s_grounded",
    "optimized_k_rr_grounded",

})


_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent


LOG_DIR: Path = _PROJECT_ROOT / "logs"


EXPERIMENT_DATASET: str = "sample"


_PROJECT_DATA: Path = _PROJECT_ROOT / "data"

DATASET_CORPUS_MAPPING: dict[str, dict] = {
    "sample": {

        "corpus_dir": _PROJECT_DATA / "corpus",
        "corpus_prefixes": ["01_", "02_", "03_", "04_", "05_", "06_", "07_", "08_"],
        "eval_file": "data/eval/sample_eval.json",
        "notes": "Offline, 20 triples. Para pruebas rápidas.",
    },
    "rag_domain": {

        "corpus_dir": _PROJECT_DATA / "corpus",
        "corpus_prefixes": ["01_", "02_", "03_", "04_", "05_", "06_", "07_", "08_"],
        "eval_file": "data/eval/rag_domain_eval.json",
        "notes": "Offline, 25 triples curados. Recomendado para primeras pruebas.",
    },
    "triviaqa": {


        "corpus_dir": _PROJECT_DATA / "external" / "evidence" / "wikipedia",
        "corpus_prefixes": None,
        "eval_file": "data/eval/triviaqa_eval.json",
        "notes": "Requiere download_corpus.py --source triviaqa.",
    },
    "hotpotqa": {

        "corpus_dir": _PROJECT_DATA / "corpus",
        "corpus_prefixes": ["hotpotqa_"],
        "eval_file": "data/eval/hotpotqa_eval.json",
        "notes": "Requiere download_corpus.py --source hotpotqa. Multi-salto.",
    },
}


DEFAULT_MAX_SAMPLES: int = 20


class DryRunLLM:


    def __init__(self, model_name: str = "dry-run-stub") -> None:
        self.model_name: str = model_name
        self.temperature: float = 0.0
        self.max_tokens: int = 512

    def generate(self, prompt: str) -> Any:

        from src.llm import LLMResponse
        time.sleep(0.01)
        answer: str = (
            "Esta es una respuesta simulada del modo dry-run. "
            "El pipeline RAG se ejecutó correctamente pero no se usó "
            "un LLM real. Para obtener respuestas reales, ejecuta "
            "sin la bandera --dry-run con Ollama activo."
        )
        return LLMResponse(
            text=answer,
            model=self.model_name,
            tokens_prompt=len(prompt.split()),
            tokens_generated=len(answer.split()),
            latency_ms=10.0,
        )


class DryRunEmbedder:


    def __init__(self, dimension: int = 384) -> None:
        self.model_name: str = "dry-run-embedder"
        self.dimension: int = dimension
        import numpy as np
        self._rng = np.random.default_rng(seed=42)

    def embed(self, texts: list[str]) -> Any:

        import numpy as np
        embeddings: Any = self._rng.standard_normal(
            (len(texts), self.dimension)
        ).astype(np.float32)
        logger.info("DryRunEmbedder: %d textos → shape %s", len(texts), embeddings.shape)
        return embeddings

    def embed_query(self, query: str) -> Any:

        return self.embed([query])[0]


class DryRunRetriever:


    def __init__(self, top_k: int = 5) -> None:
        self.top_k: int = top_k
        self._texts: list[str] = []

    def index(self, embeddings: Any, texts: list[str], metadatas: Any = None) -> None:

        self._texts = texts
        logger.info("DryRunRetriever: %d textos indexados", len(texts))

    def retrieve(
        self,
        query_embedding: Any = None,
        query_text: str = "",
    ) -> list[Any]:

        from src.retrieval import RetrievalResult
        results: list[Any] = []
        for i in range(min(self.top_k, len(self._texts))):
            results.append(RetrievalResult(
                text=self._texts[i], score=1.0 - (i * 0.1), chunk_id=i, metadata={},
            ))
        return results


def _create_dry_run_pipeline(
    config_option: int,
    config_name: str,
    config: dict[str, Any],
) -> RAGPipeline:

    pipeline: RAGPipeline = RAGPipeline.__new__(RAGPipeline)
    pipeline.config_name = config_name
    pipeline.config = config
    pipeline.is_indexed = False
    pipeline._chunks = []

    pipeline.llm = DryRunLLM(model_name=f"dry-run-{config_name}")

    if config_name == "no_rag":
        pipeline.chunker = None
        pipeline.embedder = None
        pipeline.retriever = None
        pipeline.reranker = None
    else:
        from src.chunking import FixedChunker, SemanticChunker
        if config.get("chunker") == "fixed":
            pipeline.chunker = FixedChunker(
                chunk_size=config.get("chunk_size", 2048),
                overlap=config.get("chunk_overlap", 200),
            )
        elif config.get("chunker") == "semantic":
            pipeline.chunker = SemanticChunker(
                chunk_size=config.get("chunk_size", 1500),
                overlap=config.get("chunk_overlap", 150),
            )
        else:
            pipeline.chunker = None

        pipeline.embedder = DryRunEmbedder()
        pipeline.retriever = DryRunRetriever(top_k=config.get("top_k", 5))

        from src.reranking import NoReranker
        pipeline.reranker = NoReranker(
            top_n=config.get("reranker_top_n", config.get("top_k", 5))
        )

    from src.prompts import PromptBuilder
    pipeline.prompt_builder = PromptBuilder(version=config.get("prompt_version", "basic"))

    logger.info(
        "Pipeline dry-run '%s' creado: chunker=%s, prompt=%s",
        config_name, config.get("chunker", "none"), config.get("prompt_version", "?"),
    )
    return pipeline


@dataclass
class ExperimentResult:


    config_option: int
    config_name: str
    pipeline_results: list[PipelineResult]
    elapsed_seconds: float
    success: bool
    error_message: str = ""

    experiment_log_v2: ExperimentLogV2 | None = None


def _check_server_alive(timeout: int = 10) -> bool:

    from urllib.request import urlopen, Request as URequest
    from urllib.error import URLError, HTTPError
    import hmac
    import json as _json

    try:
        from src.config_loader import (
            get_server_url, get_api_key,
            get_auth_header_name, get_auth_header_prefix,
            get_signature_header_name, get_signature_prefix,
        )
        server_url: str = get_server_url()
        api_key: str = get_api_key()
        auth_header_name: str = get_auth_header_name()
        auth_header_prefix: str = get_auth_header_prefix()
        sig_header_name: str = get_signature_header_name()
        sig_prefix: str = get_signature_prefix()
    except (ImportError, Exception):
        import os
        server_url = os.environ.get("TFG_SERVER_URL", "http://localhost:8000")
        api_key = os.environ.get("TFG_API_KEY", "tfg-rag-2026-shared-secret-change-me")
        auth_header_name = "X-TFG-Auth"
        auth_header_prefix = "TFG-RAG-2026"
        sig_header_name = "X-TFG-Signature"
        sig_prefix = "sha256="

    health_url: str = f"{server_url}/health"


    body: bytes = _json.dumps({}).encode("utf-8")


    digest: str = hmac.new(
        key=api_key.encode("utf-8"),
        msg=body,
        digestmod="sha256",
    ).hexdigest()
    signature: str = f"{sig_prefix}{digest}"

    try:
        req: URequest = URequest(
            health_url,
            data=body,
            headers={
                "Content-Type": "application/json",
                auth_header_name: f"{auth_header_prefix}:{api_key}",
                sig_header_name: signature,
            },
            method="POST",
        )
        with urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                return True
            logger.warning("Servidor respondió HTTP %d en /health", resp.status)
            return False
    except (URLError, HTTPError, TimeoutError, OSError) as e:
        logger.warning(
            "Servidor no accesible en %s: %s. "
            "¿Está activo el SSH tunnel? Ejecuta: ssh -L 8000:127.0.0.1:8000 usuario@servidor",
            health_url, e,
        )
        return False


def preflight_get_active_model() -> dict[str, Any] | None:

    from urllib.request import urlopen, Request as URequest
    from urllib.error import URLError, HTTPError
    import hmac
    import json as _json

    try:
        from src.config_loader import (
            get_server_url, get_api_key,
            get_auth_header_name, get_auth_header_prefix,
            get_signature_header_name, get_signature_prefix,
        )
        server_url: str = get_server_url()
        api_key: str = get_api_key()
        auth_header_name: str = get_auth_header_name()
        auth_header_prefix: str = get_auth_header_prefix()
        sig_header_name: str = get_signature_header_name()
        sig_prefix: str = get_signature_prefix()
    except (ImportError, Exception):
        import os
        server_url = os.environ.get("TFG_SERVER_URL", "http://localhost:8000")
        api_key = os.environ.get("TFG_API_KEY", "tfg-rag-2026-shared-secret-change-me")
        auth_header_name = "X-TFG-Auth"
        auth_header_prefix = "TFG-RAG-2026"
        sig_header_name = "X-TFG-Signature"
        sig_prefix = "sha256="

    url: str = f"{server_url}/active-model"
    body: bytes = _json.dumps({}).encode("utf-8")


    digest: str = hmac.new(
        key=api_key.encode("utf-8"),
        msg=body,
        digestmod="sha256",
    ).hexdigest()
    signature: str = f"{sig_prefix}{digest}"

    try:
        req: URequest = URequest(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                auth_header_name: f"{auth_header_prefix}:{api_key}",
                sig_header_name: signature,
            },
            method="POST",
        )
        with urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                data: dict[str, Any] = _json.loads(resp.read().decode("utf-8"))
                logger.info(
                    "Preflight /active-model: model=%s actual=%s "
                    "num_ctx=%d chunk_size=%d top_k=%d",
                    data.get("model"),
                    data.get("actual_model"),
                    data.get("num_ctx"),
                    data.get("recommended_chunk_size"),
                    data.get("recommended_top_k"),
                )
                return data
            logger.warning("Preflight /active-model respondió HTTP %d", resp.status)
            return None
    except (URLError, HTTPError, TimeoutError, OSError) as e:
        logger.warning(
            "Preflight /active-model falló: %s - se usarán los parámetros por defecto.",
            e,
        )
        return None


def _apply_model_overrides(
    model_info: dict[str, Any],
    configs_to_run: list[int],
) -> None:

    chunk_size: int = model_info.get("recommended_chunk_size", 0)
    top_k: int = model_info.get("recommended_top_k", 0)

    if chunk_size <= 0 or top_k <= 0:

        logger.warning(
            "Preflight devolvió chunk_size=%d top_k=%d - sin sobreescritura.",
            chunk_size, top_k,
        )
        return


    model_name: str = model_info.get("model", "desconocido")
    category: str = model_info.get("model_size_category", "?")

    logger.info(
        "Ajustando parámetros de pipeline para modelo '%s' (%s): "
        "chunk_size=%d, top_k=%d",
        model_name, category, chunk_size, top_k,
    )


    rag_configs: list[str] = [
        "baseline_k", "baseline_s",
        "baseline_k_rr", "baseline_s_rr",
        "baseline_k_rr_grounded", "baseline_s_rr_grounded",
        "optimized_k", "optimized_s",
        "optimized_k_rr", "optimized_s_rr",
        "optimized_k_rr_grounded", "optimized_s_rr_grounded",
    ]

    names_to_run: list[str] = [
        RAGPipeline.CONFIG_MAP[c] for c in configs_to_run
        if c in RAGPipeline.CONFIG_MAP
    ]

    for config_name in names_to_run:
        if config_name not in rag_configs:
            continue
        if config_name not in PIPELINE_CONFIGS:
            continue

        PIPELINE_CONFIGS[config_name]["chunk_size"] = chunk_size
        PIPELINE_CONFIGS[config_name]["chunk_overlap"] = max(50, chunk_size // 10)


        if "_rr" in config_name:
            PIPELINE_CONFIGS[config_name]["top_k"] = max(25, top_k * 4)
            PIPELINE_CONFIGS[config_name]["reranker_top_n"] = top_k
        else:
            PIPELINE_CONFIGS[config_name]["top_k"] = top_k

        logger.debug(
            "  %s: chunk_size=%d overlap=%d top_k=%d reranker_top_n=%s",
            config_name,
            PIPELINE_CONFIGS[config_name]["chunk_size"],
            PIPELINE_CONFIGS[config_name]["chunk_overlap"],
            PIPELINE_CONFIGS[config_name]["top_k"],
            PIPELINE_CONFIGS[config_name].get("reranker_top_n", "-"),
        )


def _phase1_run_dirs(run_id: str) -> tuple[Path, Path, Path]:

    run_dir: Path = LOG_DIR / "runs" / run_id
    experiments_dir: Path = run_dir / "experiments"
    eval_artifacts_dir: Path = run_dir / "evaluation_artifacts"
    summaries_dir: Path = run_dir / "summaries"
    for d in (run_dir, experiments_dir, eval_artifacts_dir, summaries_dir):
        d.mkdir(parents=True, exist_ok=True)
    return run_dir, experiments_dir, eval_artifacts_dir


def run_single_experiment_v2(
    config_option: int,
    queries: list[str],
    ground_truths: list[str],
    run_id: str,
    dataset: str,
    dry_run: bool = False,
    persist_index: bool = False,
    corpus_dir: Path | None = None,
    corpus_file_prefixes: list[str] | None = None,
    cache_manager: Any = None,
    cached_only: bool = False,
    query_ids: list[str] | None = None,
) -> ExperimentResult:

    config_name: str = RAGPipeline.CONFIG_MAP[config_option]
    config: dict[str, Any] = dict(PIPELINE_CONFIGS[config_name])
    config["mode"] = "dry_run" if dry_run else "real"


    from src.pipeline import RETRIEVAL_MODEL, RERANKER_MODEL
    if config.get("retriever") == "faiss":
        config["retriever_model"] = config.get("embedder") or RETRIEVAL_MODEL
    elif config.get("retriever") == "bm25":
        config["retriever_model"] = "bm25"
    else:
        config["retriever_model"] = "none"
    if config.get("reranker") == "cross-encoder":
        config["reranker_model"] = RERANKER_MODEL
    elif config.get("reranker") and config["reranker"] != "none":
        config["reranker_model"] = config["reranker"]
    else:
        config["reranker_model"] = "none"
    if config.get("embedder") and config["embedder"] != "none":
        config["embedder_model"] = config["embedder"]
    else:
        config["embedder_model"] = "none"

    _corpus_dir: Path = corpus_dir if corpus_dir is not None else CORPUS_DIR

    logger.info("=" * 60)
    logger.info(
        "EXPERIMENTO v2: %s (config=%d) run_id=%s",
        config_name.upper(), config_option, run_id,
    )
    logger.info("=" * 60)

    if not dry_run and not _check_server_alive(timeout=10):
        msg: str = (
            f"Servidor no accesible antes de iniciar '{config_name}'. "
            f"Verifica el túnel SSH inverso."
        )
        logger.error(msg)
        return ExperimentResult(
            config_option=config_option, config_name=config_name,
            pipeline_results=[],
            elapsed_seconds=0.0, success=False, error_message=msg,
        )

    ts_start_iso: str = time.strftime("%Y-%m-%dT%H:%M:%S")
    start: float = time.perf_counter()

    try:
        if dry_run:
            pipeline: RAGPipeline = _create_dry_run_pipeline(
                config_option, config_name, config,
            )
        else:
            pipeline = RAGPipeline(config_option=config_option)

        if config_name != "no_rag":


            if cache_manager is not None and not dry_run:
                qid_map: dict[str, str] = (
                    dict(zip(queries, query_ids)) if query_ids else {}
                )
                pipeline.attach_cache(
                    cache_manager, query_ids=qid_map, cached_only=cached_only,
                    dataset_name=dataset,
                )
            logger.info("Construyendo índice desde %s...", _corpus_dir)
            pipeline.build_index(
                corpus_dir=_corpus_dir,
                persist_index=persist_index,
                corpus_file_prefixes=corpus_file_prefixes,
            )
        else:
            pipeline.is_indexed = True

        logger.info("Ejecutando %d consultas...", len(queries))
        results: list[PipelineResult] = pipeline.run_batch(
            queries, query_ids=query_ids,
        )

        elapsed: float = time.perf_counter() - start
        ts_end_iso: str = time.strftime("%Y-%m-%dT%H:%M:%S")


        if not dry_run:
            had_model: bool = any(
                (r.metadata or {}).get("model") for r in results
            )
            if not had_model:
                msg = (
                    f"Experimento '{config_name}' inválido: el servidor no "
                    "devolvió un nombre de modelo en ninguna respuesta."
                )
                logger.error(msg)
                return ExperimentResult(
                    config_option=config_option, config_name=config_name,
                    pipeline_results=results,
                    elapsed_seconds=elapsed, success=False, error_message=msg,
                )


        runner: ExperimentRunner = ExperimentRunner(log_dir=LOG_DIR)
        log_v2: ExperimentLogV2 = runner.run_collect_only(
            results=results,
            config_name=config_name,
            config_option=config_option,
            config=config,
            run_id=run_id,
            dataset=dataset,
            ground_truths=ground_truths,
            timestamp_start=ts_start_iso,
            timestamp_end=ts_end_iso,
            elapsed_seconds=elapsed,
        )

        return ExperimentResult(
            config_option=config_option, config_name=config_name,
            pipeline_results=results,

            elapsed_seconds=elapsed, success=True,
            experiment_log_v2=log_v2,
        )

    except (ConnectionError, TimeoutError, ImportError,
            FileNotFoundError, RuntimeError) as e:
        elapsed = time.perf_counter() - start
        msg = f"Error en {config_name}: {e}"
        logger.error(msg, exc_info=True)
        return ExperimentResult(
            config_option=config_option, config_name=config_name,
            pipeline_results=[],
            elapsed_seconds=elapsed, success=False, error_message=msg,
        )


def run_all_experiments_v2(
    configs: list[int],
    max_samples: int,
    dry_run: bool,
    persist_index: bool,
    run_id: str,
    model_label: str,
    cache_manager: Any = None,
    cached_only: bool = False,
    run_type: str = "main",
) -> tuple[list[ExperimentResult], RunManifest, str, str, float, str]:

    logger.info("Cargando dataset '%s'...", EXPERIMENT_DATASET)
    manager: DatasetManager = DatasetManager()
    samples = manager.load(EXPERIMENT_DATASET, max_samples=max_samples,
                           allow_eval_rebuild=not cached_only)
    queries: list[str] = [s.question for s in samples]
    ground_truths: list[str] = [s.answer for s in samples]

    from src.cache import query_id_for as _qid
    query_ids: list[str] = [_qid(q) for q in queries]
    logger.info("Dataset cargado: %d samples", len(samples))

    dataset_info: dict = DATASET_CORPUS_MAPPING.get(EXPERIMENT_DATASET, {})
    corpus_dir: Path = dataset_info.get("corpus_dir", CORPUS_DIR)
    corpus_file_prefixes: list[str] | None = dataset_info.get("corpus_prefixes", None)

    if not corpus_dir.exists():
        raise FileNotFoundError(
            f"Directorio de corpus no encontrado para dataset "
            f"'{EXPERIMENT_DATASET}': {corpus_dir}."
        )


    detected_model_meta: dict[str, Any] = {}
    if not dry_run:
        info = preflight_get_active_model()
        if info is not None:
            detected_model_meta = info
            import os as _os
            if _os.environ.get("TFG_APPLY_SERVER_OVERRIDES", "0") == "1":
                _apply_model_overrides(info, configs)

    run_dir, experiments_dir, _eval_dir = _phase1_run_dirs(run_id)

    manifest: RunManifest = RunManifest(
        run_id=run_id,
        run_dir=run_dir,
        dataset=EXPERIMENT_DATASET,
        mode="dry_run" if dry_run else "real",
        run_type=run_type,
        model_label=model_label or detected_model_meta.get("model", ""),
        model_detected=detected_model_meta.get("actual_model", "")
            or detected_model_meta.get("model", ""),
        model_size_gb=str(detected_model_meta.get("model_size_gb", "")),
        model_size_category=detected_model_meta.get("model_size_category", ""),
        num_configs_expected=len(configs),
        num_queries_per_config=len(samples),
    )
    manifest.save()

    ts_start: str = time.strftime("%Y-%m-%dT%H:%M:%S")
    total_start: float = time.perf_counter()

    ordered: list[tuple[int, str]] = [
        (opt, name) for opt, name in EXPERIMENT_ORDER
        if opt in configs and name not in DISABLED_CONFIGS
    ]
    if DISABLED_CONFIGS:
        skipped: list[str] = [
            name for opt, name in EXPERIMENT_ORDER
            if opt in configs and name in DISABLED_CONFIGS
        ]
        if skipped:
            logger.info(
                "[runner] Configs desactivadas (DISABLED_CONFIGS): %s",
                ", ".join(skipped),
            )
    results: list[ExperimentResult] = []
    invalid_count: int = 0

    for config_option, _config_name in ordered:
        er: ExperimentResult = run_single_experiment_v2(
            config_option=config_option,
            queries=queries,
            ground_truths=ground_truths,
            run_id=run_id,
            dataset=EXPERIMENT_DATASET,
            dry_run=dry_run,
            persist_index=persist_index,
            corpus_dir=corpus_dir,
            corpus_file_prefixes=corpus_file_prefixes,
            cache_manager=cache_manager,
            cached_only=cached_only,
            query_ids=query_ids,
        )
        results.append(er)

        if er.success and er.experiment_log_v2 is not None:
            er.experiment_log_v2.save(experiments_dir)
        manifest.update_config_completed(
            config_name=er.config_name,
            config_option=er.config_option,
            elapsed_seconds=er.elapsed_seconds,
            success=er.success,
            error_message=er.error_message,
        )

        if not er.success and "no devolvió un nombre de modelo" in (
            er.error_message or ""
        ):
            invalid_count += 1
            if invalid_count > 2:
                logger.error(
                    "Cancelando lote: demasiados experimentos inválidos."
                )
                break

    total_elapsed: float = time.perf_counter() - total_start
    ts_end: str = time.strftime("%Y-%m-%dT%H:%M:%S")
    manifest.mark_run_evaluation_pending()
    return results, manifest, ts_start, ts_end, total_elapsed, EXPERIMENT_DATASET


def parse_args() -> argparse.Namespace:

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Ejecutor automatizado de experimentos RAG del TFG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
WORKFLOW POR MODELO (uso recomendado):
  1. En el servidor: cargar el modelo deseado con `ollama run <name>`.
     Catálogo (1 small + 2 medium representativos):
       llama3.2:latest (small)   mistral:7b (medium)   llama3:8b (medium)
     El servidor FastAPI lo detecta automáticamente vía `ollama ps` -
     no es necesario reiniciarlo al cambiar de modelo.
  2. Asegurar que el servidor FastAPI está activo y el túnel SSH inverso
     está abierto desde el servidor hacia el cliente.
  3. Ejecutar aquí (orden lógico no_rag → baseline → baseline_grounded →
     optimized → optimized_grounded; las 17 configs activas):
       python3 scripts/run_experiments.py --configs 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17
     Mapeo (CONFIG_MAP del pipeline, ver src/pipeline/__init__.py):
       1=no_rag
       === baseline (chunking fijo, prompt basic) ===
       2=baseline_k             3=baseline_s
       4=baseline_k_rr          5=baseline_s_rr
       === baseline grounded (chunking fijo, prompt grounded_sourced) ===
       6=baseline_k_grounded    7=baseline_s_grounded
       8=baseline_k_rr_grounded 9=baseline_s_rr_grounded
       === optimized (chunking semántico, prompt basic) ===
       10=optimized_k           11=optimized_s
       12=optimized_k_rr        13=optimized_s_rr
       === optimized grounded (chunking semántico, prompt grounded_sourced) ===
       14=optimized_k_grounded  15=optimized_s_grounded
       16=optimized_k_rr_grounded 17=optimized_s_rr_grounded
     Sufijo _k = retriever BM25; _s = retriever FAISS denso; _rr = re-ranking
     activado; _grounded = prompt grounded_sourced; sin sufijo = prompt basic.
     Desactivar configs sin borrarlas: editar DISABLED_CONFIGS en este script.
     En la práctica no siempre se ejecutan las 17: tras los lotes
     exploratorios pequeños se descartan las que no aportan información
     discriminativa para reducir el coste de las campañas grandes.
  4. Repetir para cada modelo (cambiándolo en el servidor con `ollama run`).
  Los logs incluyen el nombre y categoría del modelo devueltos por el servidor.
        """,
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Usar componentes simulados (sin torch/servidor). Valida la orquestación.",
    )
    parser.add_argument(
        "--verify", action="store_true",
        help="Run pre-flight verification (verify_setup.py) before experiments.",
    )
    parser.add_argument(
        "--max-samples", type=int, default=DEFAULT_MAX_SAMPLES,
        help=f"Máximo de samples del dataset (default: {DEFAULT_MAX_SAMPLES})",
    )
    parser.add_argument(
        "--configs", nargs="+", type=int,
        default=list(range(1, 18)),
        choices=list(range(1, 18)),
        help=(
            "Configuraciones a ejecutar (en orden). "
            "1=no_rag, "
            "2=baseline_k, 3=baseline_s, "
            "4=baseline_k_rr, 5=baseline_s_rr, "
            "6=baseline_k_grounded, 7=baseline_s_grounded, "
            "8=baseline_k_rr_grounded, 9=baseline_s_rr_grounded, "
            "10=optimized_k, 11=optimized_s, "
            "12=optimized_k_rr, 13=optimized_s_rr, "
            "14=optimized_k_grounded, 15=optimized_s_grounded, "
            "16=optimized_k_rr_grounded, 17=optimized_s_rr_grounded. "
            "Default: todas (1..17). "
            "Usa DISABLED_CONFIGS en el script para excluir sin cambiar CLI. "
            "_grounded = prompt grounded_sourced; sin _grounded = prompt basic."
        ),
    )
    parser.add_argument(
        "--dataset", type=str, default=EXPERIMENT_DATASET,
        choices=["rag_domain", "hotpotqa", "triviaqa"],
        help=f"Dataset de evaluación (default: {EXPERIMENT_DATASET})",
    )
    parser.add_argument(
        "--model-label", type=str, default="",
        help=(
            "Label for this experiment run (e.g. 'llama3-8b', 'mistral-7b'). "
            "Included in log filenames and log content to identify which "
            "server model was active. "
            "If not provided, the model name is read from the server response."
        ),
    )
    parser.add_argument(
        "--cache-index",
        action="store_true",
        help=(
            "Persistir el índice FAISS en disco (data/index_cache/). "
            "Primera ejecución: construye y guarda. "
            "Ejecuciones siguientes: carga directamente (evita re-embeddings). "
            "Solo aplica a configuraciones con retriever FAISS (baseline_s, "
            "baseline_s_rr, optimized_s, optimized_s_rr). "
            "No usar si el corpus ha cambiado desde la última indexación."
        ),
    )
    parser.add_argument(
        "--check-remote", type=str, default=None,
        help=(
            "URL del servidor remoto a verificar en --verify "
            "(p. ej. http://localhost:8000 si el túnel SSH está activo). "
            "Si se indica, se omiten las comprobaciones de Ollama local."
        ),
    )


    parser.add_argument(
        "--use-cache", action=argparse.BooleanOptionalAction, default=True,
        help=(
            "Activa la cache por etapas (ingestion/chunks/embeddings/...). "
            "Por defecto activada; usar --no-use-cache para desactivarla."
        ),
    )
    parser.add_argument(
        "--refresh-cache", action="store_true",
        help="Ignora artefactos existentes y los reescribe.",
    )
    parser.add_argument(
        "--cache-dir", type=Path,
        default=None,
        help=(
            "Directorio raíz de la cache. "
            "Por defecto: .cache/rag/<dataset> (aislamiento automático por dataset)."
        ),
    )
    parser.add_argument(
        "--cached-contexts", action=argparse.BooleanOptionalAction, default=True,
        help=(
            "Reutiliza la cache de contexts: si está poblada para una query, "
            "se salta query embedding, retrieval y reranking; sólo se "
            "construye el prompt, se llama al LLM y se evalúa. "
            "Por defecto activado."
        ),
    )
    parser.add_argument(
        "--cached-only", action="store_true",
        help=(
            "Falla con error si alguna etapa requiere recomputarse en lugar "
            "de cargar desde cache. Útil para verificar que "
            "prepare_rag_artifacts.py se ejecutó completamente."
        ),
    )
    parser.add_argument(
        "--prewarm-cache", action=argparse.BooleanOptionalAction, default=True,
        help=(
            "Calienta la cache antes de los experimentos (ingestion, chunking, "
            "embeddings BGE, retrieval y reranking) - análogo a la "
            "pre-descarga de modelos.  Desactivar con --no-prewarm-cache."
        ),
    )
    parser.add_argument(
        "--run-type",
        type=str,
        default="main_experiment",
        choices=["main_experiment", "model_selection"],
        help=(
            "Purpose of this run. "
            "'main_experiment' = final comparative experiment (included in TFG results). "
            "'model_selection' = exploratory run to compare models before "
            "committing to a full campaign (excluded from final results by default). "
            "Stored in run_manifest.json and run_index.jsonl for later filtering. "
            "Default: main_experiment."
        ),
    )
    return parser.parse_args()


def _run_phase2_evaluation(run_dir: Path, dry_run: bool = False) -> dict[str, Any]:

    _empty_counts: dict[str, Any] = {
        "total": 0, "completed": 0, "pending": 0,
        "failed": 0, "async_submitted": 0, "completion_rate": 0.0,
    }

    if dry_run:
        logger.info(
            "[eval] Dry-run mode - skipping Phase 2 evaluation "
            "(no real answers to judge)."
        )
        return _empty_counts

    try:
        from src.config_loader import is_evaluation_enabled
        evaluation_enabled: bool = is_evaluation_enabled()
    except ImportError:
        import os
        evaluation_enabled = bool(os.environ.get("OPENAI_API_KEY", ""))

    if not evaluation_enabled:
        logger.info(
            "[eval] OPENAI_API_KEY not configured - skipping evaluation. "
            "To evaluate later: "
            "python -m src.evaluation.run_evaluation --run-dir %s",
            run_dir,
        )

        _ensure_metrics_and_summary(run_dir)
        return _empty_counts

    logger.info(
        "[eval] Starting Phase 2 post-run evaluation for run %s…", run_dir.name
    )
    counts: dict[str, Any] = _empty_counts.copy()
    try:
        from src.evaluation.run_evaluation import evaluate_run
        counts = evaluate_run(run_dir=run_dir, pending_only=True)
        if counts is None:
            counts = _empty_counts.copy()
    except (ImportError, ValueError, RuntimeError) as exc:
        logger.error(
            "[eval] Phase 2 evaluation failed - %s: %s.\n"
            "  Cause: %s\n"
            "  Run manually: python -m src.evaluation.run_evaluation --run-dir %s",
            type(exc).__name__, exc, exc.__cause__ or "(see traceback above)",
            run_dir,
            exc_info=True,
        )
    finally:


        _ensure_metrics_and_summary(run_dir)

    return counts


def _ensure_metrics_and_summary(run_dir: Path) -> None:

    try:
        from src.evaluation.run_evaluation import (
            _recompute_all_metrics,
            regenerate_summary_for_run,
        )
        _recompute_all_metrics(run_dir)
        regenerate_summary_for_run(run_dir)
        logger.info("[eval] Metric averages recomputed and summary regenerated.")
    except (ImportError, OSError, RuntimeError) as exc:
        logger.error(
            "[eval] _ensure_metrics_and_summary failed - %s: %s",
            type(exc).__name__, exc, exc_info=True,
        )


def _prewarm_cache_before_experiments(
    cache_manager: Any,
    config_options: list[int],
    dataset: str,
    max_samples: int,
) -> None:

    from scripts.prepare_rag_artifacts import prepare_for_combo
    from src.cache import query_id_for as _qid
    from src.dataset_manager import DatasetManager
    from src.pipeline import RAGPipeline, PIPELINE_CONFIGS

    ds_info: dict[str, Any] = DATASET_CORPUS_MAPPING.get(dataset, {})
    corpus_dir: Path = ds_info.get("corpus_dir", CORPUS_DIR)
    corpus_prefixes: list[str] | None = ds_info.get("corpus_prefixes")

    logger.info("=" * 70)
    logger.info("PREWARM - cache deterministic artifacts before experiments")
    logger.info("=" * 70)
    logger.info("Dataset: %s | configs: %s", dataset, config_options)

    mgr: DatasetManager = DatasetManager()
    samples = mgr.load(dataset, max_samples=max_samples)
    questions: list[str] = [s.question for s in samples]
    query_ids: list[str] = [_qid(q) for q in questions]
    logger.info("Prewarm samples: %d", len(samples))


    for opt in config_options:
        try:
            name: str = RAGPipeline.CONFIG_MAP[opt]
        except KeyError:
            logger.warning("Config option %s no existe en CONFIG_MAP - saltando.", opt)
            continue
        cfg: dict[str, Any] = PIPELINE_CONFIGS[name]
        if cfg.get("chunker") == "none" or cfg.get("retriever") == "none":
            logger.info("[prewarm] skip %s (no retrieval)", name)
            continue

        retrieval_model: str = (
            cfg.get("embedder") or "bm25"
            if cfg.get("retriever") == "faiss" else "bm25"
        )
        reranker_value: str = cfg.get("reranker", "none")
        reranker_model: str | None = (
            None if reranker_value in (None, "none") else reranker_value
        )
        prepare_for_combo(
            config_option=opt,
            config_name=name,
            questions=questions,
            query_ids=query_ids,
            corpus_dir=corpus_dir,
            corpus_prefixes=corpus_prefixes,
            cache=cache_manager,
            retrieval_models=retrieval_model,
            reranker_models=reranker_model,
            top_k=int(cfg.get("top_k", 25)),
            reranker_top_n=int(cfg.get("reranker_top_n", cfg.get("top_k", 5))),
        )
    logger.info("PREWARM done - cache ready under %s", cache_manager.cache_dir)


def main() -> int:

    args: argparse.Namespace = parse_args()


    if args.cache_dir is None:
        args.cache_dir = (
            Path(__file__).resolve().parent.parent / ".cache" / "rag" / args.dataset
        )

    logger.info("=" * 60)
    logger.info("EJECUCIÓN AUTOMATIZADA DE EXPERIMENTOS - TFG RAG")
    logger.info("=" * 60)
    logger.info("Modo: %s", "DRY-RUN (sin LLM/torch)" if args.dry_run else "COMPLETO")
    logger.info("Configuraciones solicitadas (CLI): %s", args.configs)


    _name_to_opt: dict[str, int] = {name: opt for opt, name in EXPERIMENT_ORDER}
    _disabled_opts: set[int] = {
        _name_to_opt[n] for n in DISABLED_CONFIGS if n in _name_to_opt
    }
    _effective_configs: list[int] = [c for c in args.configs if c not in _disabled_opts]
    _skipped_now: list[str] = [
        name for opt, name in EXPERIMENT_ORDER
        if opt in args.configs and name in DISABLED_CONFIGS
    ]
    if _skipped_now:
        logger.info(
            "DISABLED_CONFIGS activo - se omitirán %d configs: %s",
            len(_skipped_now), ", ".join(_skipped_now),
        )
        logger.info("Configuraciones efectivas a ejecutar: %s", _effective_configs)
    else:
        logger.info("DISABLED_CONFIGS vacío - se ejecutarán todas las solicitadas.")
    logger.info("Run type: %s", args.run_type)
    logger.info(
        "Orden recomendado: no_rag(1) → baseline_k/s/_rr(2..5) → baseline_k/s/_rr_grounded(6..9) → "
        "optimized_k/s/_rr(10..13) → optimized_k/s/_rr_grounded(14..17)"
    )
    logger.info("Dataset: %s", args.dataset)
    logger.info("Max samples: %d", args.max_samples)
    if args.model_label:
        logger.info("Model label: %s", args.model_label)
    else:
        logger.info(
            "Model label: (not set - will use model name from server response)"
        )


    if args.verify and not args.dry_run:
        logger.info("Running pre-flight verification...")
        try:
            from scripts.verify_setup import run_all_checks


            remote_url: str = args.check_remote or "http://localhost:8000"
            logger.info("Verificando servidor FastAPI remoto en %s", remote_url)
            results, all_pass = run_all_checks(
                check_remote_url=remote_url,
                skip_ollama=True,
            )
            for r in results:
                logger.info(str(r))
            if not all_pass:
                logger.error(
                    "Pre-flight verification failed. Fix issues above or use --dry-run."
                )
                return 1
            logger.info("Pre-flight verification passed.")
        except ImportError:
            logger.warning(
                "Could not import verify_setup. Skipping verification."
            )


    global EXPERIMENT_DATASET
    EXPERIMENT_DATASET = args.dataset


    _ds_info: dict = DATASET_CORPUS_MAPPING.get(EXPERIMENT_DATASET, {})
    _corpus_info_dir: Path = _ds_info.get("corpus_dir", CORPUS_DIR)
    _corpus_info_pref: list[str] | None = _ds_info.get("corpus_prefixes", None)
    logger.info(
        "Corpus dataset '%s': dir=%s | prefijos=%s",
        EXPERIMENT_DATASET,
        _corpus_info_dir,
        _corpus_info_pref if _corpus_info_pref else "todos",
    )

    LOG_DIR.mkdir(parents=True, exist_ok=True)


    if not args.dry_run:
        try:
            from scripts.preload_models import (
                build_model_plan,
                preload_model,
            )
            logger.info("Pre-descargando modelos de embeddings y reranking...")
            model_plan = build_model_plan()
            failed_models: list[str] = []
            for spec in model_plan:


                logger.debug(
                    "Pre-descargando modelo: %s [%s]", spec.repo_id, spec.kind,
                )
                if not preload_model(spec):
                    failed_models.append(f"{spec.repo_id} [{spec.kind}]")
            if failed_models:
                logger.warning(
                    "Algún modelo no pudo pre-descargarse. "
                    "Se intentará cargar bajo demanda."
                )
                for model_name in failed_models:
                    logger.warning("Modelo no pre-descargado: %s", model_name)
            else:
                logger.info("Modelos pre-descargados correctamente.")
        except ImportError as e:
            logger.warning("No se pudo importar preload_models: %s", e)


    run_id: str = create_run_id(args.model_label or None)
    logger.info("Run ID: %s", run_id)


    cache_manager: Any = None
    if args.use_cache or args.cached_contexts or args.cached_only or args.refresh_cache:
        from src.cache import CacheManager as _CM
        cache_manager = _CM(args.cache_dir, refresh=args.refresh_cache)
        logger.info(
            "Cache: dir=%s refresh=%s cached_contexts=%s cached_only=%s",
            args.cache_dir, args.refresh_cache,
            args.cached_contexts, args.cached_only,
        )


        if (
            args.prewarm_cache
            and not args.dry_run
            and not args.cached_only
        ):
            try:
                _prewarm_cache_before_experiments(
                    cache_manager=cache_manager,
                    config_options=_effective_configs,
                    dataset=args.dataset,
                    max_samples=args.max_samples,
                )
            except (RuntimeError, OSError, ImportError) as exc:
                logger.warning(
                    "Prewarm de cache falló (%s: %s). Los experimentos "
                    "continúan y construirán la cache en línea.",
                    type(exc).__name__, exc,
                )

    (
        experiment_results,
        manifest,
        ts_start,
        ts_end,
        total_elapsed,
        dataset_used,
    ) = run_all_experiments_v2(
        configs=args.configs,
        max_samples=args.max_samples,
        dry_run=args.dry_run,
        persist_index=args.cache_index,
        run_id=run_id,
        model_label=args.model_label,
        cache_manager=cache_manager,
        cached_only=args.cached_only,
        run_type=args.run_type,
    )


    run_dir: Path = LOG_DIR / "runs" / run_id
    successful_logs: list[ExperimentLogV2] = [
        er.experiment_log_v2 for er in experiment_results
        if er.success and er.experiment_log_v2 is not None
    ]
    failed_pairs: list[tuple[str, str]] = [
        (er.config_name, er.error_message) for er in experiment_results
        if not er.success
    ]

    manifest_data: dict[str, Any] = manifest.to_dict()


    eval_counts: dict[str, Any] = _run_phase2_evaluation(
        run_dir=run_dir, dry_run=args.dry_run
    )


    summary_path: Path = run_dir / "summaries" / "experiment_summary.json"


    append_to_run_index(
        logs_root=LOG_DIR,
        run_id=run_id,
        dataset=dataset_used,
        mode="dry_run" if args.dry_run else "real",
        model_label=manifest_data.get("model_label", ""),
        model_detected=manifest_data.get("model_detected", ""),
        timestamp_start=ts_start,
        timestamp_end=ts_end,
        num_configs_completed=sum(1 for er in experiment_results if er.success),
        num_configs_expected=len(args.configs),
        summary_relative_path=str(summary_path.relative_to(LOG_DIR)),
        run_type=args.run_type,
    )


    print()
    print("=" * 82)
    print(f"  RESUMEN FINAL - run_id={run_id}")
    print("=" * 82)
    print(f"  Dataset: {dataset_used}")
    print(f"  Run type: {args.run_type}")
    print(f"  Modelo (label): {manifest_data.get('model_label', '-')}")
    print(f"  Modelo detectado: {manifest_data.get('model_detected', '-')}")
    print(f"  Duración total: {format_duration(total_elapsed)} "
          f"({total_elapsed:.1f} s)")

    _eval_info: str = "PENDING"
    _eval_status: str = "pending"
    try:
        import json as _json
        _sum_path = run_dir / "summaries" / "experiment_summary.json"
        if _sum_path.exists():
            with open(_sum_path, encoding="utf-8") as _f:
                _sum = _json.load(_f)
            _es = _sum.get("evaluation", {}).get("status", "pending")
            _eval_status = _es
            _em = _sum.get("evaluation", {}).get("model") or "-"
            _ne = _sum.get("evaluation", {}).get("num_samples_evaluated", 0)
            _nt = _sum.get("evaluation", {}).get("num_samples_total", 0)
            _eval_info = f"{_es.upper()} | judge={_em} | {_ne}/{_nt} evaluated"
    except (OSError, Exception):
        pass


    _eval_pending_count: int = (
        eval_counts.get("pending", 0) + eval_counts.get("failed", 0)
    )

    if _eval_pending_count == 0 and _eval_status in (
        "pending", "partial", "retry_pending"
    ):
        _eval_pending_count = 1
    print(f"  Evaluación: {_eval_info}")
    print("-" * 82)
    print(f"  {'Config':<18} {'Status':<10} {'Muestras':<9} "
          f"{'Latencia(ms)':<13} {'Duración':<10}")
    print("-" * 82)
    for er in experiment_results:
        if er.success and er.experiment_log_v2 is not None:
            lat: float = 0.0
            for m in er.experiment_log_v2.metrics:
                if m.get("metric") == "latency_mean_ms":
                    lat = float(m.get("value", 0.0))
                    break
            print(
                f"  {er.config_name:<18} {'OK':<10} "
                f"{er.experiment_log_v2.num_queries:<9} "
                f"{lat:<13.1f} {format_duration(er.elapsed_seconds):<10}"
            )
        else:
            print(
                f"  {er.config_name:<18} {'FAILED':<10} {'-':<9} "
                f"{'-':<13} {format_duration(er.elapsed_seconds):<10}"
            )
    print("=" * 82)
    print(f"  Logs:    {run_dir}")
    print(f"  Resumen: {summary_path}")
    print(f"  Índice:  {LOG_DIR / 'index' / 'run_index.jsonl'}")
    print("=" * 82)
    print()


    print("=" * 82)
    print("  ACCIONES SIGUIENTES")
    print("=" * 82)
    print()


    all_success: bool = all(er.success for er in experiment_results)
    if all_success:
        print("  [OK] Todos los experimentos del pipeline completados correctamente.")
    else:
        failed_names: list[str] = [
            er.config_name for er in experiment_results if not er.success
        ]
        print(f"  [FAIL] Experimentos fallidos en pipeline: {', '.join(failed_names)}")
    print()


    if not args.dry_run:
        if _eval_pending_count > 0:


            print("  ┌─ [EVALUACIÓN CON MUESTRAS PENDIENTES] ─────────────────────────────┐")
            print(f"  │  {_eval_pending_count} muestras pendientes o con error tras la evaluación Phase 2.  │")
            print("  │  Espera ~5 min para evitar rate limits de OpenAI y ejecuta:        │")
            print("  └─────────────────────────────────────────────────────────────────────┘")
            print()
            print("  Evaluación en modo SYNC (recomendado, sin async batch):")
            print()
            print(
                f"    python -m src.evaluation.run_evaluation"
                f" --run-dir {run_dir} --pending-only"
            )
            print()
            print("  Para re-evaluar TODAS las muestras (ignora anteriores resultados):")
            print()
            print(
                f"    python -m src.evaluation.run_evaluation"
                f" --run-dir {run_dir} --all-samples"
            )
        elif _eval_status == "completed":
            print("  [OK] Evaluación Phase 2 completada sin pendientes.")
        elif _eval_status in ("not_configured", "dry_run"):
            print("  ℹ  Evaluación no configurada (sin OPENAI_API_KEY).")
            print("  Para evaluar cuando esté configurada:")
            print()
            print(
                f"    python -m src.evaluation.run_evaluation"
                f" --run-dir {run_dir} --pending-only"
            )
        else:
            print(f"  [EVALUACIÓN] Estado: {_eval_status}")
            print("  Para evaluar manualmente (modo sync):")
            print()
            print(
                f"    python -m src.evaluation.run_evaluation"
                f" --run-dir {run_dir} --pending-only"
            )
        print()

        print("  Para regenerar el resumen con los últimos scores disponibles:")
        print()
        print(
            f"    python -m src.evaluation.run_evaluation"
            f" --run-dir {run_dir} --regenerate-summary"
        )
        print()
    else:
        print("  [DRY-RUN] Evaluación Phase 2 no ejecutada (no hay respuestas reales).")
        print()


    print("  Para generar las gráficas comparativas (todas las ejecuciones disponibles):")
    print()
    print("    python3 scripts/generate_charts.py")
    print()
    if manifest_data.get("model_label"):
        print(f"  Para filtrar por el modelo de esta ejecución ({manifest_data.get('model_label')}):")
        print()
        print(f"    python3 scripts/generate_charts.py --model {manifest_data.get('model_label')}")
        print()
    if dataset_used:
        print(f"  Para filtrar por dataset ({dataset_used}):")
        print()
        print(f"    python3 scripts/generate_charts.py --dataset {dataset_used}")
        print()
    print("  Para listar todas las ejecuciones disponibles:")
    print()
    print("    python3 scripts/generate_charts.py --list-runs")
    print()
    print("=" * 82)
    print()


    if all_success:
        logger.info("Todos los experimentos completados exitosamente.")
        return 0
    failed_list: list[str] = [
        er.config_name for er in experiment_results if not er.success
    ]
    logger.warning("Experimentos fallidos: %s", ", ".join(failed_list))
    return 1


if __name__ == "__main__":
    sys.exit(main())
