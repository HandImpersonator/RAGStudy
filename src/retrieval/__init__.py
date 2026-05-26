from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import logging
import pickle
from pathlib import Path
from typing import Any
import numpy as np
from numpy.typing import NDArray

logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:


    text: str
    score: float
    chunk_id: int
    metadata: dict[str, str | int | float] = field(default_factory=dict)


    chunk_global_id: str = ""
    doc_id: str = ""
    source_file: str = ""
    chunk_index_in_doc: int = -1
    retrieval_score_type: str = ""
    reranker_score: float | None = None
    reranker_score_type: str = ""


class BaseRetriever(ABC):


    def __init__(self, top_k: int = 5) -> None:
        self.top_k: int = top_k

    @abstractmethod
    def index(
        self,
        embeddings: NDArray[np.float32],
        texts: list[str],
        metadatas: list[dict[str, str | int]] | None = None,
    ) -> None:

        ...

    @abstractmethod
    def retrieve(
        self,
        query_embedding: NDArray[np.float32] | None = None,
        query_text: str = "",
    ) -> list[RetrievalResult]:

        ...


class FAISSRetriever(BaseRetriever):


    BASELINE_TOP_K: int = 5

    def __init__(self, top_k: int = BASELINE_TOP_K) -> None:
        super().__init__(top_k=top_k)
        self._index = None
        self._texts: list[str] = []
        self._metadatas: list[dict[str, str | int]] = []

    def index(
        self,
        embeddings: NDArray[np.float32],
        texts: list[str],
        metadatas: list[dict[str, str | int]] | None = None,
    ) -> None:

        try:
            import faiss
        except ImportError as e:
            raise ImportError(
                "faiss-cpu requerido. Instalar: pip install faiss-cpu"
            ) from e


        faiss.normalize_L2(embeddings)

        dimension: int = embeddings.shape[1]
        self._index = faiss.IndexFlatIP(dimension)
        self._index.add(embeddings)
        self._texts = texts
        self._metadatas = metadatas or [{} for _ in texts]

        logger.info(
            "Índice FAISS construido: %d vectores, dim=%d",
            len(texts),
            dimension,
        )

    def save(self, index_dir: Path) -> None:

        if self._index is None:
            raise RuntimeError("El índice no está construido. Llama a index() primero.")

        try:
            import faiss as faiss_lib
        except ImportError as e:
            raise ImportError("faiss-cpu requerido. Instalar: pip install faiss-cpu") from e

        index_dir.mkdir(parents=True, exist_ok=True)
        faiss_lib.write_index(self._index, str(index_dir / "faiss.index"))

        meta: dict[str, Any] = {"texts": self._texts, "metadatas": self._metadatas}
        with open(index_dir / "faiss_meta.pkl", "wb") as f:
            pickle.dump(meta, f)

        logger.info("Índice FAISS guardado en %s (%d vectores)", index_dir, len(self._texts))

    def load(self, index_dir: Path) -> bool:

        index_file: Path = index_dir / "faiss.index"
        meta_file: Path = index_dir / "faiss_meta.pkl"

        if not index_file.exists() or not meta_file.exists():
            logger.info("No se encontró índice FAISS persistido en %s", index_dir)
            return False

        try:
            import faiss as faiss_lib
        except ImportError as e:
            raise ImportError("faiss-cpu requerido. Instalar: pip install faiss-cpu") from e

        self._index = faiss_lib.read_index(str(index_file))

        with open(meta_file, "rb") as f:
            meta: dict[str, Any] = pickle.load(f)

        self._texts = meta["texts"]
        self._metadatas = meta["metadatas"]

        logger.info(
            "Índice FAISS cargado desde %s (%d vectores)",
            index_dir,
            len(self._texts),
        )
        return True

    def retrieve(
        self,
        query_embedding: NDArray[np.float32] | None = None,
        query_text: str = "",
    ) -> list[RetrievalResult]:

        if query_embedding is None:
            raise ValueError("FAISSRetriever requiere query_embedding (no None).")
        if self._index is None:
            raise RuntimeError("Índice no construido. Llama a index() primero.")

        import faiss


        query: NDArray[np.float32] = query_embedding.reshape(1, -1).copy()
        faiss.normalize_L2(query)

        scores, indices = self._index.search(query, self.top_k)

        results: list[RetrievalResult] = []
        for i in range(len(indices[0])):
            idx: int = int(indices[0][i])
            if idx < 0:
                continue
            meta: dict[str, Any] = self._metadatas[idx]


            doc_src: str = str(meta.get("doc_source", ""))
            results.append(
                RetrievalResult(
                    text=self._texts[idx],
                    score=float(scores[0][i]),
                    chunk_id=idx,
                    metadata=meta,
                    chunk_global_id=str(meta.get("chunk_global_id", f"unknown::chunk::{idx:04d}")),
                    doc_id=doc_src,
                    source_file=doc_src,
                    chunk_index_in_doc=int(meta.get("chunk_index_in_doc", idx)),
                    retrieval_score_type="cosine_similarity",
                )
            )

        logger.info(
            "FAISSRetriever: %d resultados (top_k=%d)",
            len(results),
            self.top_k,
        )
        return results


class BM25Retriever(BaseRetriever):


    BASELINE_TOP_K: int = 5

    def __init__(self, top_k: int = BASELINE_TOP_K) -> None:
        super().__init__(top_k=top_k)

        self._bm25 = None
        self._texts: list[str] = []
        self._metadatas: list[dict[str, str | int]] = []

    def index(
        self,
        embeddings: NDArray[np.float32],
        texts: list[str],
        metadatas: list[dict[str, str | int]] | None = None,
    ) -> None:

        try:
            from rank_bm25 import BM25Okapi
        except ImportError as e:
            raise ImportError(
                "rank-bm25 requerido para BM25Retriever. "
                "Instalar: pip install rank-bm25"
            ) from e


        tokenized_corpus: list[list[str]] = [
            text.lower().split() for text in texts
        ]

        self._bm25 = BM25Okapi(tokenized_corpus)
        self._texts = texts
        self._metadatas = metadatas or [{} for _ in texts]

        logger.info(
            "Índice BM25 construido: %d documentos",
            len(texts),
        )

    def save(self, index_dir: Path) -> None:

        index_dir.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "bm25": self._bm25,
            "texts": self._texts,
            "metadatas": self._metadatas,
        }
        with (index_dir / "bm25_index.pkl").open("wb") as fh:
            pickle.dump(payload, fh, protocol=pickle.HIGHEST_PROTOCOL)
        logger.info(
            "Índice BM25 guardado en %s (%d documentos)",
            index_dir,
            len(self._texts),
        )

    def load(self, index_dir: Path) -> bool:

        pkl: Path = index_dir / "bm25_index.pkl"
        if not pkl.exists():
            logger.info("No se encontró índice BM25 en %s", index_dir)
            return False
        try:
            with pkl.open("rb") as fh:
                payload: dict[str, Any] = pickle.load(fh)
            self._bm25 = payload["bm25"]
            self._texts = payload["texts"]
            self._metadatas = payload["metadatas"]
            logger.info(
                "Índice BM25 cargado desde %s (%d documentos)",
                index_dir,
                len(self._texts),
            )
            return True
        except (OSError, KeyError, pickle.UnpicklingError) as exc:
            logger.warning("Error cargando índice BM25 desde %s: %s", index_dir, exc)
            return False

    def retrieve(
        self,
        query_embedding: NDArray[np.float32] | None = None,
        query_text: str = "",
    ) -> list[RetrievalResult]:

        if self._bm25 is None:
            raise RuntimeError("Índice BM25 no construido. Llama a index() primero.")
        if not query_text.strip():
            raise ValueError("BM25Retriever requiere query_text no vacío.")


        tokenized_query: list[str] = query_text.lower().split()


        scores_all: list[float] = self._bm25.get_scores(tokenized_query).tolist()


        indexed_scores: list[tuple[int, float]] = sorted(
            enumerate(scores_all),
            key=lambda x: x[1],
            reverse=True,
        )[:self.top_k]

        results: list[RetrievalResult] = []
        for idx, score in indexed_scores:

            if score <= 0.0:
                continue
            meta: dict[str, Any] = self._metadatas[idx]
            doc_src: str = str(meta.get("doc_source", ""))
            results.append(
                RetrievalResult(
                    text=self._texts[idx],
                    score=score,
                    chunk_id=idx,
                    metadata=meta,
                    chunk_global_id=str(meta.get("chunk_global_id", f"unknown::chunk::{idx:04d}")),
                    doc_id=doc_src,
                    source_file=doc_src,
                    chunk_index_in_doc=int(meta.get("chunk_index_in_doc", idx)),
                    retrieval_score_type="bm25",
                )
            )

        logger.info(
            "BM25Retriever: %d resultados (top_k=%d, query='%s...')",
            len(results),
            self.top_k,
            query_text[:50],
        )
        return results
