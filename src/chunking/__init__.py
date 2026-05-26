from __future__ import annotations

import os
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import logging
import re

from typing_extensions import Any, deprecated

logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class Chunk:


    text: str
    chunk_id: int
    doc_source: str
    metadata: dict[str, str | int] = field(default_factory=dict)


    doc_id: str = ""
    chunk_global_id: str = ""
    chunk_index_in_doc: int = 0
    chunker_method: str = ""


def _make_global_id(doc_source: str, chunk_index: int) -> str:

    return f"{doc_source}::chunk::{chunk_index:04d}"


class BaseChunker(ABC):


    def __init__(self, chunk_size: int, overlap: int) -> None:
        self.chunk_size: int = chunk_size
        self.overlap: int = overlap

    @abstractmethod
    def chunk(self, text: str, doc_source: str = "") -> list[Chunk]:

        ...


class FixedChunker(BaseChunker):


    BASELINE_CHUNK_SIZE: int = 512
    BASELINE_OVERLAP: int = 105

    def __init__(
        self,
        chunk_size: int = BASELINE_CHUNK_SIZE,
        overlap: int = BASELINE_OVERLAP,
    ) -> None:
        super().__init__(chunk_size=chunk_size, overlap=overlap)

    def chunk(self, text: str, doc_source: str = "") -> list[Chunk]:

        chunks: list[Chunk] = []
        start: int = 0
        chunk_id: int = 0

        while start < len(text):
            end: int = start + self.chunk_size
            fragment: str = text[start:end]

            if fragment.strip():
                global_id: str = _make_global_id(doc_source, chunk_id)
                meta: dict[str, str | int] = {


                    "doc_source": doc_source,
                    "chunk_global_id": global_id,
                    "chunk_index_in_doc": chunk_id,
                    "chunker_method": "fixed",

                    "start_char": start,
                    "end_char": min(end, len(text)),
                    "chunk_size": self.chunk_size,
                    "overlap": self.overlap,
                    "strategy": "fixed",
                }
                chunks.append(
                    Chunk(
                        text=fragment.strip(),
                        chunk_id=chunk_id,
                        doc_source=doc_source,
                        metadata=meta,
                        doc_id=doc_source,
                        chunk_global_id=global_id,
                        chunk_index_in_doc=chunk_id,
                        chunker_method="fixed",
                    )
                )
                chunk_id += 1

            start += self.chunk_size - self.overlap


        logger.debug(
            "FixedChunker: %d chunks generados (size=%d, overlap=%d)",
            len(chunks),
            self.chunk_size,
            self.overlap,
        )
        return chunks

@deprecated("Old paragraph heuristic semantic chunker")
class OldSemanticChunker(BaseChunker):


    OPTIMIZED_CHUNK_SIZE: int = 512
    OPTIMIZED_OVERLAP: int = 105


    _SECTION_PATTERN: re.Pattern[str] = re.compile(r"^#{1,6}\s+", re.MULTILINE)

    def __init__(
        self,
        chunk_size: int = OPTIMIZED_CHUNK_SIZE,
        overlap: int = OPTIMIZED_OVERLAP,
    ) -> None:
        super().__init__(chunk_size=chunk_size, overlap=overlap)

    def chunk(self, text: str, doc_source: str = "") -> list[Chunk]:


        paragraphs: list[str] = self._split_paragraphs(text)

        if not paragraphs:
            return []


        chunks: list[Chunk] = []
        chunk_id: int = 0
        current_paragraphs: list[str] = []
        current_len: int = 0

        def _emit_chunk(paras: list[str]) -> None:

            nonlocal chunk_id
            chunk_text: str = "\n\n".join(paras)
            global_id: str = _make_global_id(doc_source, chunk_id)
            meta: dict[str, str | int] = {
                "doc_source": doc_source,
                "chunk_global_id": global_id,
                "chunk_index_in_doc": chunk_id,
                "chunker_method": "semantic",
                "start_char": text.find(paras[0]),
                "end_char": text.find(paras[0]) + len(chunk_text),
                "chunk_size": self.chunk_size,
                "overlap": self.overlap,
                "strategy": "semantic",
                "paragraphs": len(paras),
            }
            chunks.append(
                Chunk(
                    text=chunk_text.strip(),
                    chunk_id=chunk_id,
                    doc_source=doc_source,
                    metadata=meta,
                    doc_id=doc_source,
                    chunk_global_id=global_id,
                    chunk_index_in_doc=chunk_id,
                    chunker_method="semantic",
                )
            )
            chunk_id += 1

        for para in paragraphs:
            para_len: int = len(para)


            if para_len > self.chunk_size and not current_paragraphs:
                global_id = _make_global_id(doc_source, chunk_id)
                meta = {
                    "doc_source": doc_source,
                    "chunk_global_id": global_id,
                    "chunk_index_in_doc": chunk_id,
                    "chunker_method": "semantic",
                    "start_char": text.find(para),
                    "end_char": text.find(para) + para_len,
                    "chunk_size": self.chunk_size,
                    "overlap": self.overlap,
                    "strategy": "semantic",
                    "paragraphs": 1,
                    "oversized": 1,
                }
                chunks.append(
                    Chunk(
                        text=para.strip(),
                        chunk_id=chunk_id,
                        doc_source=doc_source,
                        metadata=meta,
                        doc_id=doc_source,
                        chunk_global_id=global_id,
                        chunk_index_in_doc=chunk_id,
                        chunker_method="semantic",
                    )
                )
                chunk_id += 1
                continue


            separator_cost: int = 2 if current_paragraphs else 0
            if current_len + separator_cost + para_len <= self.chunk_size:
                current_paragraphs.append(para)
                current_len += separator_cost + para_len
            else:

                if current_paragraphs:
                    _emit_chunk(current_paragraphs)


                overlap_paragraphs: list[str] = self._compute_overlap(current_paragraphs)


                current_paragraphs = overlap_paragraphs + [para]
                current_len = sum(len(p) for p in current_paragraphs) + (
                    2 * (len(current_paragraphs) - 1)
                    if len(current_paragraphs) > 1
                    else 0
                )


        if current_paragraphs:
            _emit_chunk(current_paragraphs)


        logger.debug(
            "SemanticChunker: %d chunks generados (size=%d, overlap=%d, "
            "paragraphs_total=%d)",
            len(chunks),
            self.chunk_size,
            self.overlap,
            len(paragraphs),
        )
        return chunks

    def _split_paragraphs(self, text: str) -> list[str]:

        raw_paragraphs: list[str] = re.split(r"\n\s*\n", text)
        paragraphs: list[str] = [
            p.strip() for p in raw_paragraphs if p.strip()
        ]
        return paragraphs

    def _compute_overlap(self, paragraphs: list[str]) -> list[str]:

        if not paragraphs or self.overlap <= 0:
            return []

        overlap_paras: list[str] = []
        accumulated: int = 0

        for para in reversed(paragraphs):
            if accumulated >= self.overlap:
                break
            overlap_paras.insert(0, para)
            accumulated += len(para)

        return overlap_paras


class SemanticChunker(BaseChunker):


    OPTIMIZED_CHUNK_SIZE: int = 512
    OPTIMIZED_OVERLAP: int = 105

    DEFAULT_EMBEDDING_MODEL: str = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"


    DEFAULT_BREAKPOINT_STRATEGY: str = "percentile"

    @classmethod
    def get_embedding_model(cls) -> str:

        return cls.DEFAULT_EMBEDDING_MODEL


    DEFAULT_SIMILARITY_THRESHOLD: float = 0.65


    DEFAULT_BREAKPOINT_PERCENTILE: float = 20.0


    DEFAULT_UNIT_LEVEL: str = "sentence"


    DEFAULT_MIN_CHUNK_SIZE: int = 256

    DEFAULT_DEVICE: str = "auto"
    DEFAULT_BATCH_SIZE: int = 64
    DEFAULT_WARMUP_ENABLED: bool = True

    _MODEL_CACHE: dict[tuple[str, str], Any] = {}
    _WARMED_UP: set[tuple[str, str]] = set()

    _SENTENCE_SPLIT_PATTERN: re.Pattern[str] = re.compile(
        r"(?<=[.!?])\s+(?=(?:[A-Z0-9#\"'¿¡(\[]|$))"
    )

    def __init__(
        self,
        chunk_size: int = OPTIMIZED_CHUNK_SIZE,
        overlap: int = OPTIMIZED_OVERLAP,
        embedding_model: str | None = None,
        breakpoint_strategy: str | None = None,
        similarity_threshold: float | None = None,
        breakpoint_percentile: float | None = None,
        unit_level: str | None = None,
        min_chunk_size: int | None = None,
    ) -> None:
        super().__init__(chunk_size=chunk_size, overlap=overlap)

        self.embedding_model: str = (
            embedding_model
            or os.getenv("SEMANTIC_CHUNKER_EMBEDDING_MODEL", "")
            or self.DEFAULT_EMBEDDING_MODEL
        )

        self.breakpoint_strategy: str = (
            breakpoint_strategy
            or os.getenv("SEMANTIC_CHUNKER_STRATEGY", "")
            or self.DEFAULT_BREAKPOINT_STRATEGY
        ).strip().lower()

        if self.breakpoint_strategy not in {"threshold", "percentile"}:
            raise ValueError(
                "SemanticChunker breakpoint_strategy must be either "
                f"'threshold' or 'percentile', got: {self.breakpoint_strategy!r}"
            )

        self.similarity_threshold: float = float(
            similarity_threshold
            if similarity_threshold is not None
            else os.getenv(
                "SEMANTIC_CHUNKER_SIMILARITY_THRESHOLD",
                str(self.DEFAULT_SIMILARITY_THRESHOLD),
            )
        )

        self.breakpoint_percentile: float = float(
            breakpoint_percentile
            if breakpoint_percentile is not None
            else os.getenv(
                "SEMANTIC_CHUNKER_BREAKPOINT_PERCENTILE",
                str(self.DEFAULT_BREAKPOINT_PERCENTILE),
            )
        )

        self.unit_level: str = (
            unit_level
            or os.getenv("SEMANTIC_CHUNKER_UNIT_LEVEL", "")
            or self.DEFAULT_UNIT_LEVEL
        ).strip().lower()

        if self.unit_level not in {"sentence", "paragraph"}:
            raise ValueError(
                "SemanticChunker unit_level must be either "
                f"'sentence' or 'paragraph', got: {self.unit_level!r}"
            )

        self.min_chunk_size: int = int(
            min_chunk_size
            if min_chunk_size is not None
            else os.getenv(
                "SEMANTIC_CHUNKER_MIN_CHUNK_SIZE",
                str(self.DEFAULT_MIN_CHUNK_SIZE),
            )
        )

        self.device: str = self._resolve_device(
            os.getenv("SEMANTIC_CHUNKER_DEVICE", self.DEFAULT_DEVICE)
        )

        self.batch_size: int = int(
            os.getenv(
                "SEMANTIC_CHUNKER_BATCH_SIZE",
                str(self.DEFAULT_BATCH_SIZE),
            )
        )

        self.warmup_enabled: bool = self._env_bool(
            os.getenv(
                "SEMANTIC_CHUNKER_WARMUP",
                str(self.DEFAULT_WARMUP_ENABLED),
            )
        )

        logger.info(
            "SemanticChunker initialized: model=%s device=%s batch_size=%d "
            "strategy=%s unit_level=%s warmup=%s",
            self.embedding_model,
            self.device,
            self.batch_size,
            self.breakpoint_strategy,
            self.unit_level,
            self.warmup_enabled,
        )

    @staticmethod
    def _env_bool(value: str | bool | None) -> bool:

        if isinstance(value, bool):
            return value
        if value is None:
            return False
        return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}

    def _resolve_device(self, requested_device: str) -> str:

        requested = str(requested_device or "auto").strip().lower()

        try:
            import torch
        except ImportError:
            if requested not in {"auto", "cpu"}:
                logger.warning(
                    "Torch is not importable; SemanticChunker falling back to CPU."
                )
            return "cpu"

        if requested == "auto":
            if torch.cuda.is_available():
                return "cuda"
            if (
                hasattr(torch.backends, "mps")
                and torch.backends.mps.is_available()
            ):
                return "mps"
            return "cpu"

        if requested == "cuda":
            if torch.cuda.is_available():
                return "cuda"
            logger.warning(
                "SEMANTIC_CHUNKER_DEVICE=cuda was requested, but CUDA is not "
                "available. Falling back to CPU."
            )
            return "cpu"

        if requested == "mps":
            if (
                hasattr(torch.backends, "mps")
                and torch.backends.mps.is_available()
            ):
                return "mps"
            logger.warning(
                "SEMANTIC_CHUNKER_DEVICE=mps was requested, but MPS is not "
                "available. Falling back to CPU."
            )
            return "cpu"

        if requested == "cpu":
            return "cpu"

        raise ValueError(
            "SEMANTIC_CHUNKER_DEVICE must be one of "
            f"'auto', 'cuda', 'cpu', or 'mps'; got {requested_device!r}"
        )

    def _warmup_model(self, model: Any, cache_key: tuple[str, str]) -> None:

        if not self.warmup_enabled:
            return

        if cache_key in self._WARMED_UP:
            return

        warmup_texts: list[str] = [
            "Semantic chunker warmup sentence.",
            "This warmup initializes the embedding model execution path.",
        ]

        try:
            model.encode(
                warmup_texts,
                normalize_embeddings=True,
                show_progress_bar=False,
                batch_size=min(self.batch_size, len(warmup_texts)),
                convert_to_numpy=True,
            )

            if self.device == "cuda":
                try:
                    import torch
                    torch.cuda.synchronize()
                except Exception:
                    pass

            self._WARMED_UP.add(cache_key)
            logger.info(
                "SemanticChunker warmup complete: model=%s device=%s",
                self.embedding_model,
                self.device,
            )

        except Exception as exc:
            logger.warning(
                "SemanticChunker warmup failed for model=%s device=%s: %s. "
                "Continuing without warmup.",
                self.embedding_model,
                self.device,
                exc,
            )

    def chunk(self, text: str, doc_source: str = "") -> list[Chunk]:

        units: list[dict[str, Any]] = self._split_units(text)

        if not units:
            return []

        if len(units) == 1:
            return [
                self._make_chunk(
                    chunk_text=units[0]["text"],
                    chunk_units=[units[0]],
                    chunk_id=0,
                    doc_source=doc_source,
                )
            ]

        embeddings = self._embed_units([u["text"] for u in units])
        similarities = self._adjacent_similarities(embeddings)
        breakpoints, effective_threshold = self._find_breakpoints(similarities)

        chunks: list[Chunk] = []
        chunk_id: int = 0

        current_units: list[dict[str, Any]] = []
        current_len: int = 0

        def _joined_len(items: list[dict[str, Any]]) -> int:
            if not items:
                return 0
            sep_len = 1 if self.unit_level == "sentence" else 2
            return sum(len(i["text"]) for i in items) + sep_len * (len(items) - 1)

        def _emit(items: list[dict[str, Any]]) -> None:
            nonlocal chunk_id
            if not items:
                return

            chunk_text = self._join_units(items)
            chunks.append(
                self._make_chunk(
                    chunk_text=chunk_text,
                    chunk_units=items,
                    chunk_id=chunk_id,
                    doc_source=doc_source,
                    effective_threshold=effective_threshold,
                )
            )
            chunk_id += 1

        breakpoint_set: set[int] = set(breakpoints)

        for idx, unit in enumerate(units):
            unit_text = unit["text"]
            unit_len = len(unit_text)


            semantic_break_before: bool = (idx - 1) in breakpoint_set


            if unit_len > self.chunk_size:
                if current_units:
                    _emit(current_units)
                    current_units = []
                    current_len = 0

                _emit([unit])
                continue

            sep_cost = 1 if self.unit_level == "sentence" else 2
            projected_len = (
                current_len + sep_cost + unit_len
                if current_units
                else unit_len
            )

            should_split_for_size = (
                bool(current_units) and projected_len > self.chunk_size
            )

            should_split_for_semantics = (
                bool(current_units)
                and semantic_break_before
                and current_len >= self.min_chunk_size
            )

            if should_split_for_size or should_split_for_semantics:
                previous_units = current_units
                _emit(previous_units)

                overlap_units = self._compute_overlap_units(previous_units)
                current_units = list(overlap_units)
                current_len = _joined_len(current_units)

            if current_units:
                current_len += sep_cost + unit_len
            else:
                current_len = unit_len

            current_units.append(unit)

        if current_units:
            _emit(current_units)

        logger.debug(
            "SemanticChunker: %d chunks generated "
            "(strategy=%s, unit_level=%s, model=%s, size=%d, overlap=%d, "
            "threshold=%.4f, percentile=%.1f, units=%d)",
            len(chunks),
            self.breakpoint_strategy,
            self.unit_level,
            self.embedding_model,
            self.chunk_size,
            self.overlap,
            effective_threshold,
            self.breakpoint_percentile,
            len(units),
        )

        return chunks

    def _get_model(self) -> Any:

        cache_key: tuple[str, str] = (self.embedding_model, self.device)

        if cache_key in self._MODEL_CACHE:
            model = self._MODEL_CACHE[cache_key]
            self._warmup_model(model, cache_key)
            return model

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "Embedding-based SemanticChunker requires sentence-transformers. "
                "Install it or use the old paragraph-aware chunker."
            ) from exc

        logger.info(
            "Loading SemanticChunker embedding model: %s on device=%s",
            self.embedding_model,
            self.device,
        )

        model = SentenceTransformer(
            self.embedding_model,
            device=self.device,
        )

        self._MODEL_CACHE[cache_key] = model
        self._warmup_model(model, cache_key)

        return model

    def _embed_units(self, unit_texts: list[str]) -> Any:

        try:
            import numpy as np
        except ImportError as exc:
            raise ImportError(
                "Embedding-based SemanticChunker requires numpy."
            ) from exc

        model = self._get_model()

        vectors = model.encode(
            unit_texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=self.batch_size,
            convert_to_numpy=True,
        )

        return np.asarray(vectors, dtype="float32")

    def _adjacent_similarities(self, embeddings: Any) -> list[float]:

        if len(embeddings) < 2:
            return []


        similarities: list[float] = []
        for i in range(len(embeddings) - 1):
            similarities.append(float(embeddings[i] @ embeddings[i + 1]))
        return similarities

    def _find_breakpoints(
        self,
        similarities: list[float],
    ) -> tuple[list[int], float]:

        if not similarities:
            return [], self.similarity_threshold

        if self.breakpoint_strategy == "threshold":
            threshold = self.similarity_threshold
        else:
            try:
                import numpy as np
            except ImportError as exc:
                raise ImportError(
                    "Percentile semantic chunking requires numpy."
                ) from exc

            threshold = float(
                np.percentile(similarities, self.breakpoint_percentile)
            )

        breakpoints = [
            i for i, sim in enumerate(similarities)
            if sim < threshold
        ]

        return breakpoints, threshold

    def _split_units(self, text: str) -> list[dict[str, Any]]:

        paragraphs = self._split_paragraphs_with_offsets(text)

        if self.unit_level == "paragraph":
            return paragraphs

        units: list[dict[str, Any]] = []

        for para in paragraphs:
            para_text = para["text"]
            para_start = int(para["start_char"])


            if para_text.startswith("#") or len(para_text) < 80:
                units.append(para)
                continue

            local_pos = 0
            sentences = self._SENTENCE_SPLIT_PATTERN.split(para_text)

            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue

                found_at = para_text.find(sent, local_pos)
                if found_at < 0:
                    found_at = local_pos

                start = para_start + found_at
                end = start + len(sent)
                local_pos = found_at + len(sent)

                units.append({
                    "text": sent,
                    "start_char": start,
                    "end_char": end,
                })

        return units

    def _split_paragraphs_with_offsets(self, text: str) -> list[dict[str, Any]]:

        paragraphs: list[dict[str, Any]] = []


        pattern = re.compile(r"\S[\s\S]*?(?=\n\s*\n|\Z)")

        for match in pattern.finditer(text):
            raw = match.group(0)
            stripped = raw.strip()

            if not stripped:
                continue

            leading = len(raw) - len(raw.lstrip())
            start = match.start() + leading
            end = start + len(stripped)

            paragraphs.append({
                "text": stripped,
                "start_char": start,
                "end_char": end,
            })

        return paragraphs

    def _join_units(self, units: list[dict[str, Any]]) -> str:

        separator = " " if self.unit_level == "sentence" else "\n\n"
        return separator.join(u["text"].strip() for u in units if u["text"].strip()).strip()

    def _compute_overlap_units(
        self,
        units: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        if not units or self.overlap <= 0:
            return []

        overlap_units: list[dict[str, Any]] = []
        accumulated = 0

        for unit in reversed(units):
            if accumulated >= self.overlap:
                break
            overlap_units.insert(0, unit)
            accumulated += len(unit["text"])

        return overlap_units

    def _make_chunk(
        self,
        chunk_text: str,
        chunk_units: list[dict[str, Any]],
        chunk_id: int,
        doc_source: str,
        effective_threshold: float | None = None,
    ) -> Chunk:

        global_id: str = _make_global_id(doc_source, chunk_id)

        start_char = (
            int(chunk_units[0].get("start_char", 0))
            if chunk_units
            else 0
        )
        end_char = (
            int(chunk_units[-1].get("end_char", start_char + len(chunk_text)))
            if chunk_units
            else start_char + len(chunk_text)
        )

        meta: dict[str, str | int | float] = {
            "doc_source": doc_source,
            "chunk_global_id": global_id,
            "chunk_index_in_doc": chunk_id,
            "chunker_method": "semantic",
            "start_char": start_char,
            "end_char": end_char,
            "chunk_size": self.chunk_size,
            "overlap": self.overlap,


            "strategy": "embedding_semantic",
            "semantic_mode": self.breakpoint_strategy,
            "unit_level": self.unit_level,
            "embedding_model": self.embedding_model,
            "similarity_threshold": self.similarity_threshold,
            "breakpoint_percentile": self.breakpoint_percentile,
            "effective_similarity_threshold": (
                float(effective_threshold)
                if effective_threshold is not None
                else float(self.similarity_threshold)
            ),
            "units": len(chunk_units),
        }

        if len(chunk_text) > self.chunk_size:
            meta["oversized"] = 1

        return Chunk(
            text=chunk_text.strip(),
            chunk_id=chunk_id,
            doc_source=doc_source,
            metadata=meta,
            doc_id=doc_source,
            chunk_global_id=global_id,
            chunk_index_in_doc=chunk_id,
            chunker_method="semantic",
        )
