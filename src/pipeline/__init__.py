from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import logging
import time

import numpy as np
from numpy.typing import NDArray

from src.ingestion import Document, DocumentLoader
from src.chunking import Chunk, FixedChunker, SemanticChunker, BaseChunker
from src.embeddings import SentenceTransformerEmbedder, BaseEmbedder
from src.retrieval import FAISSRetriever, BM25Retriever, RetrievalResult, BaseRetriever
from src.reranking import CrossEncoderReranker, NoReranker, BaseReranker
from src.prompts import PromptBuilder, SourceInfo, source_info_from_result
from src.llm import BaseLLM, RemoteLLM, LLMResponse
from src.evaluation import PerformanceTimer
from src.cache import CacheManager, query_id_for, query_set_key, _hash_file

logger: logging.Logger = logging.getLogger(__name__)


try:
    from src.config_loader import get_server_url, get_api_key
    REMOTE_LLM_URL: str = get_server_url()
    REMOTE_API_KEY: str = get_api_key()
except ImportError:
    import os as _os
    REMOTE_LLM_URL = _os.environ.get("TFG_SERVER_URL", "http://localhost:8000")
    REMOTE_API_KEY = _os.environ.get("TFG_API_KEY", "tfg-rag-2026-shared-secret-change-me")


RETRIEVAL_MODEL: str = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"


EMBED_BATCH_SIZE: int = 256


PIPELINE_CONFIGS: dict[str, dict[str, Any]] = {


    "no_rag": {
        "chunker": "none",
        "embedder": "none",
        "retriever": "none",
        "reranker": "none",
        "llm": "remote",
        "llm_backend": "remote",
        "prompt_version": "direct",
        "temperature": 0.0,
        "max_tokens": 512,
    },


    "baseline_k": {
        "chunker": "fixed",


        "chunk_size": 512,
        "chunk_overlap": 105,
        "embedder": "none",
        "retriever": "bm25",
        "top_k": 5,
        "reranker": "none",
        "llm": "remote",
        "llm_backend": "remote",
        "prompt_version": "basic",
        "temperature": 0.0,
        "max_tokens": 512,
    },
    "baseline_k_rr": {
        "chunker": "fixed",
        "chunk_size": 512,
        "chunk_overlap": 105,


        "embedder": "none",
        "retriever": "bm25",

        "top_k": 25,
        "reranker": RERANKER_MODEL,
        "reranker_top_n": 5,
        "llm": "remote",
        "llm_backend": "remote",
        "prompt_version": "basic",
        "temperature": 0.0,
        "max_tokens": 512,
    },


    "baseline_s": {
        "chunker": "fixed",
        "chunk_size": 512,
        "chunk_overlap": 105,
        "embedder": RETRIEVAL_MODEL,
        "retriever": "faiss",
        "top_k": 5,
        "reranker": "none",
        "llm": "remote",
        "llm_backend": "remote",
        "prompt_version": "basic",
        "temperature": 0.0,
        "max_tokens": 512,
    },
    "baseline_s_rr": {
        "chunker": "fixed",
        "chunk_size": 512,
        "chunk_overlap": 105,
        "embedder": RETRIEVAL_MODEL,
        "retriever": "faiss",

        "top_k": 25,
        "reranker": RERANKER_MODEL,
        "reranker_top_n": 5,
        "llm": "remote",
        "llm_backend": "remote",
        "prompt_version": "basic",
        "temperature": 0.0,
        "max_tokens": 512,
    },


    "baseline_k_grounded": {
        "chunker": "fixed",
        "chunk_size": 512,
        "chunk_overlap": 105,
        "embedder": "none",
        "retriever": "bm25",
        "top_k": 5,
        "reranker": "none",
        "llm": "remote",
        "llm_backend": "remote",
        "prompt_version": "grounded_sourced",
        "temperature": 0.0,
        "max_tokens": 512,
    },
    "baseline_s_grounded": {
        "chunker": "fixed",
        "chunk_size": 512,
        "chunk_overlap": 105,
        "embedder": RETRIEVAL_MODEL,
        "retriever": "faiss",
        "top_k": 5,
        "reranker": "none",
        "llm": "remote",
        "llm_backend": "remote",
        "prompt_version": "grounded_sourced",
        "temperature": 0.0,
        "max_tokens": 512,
    },
    "baseline_k_rr_grounded": {
        "chunker": "fixed",
        "chunk_size": 512,
        "chunk_overlap": 105,
        "embedder": "none",
        "retriever": "bm25",

        "top_k": 25,
        "reranker": RERANKER_MODEL,
        "reranker_top_n": 5,
        "llm": "remote",
        "llm_backend": "remote",
        "prompt_version": "grounded_sourced",
        "temperature": 0.0,
        "max_tokens": 512,
    },
    "baseline_s_rr_grounded": {
        "chunker": "fixed",
        "chunk_size": 512,
        "chunk_overlap": 105,
        "embedder": RETRIEVAL_MODEL,
        "retriever": "faiss",

        "top_k": 25,
        "reranker": RERANKER_MODEL,
        "reranker_top_n": 5,
        "llm": "remote",
        "llm_backend": "remote",
        "prompt_version": "grounded_sourced",
        "temperature": 0.0,
        "max_tokens": 512,
    },


    "optimized_k": {
        "chunker": "semantic",


        "chunk_size": 512,
        "chunk_overlap": 105,
        "embedder": "none",
        "retriever": "bm25",
        "top_k": 5,
        "reranker": "none",
        "llm": "remote",
        "llm_backend": "remote",
        "prompt_version": "basic",
        "temperature": 0.0,
        "max_tokens": 512,
    },
    "optimized_s": {
        "chunker": "semantic",
        "chunk_size": 512,
        "chunk_overlap": 105,

        "embedder": RETRIEVAL_MODEL,
        "retriever": "faiss",
        "top_k": 5,
        "reranker": "none",
        "llm": "remote",
        "llm_backend": "remote",
        "prompt_version": "basic",
        "temperature": 0.0,
        "max_tokens": 512,
    },
    "optimized_k_rr": {
        "chunker": "semantic",
        "chunk_size": 512,
        "chunk_overlap": 105,
        "embedder": "none",
        "retriever": "bm25",

        "top_k": 25,
        "reranker": RERANKER_MODEL,
        "reranker_top_n": 5,
        "llm": "remote",
        "llm_backend": "remote",
        "prompt_version": "basic",
        "temperature": 0.0,
        "max_tokens": 512,
    },
    "optimized_s_rr": {
        "chunker": "semantic",
        "chunk_size": 512,
        "chunk_overlap": 105,

        "embedder": RETRIEVAL_MODEL,
        "retriever": "faiss",

        "top_k": 25,
        "reranker": RERANKER_MODEL,
        "reranker_top_n": 5,
        "llm": "remote",
        "llm_backend": "remote",
        "prompt_version": "basic",
        "temperature": 0.0,
        "max_tokens": 512,
    },


    "optimized_k_grounded": {
        "chunker": "semantic",
        "chunk_size": 512,
        "chunk_overlap": 105,
        "embedder": "none",
        "retriever": "bm25",
        "top_k": 5,
        "reranker": "none",
        "llm": "remote",
        "llm_backend": "remote",
        "prompt_version": "grounded_sourced",
        "temperature": 0.0,
        "max_tokens": 512,
    },
    "optimized_s_grounded": {
        "chunker": "semantic",
        "chunk_size": 512,
        "chunk_overlap": 105,
        "embedder": RETRIEVAL_MODEL,
        "retriever": "faiss",
        "top_k": 5,
        "reranker": "none",
        "llm": "remote",
        "llm_backend": "remote",
        "prompt_version": "grounded_sourced",
        "temperature": 0.0,
        "max_tokens": 512,
    },
    "optimized_k_rr_grounded": {
        "chunker": "semantic",
        "chunk_size": 512,
        "chunk_overlap": 105,
        "embedder": "none",
        "retriever": "bm25",

        "top_k": 25,
        "reranker": RERANKER_MODEL,
        "reranker_top_n": 5,
        "llm": "remote",
        "llm_backend": "remote",
        "prompt_version": "grounded_sourced",
        "temperature": 0.0,
        "max_tokens": 512,
    },
    "optimized_s_rr_grounded": {
        "chunker": "semantic",
        "chunk_size": 512,
        "chunk_overlap": 105,
        "embedder": RETRIEVAL_MODEL,
        "retriever": "faiss",

        "top_k": 25,
        "reranker": RERANKER_MODEL,
        "reranker_top_n": 5,
        "llm": "remote",
        "llm_backend": "remote",
        "prompt_version": "grounded_sourced",
        "temperature": 0.0,
        "max_tokens": 512,
    },
}


_PIPELINE_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
CORPUS_DIR: Path = _PIPELINE_PROJECT_ROOT / "data" / "corpus"


@dataclass
class PipelineResult:


    query: str = ""
    answer: str = ""
    contexts: list[str] = field(default_factory=list)
    config_name: str = ""
    timings: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


    prompt: str = ""


    sources: list[dict[str, Any]] = field(default_factory=list)
class RAGPipeline:


    cache: CacheManager | None = None
    _cache_query_ids: dict[str, str] = {}
    _cache_query_set_hash: str = ""
    _cache_keys: dict[str, str] = {}
    _cache_only: bool = False
    _pending_retrieval: dict[str, list[dict[str, Any]]] = {}
    _pending_reranking: dict[str, list[dict[str, Any]]] = {}
    _pending_contexts: dict[str, dict[str, Any]] = {}

    CONFIG_MAP: dict[int, str] = {
        1:  "no_rag",
        2:  "baseline_k",
        3:  "baseline_s",
        4:  "baseline_k_rr",
        5:  "baseline_s_rr",

        6:  "baseline_k_grounded",
        7:  "baseline_s_grounded",
        8:  "baseline_k_rr_grounded",
        9:  "baseline_s_rr_grounded",

        10: "optimized_k",
        11: "optimized_s",
        12: "optimized_k_rr",
        13: "optimized_s_rr",

        14: "optimized_k_grounded",
        15: "optimized_s_grounded",
        16: "optimized_k_rr_grounded",
        17: "optimized_s_rr_grounded",
    }

    def __init__(self, config_option: int = 2) -> None:

        if config_option not in self.CONFIG_MAP:
            valid: str = ", ".join(str(k) for k in sorted(self.CONFIG_MAP))
            raise ValueError(
                f"config_option debe ser 1-17. Recibido: {config_option}. "
                f"Valores válidos: {valid}"
            )

        config_name: str = self.CONFIG_MAP[config_option]
        self.config_name: str = config_name
        self.config: dict[str, Any] = PIPELINE_CONFIGS[config_name]


        self.is_indexed: bool = False
        self._chunks: list[Chunk] = []


        self.cache: CacheManager | None = None
        self._cache_query_ids: dict[str, str] = {}
        self._cache_query_set_hash: str = ""
        self._cache_keys: dict[str, str] = {}
        self._cache_only: bool = False

        self._pending_retrieval: dict[str, list[dict[str, Any]]] = {}
        self._pending_reranking: dict[str, list[dict[str, Any]]] = {}
        self._pending_contexts: dict[str, dict[str, Any]] = {}


        self._pending_retrieval_timings: dict[str, dict[str, float | None]] = {}
        self._pending_reranking_timings: dict[str, dict[str, float | None]] = {}
        self._pending_contexts_timings: dict[str, dict[str, float | None]] = {}


        self._cache_stage_timings: dict[str, dict[str, dict[str, float | None]]] = {}


        self._show_progress: bool = True


        self.chunker: BaseChunker | None = self._build_chunker()
        self.embedder: BaseEmbedder | None = self._build_embedder()
        self.retriever: BaseRetriever | None = self._build_retriever()
        self.reranker: BaseReranker | None = self._build_reranker()
        self.llm: BaseLLM = self._build_llm()
        self.prompt_builder: PromptBuilder = PromptBuilder(
            version=self.config["prompt_version"]
        )

        logger.info(
            "Pipeline '%s' inicializado: chunker=%s, embedder=%s, "
            "retriever=%s, reranker=%s, prompt=%s",
            config_name,
            self.config["chunker"],
            self.config["embedder"],
            self.config["retriever"],
            self.config["reranker"],
            self.config["prompt_version"],
        )


    def _build_chunker(self) -> BaseChunker | None:

        chunker_type: str = self.config["chunker"]

        if chunker_type == "none":
            return None
        elif chunker_type == "fixed":
            return FixedChunker(
                chunk_size=self.config["chunk_size"],
                overlap=self.config["chunk_overlap"],
            )
        elif chunker_type == "semantic":
            return SemanticChunker(
                chunk_size=self.config["chunk_size"],
                overlap=self.config["chunk_overlap"],
            )
        else:
            raise ValueError(f"Chunker desconocido: {chunker_type}")

    def _build_embedder(self) -> BaseEmbedder | None:

        embedder_name: str = self.config["embedder"]

        if embedder_name == "none":
            return None

        batch_size: int = self.config.get(
            "embed_batch_size",
            EMBED_BATCH_SIZE,
        )
        return SentenceTransformerEmbedder(
            model_name=embedder_name,
            batch_size=batch_size,
        )

    def _build_retriever(self) -> BaseRetriever | None:

        retriever_type: str = self.config["retriever"]

        if retriever_type == "none":
            return None
        elif retriever_type == "faiss":
            return FAISSRetriever(top_k=self.config["top_k"])
        elif retriever_type == "bm25":
            return BM25Retriever(top_k=self.config["top_k"])
        else:
            raise ValueError(f"Retriever desconocido: {retriever_type}")

    def _build_reranker(self) -> BaseReranker | None:

        reranker_value: str = self.config["reranker"]


        if reranker_value == "none":
            top_n: int = self.config.get("top_k", 5)
            return NoReranker(top_n=top_n)

        top_n = self.config.get("reranker_top_n", 3)
        model_name: str = (
            RERANKER_MODEL if reranker_value == "cross-encoder" else reranker_value
        )
        return CrossEncoderReranker(top_n=top_n, model_name=model_name)

    def _build_llm(self) -> BaseLLM:

        temperature: float = self.config["temperature"]
        max_tokens: int = self.config["max_tokens"]


        return RemoteLLM(
            server_url=REMOTE_LLM_URL,
            model_name="remote",
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=REMOTE_API_KEY,
            query_type=self.config_name,
        )


    INDEX_CACHE_DIR: Path = Path("data/index_cache")


    def attach_cache(
        self,
        cache: CacheManager,
        query_ids: dict[str, str] | None = None,
        cached_only: bool = False,
        dataset_name: str = "",
    ) -> None:

        self.cache = cache
        self._cache_query_ids = dict(query_ids) if query_ids else {}
        self._cache_query_set_hash = (
            query_set_key(self._cache_query_ids.values())
            if self._cache_query_ids else ""
        )
        self._cache_only = cached_only

        self._cache_dataset_name: str = dataset_name


        self._cache_keys = {}
        self._pending_retrieval = {}
        self._pending_reranking = {}
        self._pending_contexts = {}
        self._pending_retrieval_timings = {}
        self._pending_reranking_timings = {}
        self._pending_contexts_timings = {}
        self._cache_stage_timings = {}
        logger.info(
            "Cache attached: dir=%s refresh=%s cached_only=%s n_queries=%d dataset=%s",
            cache.cache_dir, cache.refresh, cached_only,
            len(self._cache_query_ids), dataset_name or "(unset)",
        )

    def _qid(self, query: str) -> str:

        if query in self._cache_query_ids:
            return self._cache_query_ids[query]
        qid: str = query_id_for(query)

        self._cache_query_ids[query] = qid
        return qid

    def _miss(self, stage: str, key: str) -> None:

        logger.info("CACHE_MISS stage=%s key=%s", stage, key)
        if self._cache_only:
            raise RuntimeError(
                f"--cached-only set but stage '{stage}' (key={key}) is not "
                f"in the cache.  Run scripts/prepare_rag_artifacts.py first."
            )


    @staticmethod
    def _capture_memory_mb() -> float | None:

        try:
            import resource
            kb: int = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            return round(kb / 1024.0, 2)
        except (ImportError, AttributeError):
            return None

    def _load_cached_timings(self, stage: str) -> dict[str, dict[str, float | None]]:

        if stage in self._cache_stage_timings:
            return self._cache_stage_timings[stage]
        if self.cache is None or stage not in self._cache_keys:
            self._cache_stage_timings[stage] = {}
            return {}
        loaded = self.cache.load_stage_timings(stage, self._cache_keys[stage])
        self._cache_stage_timings[stage] = loaded
        if loaded:
            logger.info(
                "CACHE_HIT timings stage=%s n_queries=%d", stage, len(loaded),
            )
        return loaded

    def _compute_ingestion_key(
        self,
        corpus_dir: Path,
        corpus_file_prefixes: list[str] | None,
    ) -> tuple[str, list[Path], list[str]]:

        from src.cache import _hash_file as _hf

        all_paths: list[Path] = []
        for p in sorted(corpus_dir.rglob("*")):
            if not p.is_file():
                continue
            if p.suffix.lower() not in {".md", ".txt", ".pdf"}:
                continue
            if corpus_file_prefixes and not any(
                p.name.startswith(pref) for pref in corpus_file_prefixes
            ):
                continue
            all_paths.append(p)
        hashes: list[str] = [_hf(p) for p in all_paths]
        key: str = CacheManager.key_ingestion(corpus_dir, all_paths, hashes)
        return key, all_paths, hashes

    def _rebuild_chunks_from_dicts(self, raw: list[dict[str, Any]]) -> list[Chunk]:

        out: list[Chunk] = []
        for d in raw:
            md: dict[str, Any] = d.get("metadata", {}) or {}
            out.append(Chunk(
                text=d["text"],
                chunk_id=int(d["chunk_id"]),
                doc_source=d["doc_source"],
                metadata=md,
                doc_id=d.get("doc_id", d["doc_source"]),
                chunk_global_id=d.get("chunk_global_id", ""),
                chunk_index_in_doc=int(d.get("chunk_index_in_doc", d["chunk_id"])),
                chunker_method=d.get("chunker_method", ""),
            ))
        return out

    def build_index(
        self,
        corpus_dir: Path = CORPUS_DIR,
        persist_index: bool = False,
        corpus_file_prefixes: list[str] | None = None,
    ) -> int:

        if self.config_name == "no_rag":
            logger.info("Modo no_rag: no se requiere índice")
            self.is_indexed = True
            return 0


        if self.cache is not None:
            n_chunks: int = self._build_index_with_cache(
                corpus_dir=corpus_dir,
                corpus_file_prefixes=corpus_file_prefixes,
            )
            return n_chunks


        retriever_type: str = self.config["retriever"]
        if persist_index and retriever_type == "faiss" and isinstance(self.retriever, FAISSRetriever):

            cache_dir: Path = RAGPipeline.INDEX_CACHE_DIR / self.config_name
            logger.info("persist_index=True: buscando índice cacheado en %s", cache_dir)
            loaded: bool = self.retriever.load(cache_dir)
            if loaded:
                self.is_indexed = True
                logger.info(
                    "Índice FAISS cargado desde caché (%s). "
                    "Se omite ingesta/chunking/embeddings.",
                    cache_dir,
                )
                return 0
            logger.info("No se encontró caché. Se construirá y guardará el índice.")

        if self.chunker is None or self.retriever is None:
            raise RuntimeError(
                "Componentes de indexación no disponibles. "
                "¿Configuración correcta?"
            )


        uses_embeddings: bool = (retriever_type == "faiss")

        logger.info("=" * 50)
        logger.info("INDEXACIÓN DEL CORPUS (%s)", retriever_type.upper())
        logger.info("=" * 50)


        with PerformanceTimer("ingestion") as t_ingest:
            loader: DocumentLoader = DocumentLoader(
                data_dir=corpus_dir,
                file_prefixes=corpus_file_prefixes,
            )
            documents: list[Document] = loader.load_all()

        logger.info(
            "Ingesta: %d documentos cargados en %.0f ms",
            len(documents),
            t_ingest.elapsed_ms,
        )

        if not documents:
            raise FileNotFoundError(
                f"No se encontraron documentos en {corpus_dir}. "
                f"Coloca archivos .md o .txt en el directorio."
            )


        with PerformanceTimer("chunking") as t_chunk:
            all_chunks: list[Chunk] = []
            for doc in documents:
                doc_source: str = doc.metadata.get("filename", "unknown")
                chunks: list[Chunk] = self.chunker.chunk(
                    text=doc.content,
                    doc_source=doc_source,
                )
                all_chunks.extend(chunks)

        self._chunks = all_chunks
        chunk_texts: list[str] = [c.text for c in all_chunks]
        metadatas: list[dict[str, str | int]] = [c.metadata for c in all_chunks]


        self._chunk_lookup = {c.chunk_global_id: c for c in all_chunks if c.chunk_global_id}
        self._doc_chunk_list = {}
        for c in all_chunks:
            self._doc_chunk_list.setdefault(c.doc_source, []).append(c)

        for doc_src in self._doc_chunk_list:
            self._doc_chunk_list[doc_src].sort(key=lambda x: x.chunk_index_in_doc)

        logger.info(
            "Chunking: %d chunks generados en %.0f ms",
            len(all_chunks),
            t_chunk.elapsed_ms,
        )

        if uses_embeddings:

            if self.embedder is None:
                raise RuntimeError(
                    "Configuración FAISS requiere embedder. "
                    "Verifica PIPELINE_CONFIGS[embedder]."
                )

            with PerformanceTimer("embedding") as t_embed:
                embeddings: NDArray[np.float32] = self.embedder.embed(chunk_texts)

            logger.info(
                "Embeddings: shape %s generados en %.0f ms",
                embeddings.shape,
                t_embed.elapsed_ms,
            )

            with PerformanceTimer("indexing") as t_index:
                self.retriever.index(
                    embeddings=embeddings,
                    texts=chunk_texts,
                    metadatas=metadatas,
                )

            logger.info(
                "Índice FAISS: %d vectores indexados en %.0f ms",
                len(chunk_texts),
                t_index.elapsed_ms,
            )

            total_ms: float = (
                t_ingest.elapsed_ms
                + t_chunk.elapsed_ms
                + t_embed.elapsed_ms
                + t_index.elapsed_ms
            )


            if persist_index and isinstance(self.retriever, FAISSRetriever):
                cache_dir_save: Path = RAGPipeline.INDEX_CACHE_DIR / self.config_name
                try:
                    self.retriever.save(cache_dir_save)
                    logger.info("Índice FAISS guardado en caché: %s", cache_dir_save)
                except Exception as e:

                    logger.warning("No se pudo guardar el índice en caché: %s", e)
        else:


            dummy_embeddings: NDArray[np.float32] = np.empty((0,), dtype=np.float32)

            with PerformanceTimer("indexing") as t_index:
                self.retriever.index(
                    embeddings=dummy_embeddings,
                    texts=chunk_texts,
                    metadatas=metadatas,
                )

            logger.info(
                "Índice BM25: %d documentos indexados en %.0f ms",
                len(chunk_texts),
                t_index.elapsed_ms,
            )

            total_ms = t_ingest.elapsed_ms + t_chunk.elapsed_ms + t_index.elapsed_ms

        self.is_indexed = True
        logger.info(
            "Indexación completa: %d chunks, %.0f ms total",
            len(all_chunks),
            total_ms,
        )
        return len(all_chunks)


    def _build_index_with_cache(
        self,
        corpus_dir: Path,
        corpus_file_prefixes: list[str] | None,
    ) -> int:

        assert self.cache is not None

        if self.chunker is None or self.retriever is None:
            raise RuntimeError(
                "Componentes de indexación no disponibles. ¿Configuración correcta?"
            )

        retriever_type: str = self.config["retriever"]
        uses_embeddings: bool = (retriever_type == "faiss")
        chunker_type: str = self.config["chunker"]
        chunk_size: int = int(self.config.get("chunk_size", 0))
        chunk_overlap: int = int(self.config.get("chunk_overlap", 0))
        embedder_name: str = self.config.get("embedder", "none")


        logger.info("[cache] computing ingestion fingerprint from %s", corpus_dir)
        ing_key, file_paths, file_hashes = self._compute_ingestion_key(
            corpus_dir, corpus_file_prefixes,
        )
        self._cache_keys["ingestion"] = ing_key


        chunks_key: str = CacheManager.key_chunks(
            ing_key, chunker_type, chunk_size, chunk_overlap,
        )
        self._cache_keys["chunks"] = chunks_key


        emb_key: str | None = None
        if uses_embeddings:
            emb_key = CacheManager.key_embeddings(
                chunks_key, embedder_name,
            )
            self._cache_keys["embeddings"] = emb_key
        index_key: str = CacheManager.key_index(
            chunks_key, retriever_type, emb_key,
        )
        self._cache_keys["index"] = index_key


        top_k: int = int(self.config.get("top_k", 5))
        retrieval_model: str = (
            embedder_name if uses_embeddings else "bm25"
        )
        if self._cache_query_set_hash:
            retr_key: str = CacheManager.key_retrieval(
                index_key, top_k, retrieval_model, self._cache_query_set_hash,
            )
            self._cache_keys["retrieval"] = retr_key

            reranker_value: str = self.config.get("reranker", "none")
            reranker_top_n: int = int(self.config.get("reranker_top_n",
                                       self.config.get("top_k", 5)))
            reranker_model: str = (
                RERANKER_MODEL if reranker_value == "cross-encoder"
                else reranker_value
            )
            rer_key: str = CacheManager.key_reranking(
                retr_key, reranker_model, reranker_top_n,
                self._cache_query_set_hash,
            )
            self._cache_keys["reranking"] = rer_key

            ctx_mode: str = self.config.get("context_selection_mode", "top_n")
            ctx_budget: int = int(self.config.get("context_token_budget", 4000))
            ctx_neighbor: bool = bool(self.config.get("neighbor_expansion", False))
            ctx_key: str = CacheManager.key_contexts(
                rer_key, self.config_name, ctx_mode, ctx_budget, ctx_neighbor,
                self._cache_query_set_hash,
            )
            self._cache_keys["contexts"] = ctx_key


            if self.cache.has("contexts", ctx_key, ["contexts.jsonl"]):
                logger.info(
                    "CACHE_HIT contexts key=%s - skipping ingestion/chunking/"
                    "embeddings/indexing (LLM-only mode)",
                    ctx_key,
                )
                self.is_indexed = True

                self._pending_contexts = self.cache.load_contexts(ctx_key)
                return 0


        required_idx_files: list[str] = (
            ["manifest.json"]
        )
        if self.cache.has("indexes", index_key, []):
            if self.cache.load_index(index_key, self.retriever):
                self.is_indexed = True

                self._hydrate_chunk_lookup_from_cache(chunks_key)
                return 0
            logger.warning("Index cache present but load failed; recomputing.")
            self._miss("indexes", index_key)
        else:
            self._miss("indexes", index_key)


        if self.cache.has("ingestion", ing_key, ["documents.jsonl"]):
            doc_rows: list[dict[str, Any]] = self.cache.load_ingestion(ing_key)
            documents: list[Document] = [
                Document(
                    content=d["content"],
                    metadata=d.get("metadata", {}) or {},
                    source_path=Path(d["source_path"]) if d.get("source_path") else None,
                )
                for d in doc_rows
            ]
        else:
            self._miss("ingestion", ing_key)
            with PerformanceTimer("ingestion") as t_ingest:
                loader: DocumentLoader = DocumentLoader(
                    data_dir=corpus_dir,
                    file_prefixes=corpus_file_prefixes,
                )
                documents = loader.load_all(show_progress=self._show_progress)
            logger.info(
                "Ingesta: %d documentos cargados en %.0f ms",
                len(documents), t_ingest.elapsed_ms,
            )
            self.cache.save_ingestion(
                ing_key, documents, corpus_dir, file_paths, file_hashes,
            )

        if not documents:
            raise FileNotFoundError(
                f"No se encontraron documentos en {corpus_dir}."
            )


        if self.cache.has("chunks", chunks_key, ["chunks.jsonl"]):
            raw_chunks: list[dict[str, Any]] = self.cache.load_chunks_raw(chunks_key)
            all_chunks: list[Chunk] = self._rebuild_chunks_from_dicts(raw_chunks)
        else:
            self._miss("chunks", chunks_key)
            with PerformanceTimer("chunking") as t_chunk:
                all_chunks = []
                _docs_iter: Any = documents
                if self._show_progress:
                    try:
                        from tqdm.auto import tqdm as _tqdm
                        _docs_iter = _tqdm(documents, desc="chunking", unit="doc")
                    except ImportError:
                        pass
                for doc in _docs_iter:
                    doc_source: str = doc.metadata.get("filename", "unknown")
                    all_chunks.extend(self.chunker.chunk(
                        text=doc.content, doc_source=doc_source,
                    ))
            logger.info(
                "Chunking: %d chunks generados en %.0f ms",
                len(all_chunks), t_chunk.elapsed_ms,
            )
            self.cache.save_chunks(chunks_key, all_chunks, {
                "ingestion": ing_key,
                "chunker": chunker_type,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
            })

        self._chunks = all_chunks
        chunk_texts: list[str] = [c.text for c in all_chunks]
        metadatas: list[dict[str, str | int]] = [c.metadata for c in all_chunks]
        self._chunk_lookup = {c.chunk_global_id: c for c in all_chunks if c.chunk_global_id}
        self._doc_chunk_list = {}
        for c in all_chunks:
            self._doc_chunk_list.setdefault(c.doc_source, []).append(c)
        for doc_src in self._doc_chunk_list:
            self._doc_chunk_list[doc_src].sort(key=lambda x: x.chunk_index_in_doc)


        if uses_embeddings:
            assert self.embedder is not None
            assert emb_key is not None
            if self.cache.has("embeddings", emb_key, ["embeddings.npy", "chunk_ids.json"]):
                embeddings, cached_ids = self.cache.load_embeddings(emb_key)

                cur_ids: list[str] = [c.chunk_global_id for c in all_chunks]
                if cached_ids != cur_ids:
                    logger.warning(
                        "Embeddings cache ids mismatch (%d vs %d) - recomputing.",
                        len(cached_ids), len(cur_ids),
                    )
                    self._miss("embeddings", emb_key)
                    embeddings = self.embedder.embed(
                        chunk_texts, show_progress=self._show_progress,
                    )
                    self.cache.save_embeddings(
                        emb_key, embeddings, cur_ids,
                        {"chunks": chunks_key, "model": embedder_name},
                    )
            else:
                self._miss("embeddings", emb_key)
                with PerformanceTimer("embedding") as t_embed:
                    embeddings = self.embedder.embed(
                        chunk_texts, show_progress=self._show_progress,
                    )
                logger.info(
                    "Embeddings: shape %s en %.0f ms",
                    embeddings.shape, t_embed.elapsed_ms,
                )
                self.cache.save_embeddings(
                    emb_key, embeddings,
                    [c.chunk_global_id for c in all_chunks],
                    {"chunks": chunks_key, "model": embedder_name},
                )

            with PerformanceTimer("indexing") as t_index:
                self.retriever.index(
                    embeddings=embeddings, texts=chunk_texts, metadatas=metadatas,
                )
            logger.info("Índice FAISS: %d vectores en %.0f ms",
                        len(chunk_texts), t_index.elapsed_ms)
        else:
            dummy_embeddings: NDArray[np.float32] = np.empty((0,), dtype=np.float32)
            with PerformanceTimer("indexing") as t_index:
                self.retriever.index(
                    embeddings=dummy_embeddings, texts=chunk_texts, metadatas=metadatas,
                )
            logger.info("Índice BM25: %d documentos en %.0f ms",
                        len(chunk_texts), t_index.elapsed_ms)


        try:
            self.cache.save_index(index_key, self.retriever, {
                "chunks": chunks_key,
                "retriever": retriever_type,
                "embeddings": emb_key,
            })
        except Exception as e:
            logger.warning("CACHE save_index failed for %s: %s", index_key, e)

        self.is_indexed = True
        return len(all_chunks)

    def _hydrate_chunk_lookup_from_cache(self, chunks_key: str) -> None:

        assert self.cache is not None
        if not self.cache.has("chunks", chunks_key, ["chunks.jsonl"]):
            logger.warning(
                "Index loaded but chunks cache missing - neighbor expansion will be limited."
            )
            self._chunk_lookup = {}
            self._doc_chunk_list = {}
            return
        raw: list[dict[str, Any]] = self.cache.load_chunks_raw(chunks_key)
        all_chunks: list[Chunk] = self._rebuild_chunks_from_dicts(raw)
        self._chunks = all_chunks
        self._chunk_lookup = {c.chunk_global_id: c for c in all_chunks if c.chunk_global_id}
        self._doc_chunk_list = {}
        for c in all_chunks:
            self._doc_chunk_list.setdefault(c.doc_source, []).append(c)
        for doc_src in self._doc_chunk_list:
            self._doc_chunk_list[doc_src].sort(key=lambda x: x.chunk_index_in_doc)


    def run(self, query: str, query_id: str | None = None) -> PipelineResult:

        total_start: float = time.perf_counter()
        timings: dict[str, float] = {}


        if self.config_name == "no_rag":
            return self._run_no_rag(query, timings, total_start)


        if not self.is_indexed:
            raise RuntimeError(
                "Índice no construido. Ejecuta build_index() antes de run()."
            )


        if self.cache is not None and "contexts" in self._cache_keys:
            qid: str = query_id or self._qid(query)
            cached: dict[str, Any] | None = self._pending_contexts.get(qid)
            if cached is not None:
                return self._run_from_cached_contexts(
                    query=query, qid=qid, cached=cached,
                    timings=timings, total_start=total_start,
                )
            self._miss("contexts", self._cache_keys["contexts"])

        return self._run_rag(query, timings, total_start, query_id=query_id)


    def _run_no_rag(
        self,
        query: str,
        timings: dict[str, float],
        total_start: float,
    ) -> PipelineResult:


        with PerformanceTimer("prompt_build") as t_prompt:
            prompt: str = self.prompt_builder.build(
                question=query,
                contexts=None,
            )
        timings["prompt_build_ms"] = t_prompt.elapsed_ms


        with PerformanceTimer("llm_generation") as t_llm:
            llm_response: LLMResponse = self.llm.generate(prompt)
        timings["llm_generation_ms"] = t_llm.elapsed_ms

        total_ms: float = (time.perf_counter() - total_start) * 1000
        timings["total_pipeline_ms"] = total_ms

        logger.info(
            "Pipeline no_rag completado: %.0f ms total", total_ms
        )

        return PipelineResult(
            query=query,
            answer=llm_response.text,
            contexts=[],
            config_name=self.config_name,
            timings=timings,
            metadata={
                "model": llm_response.model,
                "model_size_gb": llm_response.model_size_gb,
                "model_size_category": llm_response.model_size_category,
                "query_type": llm_response.query_type,
                "tokens_prompt": llm_response.tokens_prompt,
                "tokens_generated": llm_response.tokens_generated,
                "llm_latency_ms": llm_response.latency_ms,
            },
            prompt=prompt,
        )

    def _estimate_tokens(self, text: str) -> int:

        return max(1, len(text) // 4)
    def _select_by_token_budget(
        self,
        results: list[RetrievalResult],
        budget: int,
    ) -> list[RetrievalResult]:

        selected: list[RetrievalResult] = []
        used_tokens: int = 0
        for r in results:
            est: int = self._estimate_tokens(r.text)
            if used_tokens + est > budget and selected:

                break
            selected.append(r)
            used_tokens += est
        logger.info(
            "Token budget: %d tokens usados (budget=%d), %d/%d chunks incluidos",
            used_tokens, budget, len(selected), len(results),
        )
        return selected
    def _apply_neighbor_expansion(
        self,
        results: list[RetrievalResult],
        budget: int,
    ) -> list[RetrievalResult]:

        if not self._doc_chunk_list:
            logger.warning(
                "Neighbor expansion pedida pero _doc_chunk_list esta vacio. "
                "Asegurate de llamar build_index() antes de run()."
            )
            return results


        seen_ids: set[str] = set()
        expanded: list[RetrievalResult] = []
        for base_result in results:
            base_gid: str = base_result.chunk_global_id
            doc_src: str = base_result.source_file or base_result.doc_id
            doc_chunks: list[Chunk] = self._doc_chunk_list.get(doc_src, [])
            base_idx: int = base_result.chunk_index_in_doc

            candidate_indices: list[int] = [base_idx - 1, base_idx, base_idx + 1]
            for ci in candidate_indices:
                if ci < 0 or ci >= len(doc_chunks):
                    continue
                neighbor: Chunk = doc_chunks[ci]
                gid: str = neighbor.chunk_global_id
                if not gid or gid in seen_ids:
                    continue
                seen_ids.add(gid)
                if gid == base_gid:

                    expanded.append(base_result)
                else:


                    from dataclasses import replace as _dc_replace
                    neighbor_result: RetrievalResult = RetrievalResult(
                        text=neighbor.text,
                        score=0.0,
                        chunk_id=-1,
                        metadata=neighbor.metadata,
                        chunk_global_id=gid,
                        doc_id=neighbor.doc_id,
                        source_file=neighbor.doc_source,
                        chunk_index_in_doc=neighbor.chunk_index_in_doc,
                        retrieval_score_type="neighbor_expansion",
                        reranker_score=None,
                        reranker_score_type="neighbor_expansion",
                    )
                    expanded.append(neighbor_result)

        trimmed: list[RetrievalResult] = self._select_by_token_budget(expanded, budget)
        logger.info(
            "Neighbor expansion: %d base chunks -> %d con vecinos -> %d tras recorte",
            len(results),
            len(expanded),
            len(trimmed),
        )
        return trimmed


    @staticmethod
    def _retrieval_result_to_row(r: RetrievalResult) -> dict[str, Any]:

        return {
            "text": r.text,
            "score": float(r.score),
            "chunk_id": int(r.chunk_id),
            "metadata": dict(r.metadata),
            "chunk_global_id": r.chunk_global_id,
            "doc_id": r.doc_id,
            "source_file": r.source_file,
            "chunk_index_in_doc": int(r.chunk_index_in_doc),
            "retrieval_score_type": r.retrieval_score_type,
            "reranker_score": (
                float(r.reranker_score) if r.reranker_score is not None else None
            ),
            "reranker_score_type": r.reranker_score_type,
        }

    @staticmethod
    def _retrieval_result_from_row(row: dict[str, Any]) -> RetrievalResult:

        return RetrievalResult(
            text=row["text"],
            score=float(row.get("score", 0.0)),
            chunk_id=int(row.get("chunk_id", -1)),
            metadata=row.get("metadata", {}) or {},
            chunk_global_id=row.get("chunk_global_id", ""),
            doc_id=row.get("doc_id", ""),
            source_file=row.get("source_file", ""),
            chunk_index_in_doc=int(row.get("chunk_index_in_doc", -1)),
            retrieval_score_type=row.get("retrieval_score_type", ""),
            reranker_score=row.get("reranker_score"),
            reranker_score_type=row.get("reranker_score_type", ""),
        )

    def _run_from_cached_contexts(
        self,
        query: str,
        qid: str,
        cached: dict[str, Any],
        timings: dict[str, float],
        total_start: float,
    ) -> PipelineResult:

        final_contexts: list[str] = list(cached.get("contexts", []))
        sources: list[dict[str, Any]] = list(cached.get("sources", []))

        with PerformanceTimer("prompt_build") as t_prompt:
            prompt: str = self.prompt_builder.build(
                question=query, contexts=final_contexts,
            )
        timings["prompt_build_ms"] = t_prompt.elapsed_ms

        with PerformanceTimer("llm_generation") as t_llm:
            llm_response: LLMResponse = self.llm.generate(prompt)
        timings["llm_generation_ms"] = t_llm.elapsed_ms

        total_ms: float = (time.perf_counter() - total_start) * 1000


        retr_t = self._load_cached_timings("retrieval").get(qid, {})
        rer_t  = self._load_cached_timings("reranking").get(qid, {})
        ctx_t  = self._load_cached_timings("contexts").get(qid, {})
        timings["query_embedding_ms"] = float(retr_t.get("query_embedding_ms") or 0.0)
        timings["retrieval_ms"]       = float(retr_t.get("retrieval_ms") or 0.0)
        timings["reranking_ms"]       = float(rer_t.get("reranking_ms") or 0.0)
        timings["context_selection_ms"] = float(ctx_t.get("context_selection_ms") or 0.0)

        timings["retrieval_total_ms"] = (
            timings["query_embedding_ms"] + timings["retrieval_ms"]
            + timings["reranking_ms"] + timings["context_selection_ms"]
        )

        timings["retrieval_total_ms"] = (
                timings["query_embedding_ms"]
                + timings["retrieval_ms"]
                + timings["reranking_ms"]
                + timings["context_selection_ms"]
        )

        timings_source: dict[str, str] = {
            "query_embedding":   "cached" if retr_t else "missing",
            "retrieval":         "cached" if retr_t else "missing",
            "reranking":         "cached" if rer_t else "missing",
            "context_selection": "cached" if ctx_t else "missing",
            "prompt_build":      "live",
            "llm_generation":    "live",
        }

        logger.info(
            "CACHE_HIT contexts qid=%s -> LLM-only path (%.0f ms total, "
            "stage timings: %s)",
            qid, total_ms, timings_source,
        )

        metadata: dict[str, Any] = {
            "model": llm_response.model,
            "model_size_gb": llm_response.model_size_gb,
            "model_size_category": llm_response.model_size_category,
            "query_type": llm_response.query_type,
            "tokens_prompt": llm_response.tokens_prompt,
            "tokens_generated": llm_response.tokens_generated,
            "llm_latency_ms": llm_response.latency_ms,
            "from_cache": True,
            "cache_keys": dict(self._cache_keys),
            "timings_source": timings_source,


            "memory_peak_mb_cached": (
                ctx_t.get("memory_peak_mb")
                or rer_t.get("memory_peak_mb")
                or retr_t.get("memory_peak_mb")
            ),
        }

        for k in (
            "retriever_type", "retrieval_score_type", "reranker_score_type",
            "num_chunks_retrieved", "num_chunks_reranked", "num_chunks_final",
            "context_chars_total", "context_tokens_est", "avg_chunk_size_chars",
            "source_files_used", "chunk_ids_final", "chunker", "prompt_version",
            "context_selection_mode", "neighbor_expansion_used",
            "retrieval_scores", "reranker_scores", "retrieval_top_k_details",
            "context_sources",
        ):
            if k in cached:
                metadata[k] = cached[k]

        return PipelineResult(
            query=query,
            answer=llm_response.text,
            contexts=final_contexts,
            config_name=self.config_name,
            timings=timings,
            metadata=metadata,
            prompt=prompt,
            sources=sources,
        )

    def _run_rag(
        self,
        query: str,
        timings: dict[str, float],
        total_start: float,
        query_id: str | None = None,
    ) -> PipelineResult:

        assert self.retriever is not None
        assert self.reranker is not None
        retriever_type: str = self.config["retriever"]
        uses_embeddings: bool = (retriever_type == "faiss")

        context_mode: str = self.config.get("context_selection_mode", "top_n")
        token_budget: int = int(self.config.get("context_token_budget", 4000))
        use_neighbor_expansion: bool = bool(self.config.get("neighbor_expansion", False))


        qid: str = query_id or (self._qid(query) if self.cache is not None else "")


        _src_retrieval: str = "live"
        _src_reranking: str = "live"
        _src_contexts: str = "live"


        retrieved_results: list[RetrievalResult] | None = None
        if self.cache is not None and "retrieval" in self._cache_keys:
            r_key: str = self._cache_keys["retrieval"]
            if not self._pending_retrieval and self.cache.has(
                "retrieval", r_key, ["retrieved_top_k.jsonl"],
            ):
                self._pending_retrieval = self.cache.load_retrieval(r_key)
            cached_rows: list[dict[str, Any]] | None = self._pending_retrieval.get(qid)
            if cached_rows is not None:
                retrieved_results = [
                    self._retrieval_result_from_row(r) for r in cached_rows
                ]


                cached_t = self._load_cached_timings("retrieval").get(qid, {})
                timings["query_embedding_ms"] = float(
                    cached_t.get("query_embedding_ms") or 0.0
                )
                timings["retrieval_ms"] = float(
                    cached_t.get("retrieval_ms") or 0.0
                )
                _src_retrieval = "cached" if cached_t else "missing"
                logger.info(
                    "CACHE_HIT retrieval qid=%s n=%d (timings=%s)",
                    qid, len(retrieved_results), _src_retrieval,
                )

        query_embedding: NDArray[np.float32] | None = None
        if retrieved_results is None:
            if uses_embeddings:
                assert self.embedder is not None
                with PerformanceTimer("query_embedding") as t_qembed:
                    query_embedding = self.embedder.embed_query(query)
                timings["query_embedding_ms"] = t_qembed.elapsed_ms
            else:
                timings["query_embedding_ms"] = 0.0
            with PerformanceTimer("retrieval") as t_retrieve:
                retrieved_results = self.retriever.retrieve(
                    query_embedding=query_embedding,
                    query_text=query,
                )
            timings["retrieval_ms"] = t_retrieve.elapsed_ms
            if self.cache is not None and qid:
                self._pending_retrieval[qid] = [
                    self._retrieval_result_to_row(r) for r in retrieved_results
                ]


                self._pending_retrieval_timings[qid] = {
                    "query_embedding_ms": float(timings["query_embedding_ms"]),
                    "retrieval_ms":       float(timings["retrieval_ms"]),
                    "memory_peak_mb":     self._capture_memory_mb(),
                }
            _src_retrieval = "live"
        retrieved_scores: list[float] = [r.score for r in retrieved_results]
        retrieval_score_type: str = (
            retrieved_results[0].retrieval_score_type if retrieved_results else ""
        )
        logger.info(
            "Retrieval (%s / %s): %d fragmentos (scores: %s)",
            retriever_type,
            retrieval_score_type,
            len(retrieved_results),
            ", ".join(f"{s:.4f}" for s in retrieved_scores),
        )


        retrieval_top_k_details: list[dict] = [
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
            for i, r in enumerate(retrieved_results)
        ]


        reranked_results: list[RetrievalResult] | None = None
        if self.cache is not None and "reranking" in self._cache_keys:
            rr_key: str = self._cache_keys["reranking"]
            if not self._pending_reranking and self.cache.has(
                "reranking", rr_key, ["reranked_top_n.jsonl"],
            ):
                self._pending_reranking = self.cache.load_reranking(rr_key)
            cached_rr: list[dict[str, Any]] | None = self._pending_reranking.get(qid)
            if cached_rr is not None:
                reranked_results = [
                    self._retrieval_result_from_row(r) for r in cached_rr
                ]
                cached_t = self._load_cached_timings("reranking").get(qid, {})
                timings["reranking_ms"] = float(
                    cached_t.get("reranking_ms") or 0.0
                )
                _src_reranking = "cached" if cached_t else "missing"
                logger.info(
                    "CACHE_HIT reranking qid=%s n=%d (timings=%s)",
                    qid, len(reranked_results), _src_reranking,
                )

        if reranked_results is None:
            with PerformanceTimer("reranking") as t_rerank:
                reranked_results = self.reranker.rerank_results(
                    query=query,
                    results=retrieved_results,
                )
            timings["reranking_ms"] = t_rerank.elapsed_ms
            if self.cache is not None and qid:
                self._pending_reranking[qid] = [
                    self._retrieval_result_to_row(r) for r in reranked_results
                ]
                self._pending_reranking_timings[qid] = {
                    "reranking_ms":   float(timings["reranking_ms"]),
                    "memory_peak_mb": self._capture_memory_mb(),
                }
            _src_reranking = "live"
        else:

            class _Z:
                elapsed_ms: float = 0.0
            t_rerank = _Z()
        reranker_cls: str = type(self.reranker).__name__
        stage_label: str = "Re-ranking" if reranker_cls == "CrossEncoderReranker" else "Recorte"
        reranker_scores: list[float] = [
            r.reranker_score for r in reranked_results if r.reranker_score is not None
        ]
        reranker_score_type: str = (
            reranked_results[0].reranker_score_type if reranked_results else ""
        )
        logger.info(
            "%s (%s / %s): %d -> %d fragmentos (scores: %s)",
            stage_label,
            reranker_cls,
            reranker_score_type,
            len(retrieved_results),
            len(reranked_results),
            ", ".join(f"{s:.4f}" for s in reranker_scores),
        )

        if context_mode == "token_budget":
            final_results: list[RetrievalResult] = self._select_by_token_budget(
                reranked_results, token_budget
            )
        else:

            final_results = reranked_results

        neighbor_expansion_used: bool = False
        with PerformanceTimer("context_selection") as t_ctx:
            if use_neighbor_expansion and self._doc_chunk_list:
                pre_expansion_count: int = len(final_results)
                final_results = self._apply_neighbor_expansion(final_results, token_budget)
                neighbor_expansion_used = len(final_results) != pre_expansion_count
        timings["context_selection_ms"] = t_ctx.elapsed_ms

        context_chars: int = sum(len(r.text) for r in final_results)
        context_tokens_est: int = self._estimate_tokens("".join(r.text for r in final_results))
        avg_chunk_size: float = (
            context_chars / len(final_results) if final_results else 0.0
        )
        source_files_used: list[str] = list(dict.fromkeys(
            r.source_file for r in final_results if r.source_file
        ))
        chunk_ids_final: list[str] = [
            r.chunk_global_id for r in final_results if r.chunk_global_id
        ]
        logger.info(
            "Contexto final: %d chunks, %d chars, ~%d tokens est."
            " (modo=%s, vecinos=%s)",
            len(final_results),
            context_chars,
            context_tokens_est,
            context_mode,
            neighbor_expansion_used,
        )


        final_contexts: list[str] = [r.text for r in final_results]
        sources: list[SourceInfo] = [
            source_info_from_result(r, f"S{i + 1}")
            for i, r in enumerate(final_results)
        ]

        with PerformanceTimer("prompt_build") as t_prompt:
            prompt: str = self.prompt_builder.build(
                question=query,
                contexts=final_contexts,
            )
        timings["prompt_build_ms"] = t_prompt.elapsed_ms

        with PerformanceTimer("llm_generation") as t_llm:
            llm_response: LLMResponse = self.llm.generate(prompt)
        timings["llm_generation_ms"] = t_llm.elapsed_ms
        total_ms: float = (time.perf_counter() - total_start) * 1000

        timings["retrieval_total_ms"] = (
            timings["query_embedding_ms"]
            + timings["retrieval_ms"]
            + timings["reranking_ms"]
        )
        timings["total_pipeline_ms"] = (
                timings["retrieval_total_ms"]
                + timings["prompt_build_ms"]
                + timings["llm_generation_ms"]
        )
        logger.info(
            "Pipeline '%s' completado: retrieval=%.0f ms, "
            "generation=%.0f ms, total=%.0f ms",
            self.config_name,
            timings["retrieval_total_ms"],
            t_llm.elapsed_ms,
            total_ms,
        )


        if self.cache is not None and qid:
            self._pending_contexts[qid] = {
                "contexts": final_contexts,
                "sources": [s.to_dict() for s in sources],
                "retriever_type": retriever_type,
                "retrieval_score_type": retrieval_score_type,
                "reranker_score_type": reranker_score_type,
                "num_chunks_retrieved": len(retrieved_results),
                "num_chunks_reranked": len(reranked_results),
                "num_chunks_final": len(final_results),
                "context_chars_total": context_chars,
                "context_tokens_est": context_tokens_est,
                "avg_chunk_size_chars": round(avg_chunk_size, 2),
                "source_files_used": source_files_used,
                "chunk_ids_final": chunk_ids_final,
                "chunker": self.config.get("chunker", ""),
                "prompt_version": self.config.get("prompt_version", ""),
                "context_selection_mode": context_mode,
                "neighbor_expansion_used": neighbor_expansion_used,
                "retrieval_top_k_details": retrieval_top_k_details,
                "context_sources": [s.to_dict() for s in sources],
            }


            self._pending_contexts_timings[qid] = {
                "context_selection_ms": float(timings.get("context_selection_ms", 0.0)),
                "memory_peak_mb":       self._capture_memory_mb(),
            }


        timings_source: dict[str, str] = {
            "query_embedding": _src_retrieval,
            "retrieval":       _src_retrieval,
            "reranking":       _src_reranking,
            "context_selection": _src_contexts,
            "prompt_build":    "live",
            "llm_generation":  "live",
        }
        return PipelineResult(
            query=query,
            answer=llm_response.text,
            contexts=final_contexts,
            config_name=self.config_name,
            timings=timings,
            metadata={
                "timings_source": timings_source,
                "model": llm_response.model,
                "model_size_gb": llm_response.model_size_gb,
                "model_size_category": llm_response.model_size_category,
                "query_type": llm_response.query_type,
                "tokens_prompt": llm_response.tokens_prompt,
                "tokens_generated": llm_response.tokens_generated,
                "llm_latency_ms": llm_response.latency_ms,
                "retriever_type": retriever_type,
                "retrieval_score_type": retrieval_score_type,
                "reranker_score_type": reranker_score_type,
                "num_chunks_retrieved": len(retrieved_results),
                "num_chunks_reranked": len(reranked_results),
                "num_chunks_final": len(final_results),
                "context_chars_total": context_chars,
                "context_tokens_est": context_tokens_est,
                "avg_chunk_size_chars": round(avg_chunk_size, 2),
                "source_files_used": source_files_used,
                "chunk_ids_final": chunk_ids_final,
                "chunker": self.config.get("chunker", ""),
                "prompt_version": self.config.get("prompt_version", ""),
                "context_selection_mode": context_mode,
                "neighbor_expansion_used": neighbor_expansion_used,

                "retrieval_scores": [
                    {"rank": i+1, "score": round(r.score, 6),
                     "type": r.retrieval_score_type,
                     "chunk_global_id": r.chunk_global_id}
                    for i, r in enumerate(retrieved_results)
                ],
                "reranker_scores": [
                    {"rank": i+1,
                     "reranker_score": round(r.reranker_score, 6) if r.reranker_score is not None else None,
                     "retrieval_score": round(r.score, 6),
                     "reranker_score_type": r.reranker_score_type,
                     "retrieval_score_type": r.retrieval_score_type,
                     "chunk_global_id": r.chunk_global_id}
                    for i, r in enumerate(reranked_results)
                ],

                "retrieval_top_k_details": retrieval_top_k_details,

                "context_sources": [s.to_dict() for s in sources],
            },
            prompt=prompt,
            sources=[s.to_dict() for s in sources],
        )

    def flush_cache(self) -> None:

        if self.cache is None:
            return

        if not (self._pending_retrieval or self._pending_reranking
                or self._pending_contexts):
            return

        if "retrieval" in self._cache_keys and self._pending_retrieval:
            self.cache.save_retrieval(
                self._cache_keys["retrieval"],
                self._pending_retrieval,
                {
                    "dataset": getattr(self, "_cache_dataset_name", ""),
                    "index": self._cache_keys.get("index", ""),
                    "top_k": int(self.config.get("top_k", 0)),
                    "query_set": self._cache_query_set_hash,


                    "retriever": str(self.config.get("retriever", "")),
                    "retrieval_model": (
                        str(self.config.get("embedder", ""))
                        if self.config.get("retriever") == "faiss"
                        else "bm25"
                    ),
                },


                timings=self._pending_retrieval_timings,
            )
        if "reranking" in self._cache_keys and self._pending_reranking:
            self.cache.save_reranking(
                self._cache_keys["reranking"],
                self._pending_reranking,
                {
                    "dataset": getattr(self, "_cache_dataset_name", ""),
                    "retrieval": self._cache_keys.get("retrieval", ""),
                    "reranker_top_n": int(self.config.get("reranker_top_n",
                                            self.config.get("top_k", 0))),
                    "query_set": self._cache_query_set_hash,

                    "reranker_model": str(self.config.get("reranker", "")),
                },
                timings=self._pending_reranking_timings,
            )
        if "contexts" in self._cache_keys and self._pending_contexts:
            self.cache.save_contexts(
                self._cache_keys["contexts"],
                self._pending_contexts,
                {
                    "dataset": getattr(self, "_cache_dataset_name", ""),
                    "reranking": self._cache_keys.get("reranking", ""),
                    "config": self.config_name,
                    "context_mode": self.config.get("context_selection_mode", "top_n"),
                    "token_budget": int(self.config.get("context_token_budget", 4000)),
                    "neighbor_expansion": bool(self.config.get("neighbor_expansion", False)),
                    "query_set": self._cache_query_set_hash,


                    "retriever": str(self.config.get("retriever", "")),
                    "retrieval_model": (
                        str(self.config.get("embedder", ""))
                        if self.config.get("retriever") == "faiss"
                        else "bm25"
                    ),
                    "reranker_model": str(self.config.get("reranker", "")),
                },
                timings=self._pending_contexts_timings,
            )

    def run_batch(
        self,
        queries: list[str],
        query_ids: list[str] | None = None,
    ) -> list[PipelineResult]:

        results: list[PipelineResult] = []
        if query_ids is not None and len(query_ids) != len(queries):
            raise ValueError("len(query_ids) must equal len(queries)")

        for i, query in enumerate(queries):
            qid: str | None = query_ids[i] if query_ids else None
            logger.info(
                "Query %d/%d: %s",
                i + 1, len(queries), query[:80],
            )
            try:
                result: PipelineResult = self.run(query=query, query_id=qid)
                results.append(result)
            except (ConnectionError, RuntimeError) as e:
                logger.error("Error en query %d: %s", i + 1, e)
                results.append(
                    PipelineResult(
                        query=query,
                        answer=f"[ERROR] {e}",
                        config_name=self.config_name,
                        timings={},
                        metadata={"error": str(e)},
                    )
                )


        try:
            self.flush_cache()
        except Exception as e:
            logger.warning("flush_cache failed: %s", e)

        logger.info(
            "Batch completado: %d/%d consultas exitosas",
            sum(1 for r in results if "error" not in r.metadata),
            len(queries),
        )
        return results
