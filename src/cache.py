from __future__ import annotations

import hashlib
import json
import logging
import pickle
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from numpy.typing import NDArray

logger: logging.Logger = logging.getLogger(__name__)


_HASH_LEN: int = 16


def _h(data: str | bytes) -> str:

    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:_HASH_LEN]


def _hash_dict(payload: dict[str, Any]) -> str:

    return _h(json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str))


def _hash_file(path: Path, chunk_size: int = 1 << 20) -> str:

    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            blk = fh.read(chunk_size)
            if not blk:
                break
            h.update(blk)
    return h.hexdigest()[:_HASH_LEN]


def query_id_for(question: str) -> str:

    return _h(question.strip())


def query_set_key(query_ids: Iterable[str]) -> str:

    return _h("\n".join(sorted(set(query_ids))))


class CacheManager:


    STAGES: tuple[str, ...] = (
        "ingestion",
        "chunks",
        "embeddings",
        "indexes",
        "retrieval",
        "reranking",
        "contexts",
    )


    _DEFAULT_MAX_ENTRIES: dict[str, int] = {
        "ingestion":  8,
        "chunks":     12,
        "embeddings": 16,
        "indexes":    32,
        "retrieval":  128,
        "reranking":  128,
        "contexts":   128,
    }

    def __init__(
        self,
        cache_dir: Path,
        refresh: bool = False,
        max_entries: dict[str, int] | None = None,
    ) -> None:
        self.cache_dir: Path = Path(cache_dir)
        self.refresh: bool = refresh

        self._max_entries: dict[str, int] = dict(self._DEFAULT_MAX_ENTRIES)
        if max_entries:
            self._max_entries.update(max_entries)
        for stage in self.STAGES:
            (self.cache_dir / stage).mkdir(parents=True, exist_ok=True)


    def stage_dir(self, stage: str, key: str) -> Path:

        if stage not in self.STAGES:
            raise ValueError(f"Unknown cache stage: {stage}")
        d: Path = self.cache_dir / stage / key
        d.mkdir(parents=True, exist_ok=True)
        return d

    def has(self, stage: str, key: str, required_files: list[str]) -> bool:

        if self.refresh:
            return False
        d: Path = self.cache_dir / stage / key
        if not d.is_dir():
            return False
        for f in ("manifest.json", *required_files):
            if not (d / f).exists():
                return False
        return True

    def _evict_old_entries(self, stage: str, current_key: str) -> None:

        cap: int = self._max_entries.get(stage, 8)
        stage_root: Path = self.cache_dir / stage


        entries: list[Path] = [
            p for p in stage_root.iterdir() if p.is_dir()
        ]
        if len(entries) <= cap:
            return

        def _mtime(p: Path) -> float:
            manifest: Path = p / "manifest.json"
            if manifest.exists():
                return manifest.stat().st_mtime

            return 0.0


        entries.sort(key=lambda p: (p.name == current_key, _mtime(p)))

        to_delete: list[Path] = entries[: len(entries) - cap]
        for entry in to_delete:
            if entry.name == current_key:

                continue
            try:
                shutil.rmtree(entry)
                logger.info(
                    "CACHE_EVICT stage=%s key=%s (cap=%d)",
                    stage, entry.name, cap,
                )
            except OSError as exc:
                logger.warning(
                    "CACHE_EVICT failed for %s: %s", entry, exc,
                )

    def _write_manifest(self, stage: str, key: str, manifest: dict[str, Any]) -> None:
        d: Path = self.stage_dir(stage, key)
        manifest = dict(manifest)
        manifest.setdefault("stage", stage)
        manifest.setdefault("key", key)
        (d / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False)
        )

        self._evict_old_entries(stage, key)

    def _read_manifest(self, stage: str, key: str) -> dict[str, Any]:
        return json.loads((self.cache_dir / stage / key / "manifest.json").read_text())

    def _validate_manifest(
        self, stage: str, key: str, expected: dict[str, Any]
    ) -> bool:

        try:
            got: dict[str, Any] = self._read_manifest(stage, key)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("CACHE corrupt manifest %s/%s: %s", stage, key, e)
            return False
        for k, v in expected.items():
            if got.get(k) != v:
                logger.warning(
                    "CACHE manifest mismatch %s/%s key=%r expected=%r got=%r",
                    stage, key, k, v, got.get(k),
                )
                return False
        return True


    @staticmethod
    def key_ingestion(
        corpus_dir: Path,
        file_paths: list[Path],
        file_hashes: list[str],
    ) -> str:
        payload: dict[str, Any] = {
            "corpus_dir": str(corpus_dir),
            "files": [
                {"path": str(p.relative_to(corpus_dir)), "sha256": h}
                for p, h in sorted(zip(file_paths, file_hashes), key=lambda x: str(x[0]))
            ],
        }
        return _hash_dict(payload)

    @staticmethod
    def key_chunks(ingestion_key: str, chunker: str, size: int, overlap: int) -> str:
        return _hash_dict({
            "ingestion": ingestion_key,
            "chunker": chunker,
            "chunk_size": size,
            "chunk_overlap": overlap,
        })

    @staticmethod
    def key_embeddings(
        chunks_key: str,
        model_name: str,
        dim: int | None = None,
        dtype: str = "float32",
    ) -> str:
        return _hash_dict({
            "chunks": chunks_key,
            "model": model_name,
            "dim": dim,
            "dtype": dtype,
        })

    @staticmethod
    def key_index(
        chunks_key: str,
        retriever: str,
        embeddings_key: str | None,
    ) -> str:
        return _hash_dict({
            "chunks": chunks_key,
            "retriever": retriever,
            "embeddings": embeddings_key,
        })

    @staticmethod
    def key_retrieval(
        index_key: str,
        top_k: int,
        retrieval_model: str,
        query_set_hash: str,
    ) -> str:
        return _hash_dict({
            "index": index_key,
            "top_k": top_k,
            "retrieval_model": retrieval_model,
            "query_set": query_set_hash,
        })

    @staticmethod
    def key_reranking(
        retrieval_key: str,
        reranker_model: str,
        top_n: int,
        query_set_hash: str,
    ) -> str:
        return _hash_dict({
            "retrieval": retrieval_key,
            "reranker_model": reranker_model,
            "top_n": top_n,
            "query_set": query_set_hash,
        })

    @staticmethod
    def key_contexts(
        reranking_key: str,
        config_name: str,
        context_mode: str,
        token_budget: int,
        neighbor_expansion: bool,
        query_set_hash: str,
    ) -> str:
        return _hash_dict({
            "reranking": reranking_key,
            "config": config_name,
            "context_mode": context_mode,
            "token_budget": token_budget,
            "neighbor_expansion": neighbor_expansion,
            "query_set": query_set_hash,
        })


    def save_ingestion(
        self,
        key: str,
        documents: list[Any],
        corpus_dir: Path,
        file_paths: list[Path],
        file_hashes: list[str],
    ) -> None:
        d: Path = self.stage_dir("ingestion", key)
        with (d / "documents.jsonl").open("w", encoding="utf-8") as fh:
            for doc in documents:
                fh.write(json.dumps({
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "source_path": str(doc.source_path) if doc.source_path else None,
                }, ensure_ascii=False) + "\n")
        self._write_manifest("ingestion", key, {
            "corpus_dir": str(corpus_dir),
            "n_documents": len(documents),
            "files": [
                {"path": str(p.relative_to(corpus_dir)), "sha256": h}
                for p, h in zip(file_paths, file_hashes)
            ],
        })
        logger.info("CACHE_SAVE ingestion key=%s n_docs=%d", key, len(documents))

    def load_ingestion(self, key: str) -> list[dict[str, Any]]:
        d: Path = self.cache_dir / "ingestion" / key
        out: list[dict[str, Any]] = []
        with (d / "documents.jsonl").open(encoding="utf-8") as fh:
            for line in fh:
                out.append(json.loads(line))
        logger.info("CACHE_HIT ingestion key=%s n_docs=%d", key, len(out))
        return out


    def save_chunks(self, key: str, chunks: list[Any], manifest: dict[str, Any]) -> None:
        d: Path = self.stage_dir("chunks", key)
        with (d / "chunks.jsonl").open("w", encoding="utf-8") as fh:
            for c in chunks:
                fh.write(json.dumps(asdict(c), ensure_ascii=False, default=str) + "\n")
        manifest = dict(manifest)
        manifest["n_chunks"] = len(chunks)
        self._write_manifest("chunks", key, manifest)
        logger.info("CACHE_SAVE chunks key=%s n_chunks=%d", key, len(chunks))

    def load_chunks_raw(self, key: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        path: Path = self.cache_dir / "chunks" / key / "chunks.jsonl"
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                out.append(json.loads(line))
        logger.info("CACHE_HIT chunks key=%s n_chunks=%d", key, len(out))
        return out


    def save_embeddings(
        self,
        key: str,
        embeddings: NDArray[np.float32],
        chunk_ids: list[str],
        manifest: dict[str, Any],
    ) -> None:
        d: Path = self.stage_dir("embeddings", key)
        np.save(d / "embeddings.npy", embeddings, allow_pickle=False)
        (d / "chunk_ids.json").write_text(json.dumps(chunk_ids))
        manifest = dict(manifest)
        manifest.update({
            "n_vectors": int(embeddings.shape[0]),
            "dim": int(embeddings.shape[1]) if embeddings.ndim == 2 else None,
            "dtype": str(embeddings.dtype),
        })
        self._write_manifest("embeddings", key, manifest)
        logger.info(
            "CACHE_SAVE embeddings key=%s shape=%s", key, embeddings.shape,
        )

    def load_embeddings(self, key: str) -> tuple[NDArray[np.float32], list[str]]:
        d: Path = self.cache_dir / "embeddings" / key
        emb: NDArray[np.float32] = np.load(d / "embeddings.npy", allow_pickle=False)
        chunk_ids: list[str] = json.loads((d / "chunk_ids.json").read_text())
        logger.info("CACHE_HIT embeddings key=%s shape=%s", key, emb.shape)
        return emb, chunk_ids


    def save_index(self, key: str, retriever: Any, manifest: dict[str, Any]) -> None:
        d: Path = self.stage_dir("indexes", key)

        if hasattr(retriever, "save") and callable(retriever.save):
            try:
                retriever.save(d)
                self._write_manifest("indexes", key, {**manifest, "backend": "native"})
                logger.info("CACHE_SAVE index key=%s backend=native", key)
                return
            except Exception as e:
                logger.warning("Native index save failed (%s); falling back to pickle.", e)
        with (d / "retriever.pkl").open("wb") as fh:
            pickle.dump(retriever, fh, protocol=pickle.HIGHEST_PROTOCOL)
        self._write_manifest("indexes", key, {**manifest, "backend": "pickle"})
        logger.info("CACHE_SAVE index key=%s backend=pickle", key)

    def load_index(self, key: str, retriever: Any) -> bool:

        d: Path = self.cache_dir / "indexes" / key
        try:
            manifest: dict[str, Any] = self._read_manifest("indexes", key)
        except (OSError, json.JSONDecodeError):
            return False
        backend: str = manifest.get("backend", "native")
        try:
            if backend == "native" and hasattr(retriever, "load"):
                ok: bool = bool(retriever.load(d))
                if ok:
                    logger.info("CACHE_HIT index key=%s backend=native", key)
                return ok
            pkl: Path = d / "retriever.pkl"
            if not pkl.exists():
                return False
            with pkl.open("rb") as fh:
                loaded: Any = pickle.load(fh)

            retriever.__dict__.update(loaded.__dict__)
            logger.info("CACHE_HIT index key=%s backend=pickle", key)
            return True
        except Exception as e:
            logger.warning("CACHE index load failed for %s: %s", key, e)
            return False


    def _jsonl_path(self, stage: str, key: str, filename: str) -> Path:
        return self.stage_dir(stage, key) / filename


    _TIMINGS_FILENAME: str = "timings.json"

    def save_stage_timings(
        self,
        stage: str,
        key: str,
        per_query: dict[str, dict[str, float | None]],
        config: dict[str, Any] | None = None,
    ) -> None:

        if not per_query:
            return

        totals: dict[str, float] = {}
        for q_metrics in per_query.values():
            for k, v in q_metrics.items():
                if not k.endswith("_ms") or v is None:
                    continue
                totals[k] = totals.get(k, 0.0) + float(v)
        payload: dict[str, Any] = {
            "stage":               stage,
            "n_queries":           len(per_query),
            "config":              dict(config or {}),
            "elapsed_ms_per_query": per_query,
            "elapsed_ms_total":    totals,
        }
        path: Path = self.stage_dir(stage, key) / self._TIMINGS_FILENAME
        path.write_text(
            json.dumps(payload, ensure_ascii=False, default=str, indent=2),
            encoding="utf-8",
        )
        logger.info(
            "CACHE_SAVE timings stage=%s key=%s n_queries=%d", stage, key,
            len(per_query),
        )

    def load_stage_timings(
        self, stage: str, key: str,
    ) -> dict[str, dict[str, float | None]]:

        path: Path = self.cache_dir / stage / key / self._TIMINGS_FILENAME
        if not path.exists():
            return {}
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Malformed timings.json at %s: %s", path, exc)
            return {}
        out = obj.get("elapsed_ms_per_query")
        return out if isinstance(out, dict) else {}

    def save_retrieval(
        self,
        key: str,
        rows: dict[str, list[dict[str, Any]]],
        manifest: dict[str, Any],
        timings: dict[str, dict[str, float | None]] | None = None,
    ) -> None:

        path: Path = self._jsonl_path("retrieval", key, "retrieved_top_k.jsonl")
        with path.open("w", encoding="utf-8") as fh:
            for qid, results in rows.items():
                fh.write(json.dumps({"query_id": qid, "results": results},
                                    ensure_ascii=False, default=str) + "\n")
        self._write_manifest("retrieval", key,
                             {**manifest, "n_queries": len(rows)})
        logger.info("CACHE_SAVE retrieval key=%s n_queries=%d", key, len(rows))
        if timings:
            self.save_stage_timings("retrieval", key, timings, config=manifest)

    def load_retrieval(self, key: str) -> dict[str, list[dict[str, Any]]]:
        out: dict[str, list[dict[str, Any]]] = {}
        path: Path = self.cache_dir / "retrieval" / key / "retrieved_top_k.jsonl"
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                obj = json.loads(line)
                out[obj["query_id"]] = obj["results"]
        logger.info("CACHE_HIT retrieval key=%s n_queries=%d", key, len(out))
        return out

    def save_reranking(
        self,
        key: str,
        rows: dict[str, list[dict[str, Any]]],
        manifest: dict[str, Any],
        timings: dict[str, dict[str, float | None]] | None = None,
    ) -> None:

        path: Path = self._jsonl_path("reranking", key, "reranked_top_n.jsonl")
        with path.open("w", encoding="utf-8") as fh:
            for qid, results in rows.items():
                fh.write(json.dumps({"query_id": qid, "results": results},
                                    ensure_ascii=False, default=str) + "\n")
        self._write_manifest("reranking", key,
                             {**manifest, "n_queries": len(rows)})
        logger.info("CACHE_SAVE reranking key=%s n_queries=%d", key, len(rows))
        if timings:
            self.save_stage_timings("reranking", key, timings, config=manifest)

    def load_reranking(self, key: str) -> dict[str, list[dict[str, Any]]]:
        out: dict[str, list[dict[str, Any]]] = {}
        path: Path = self.cache_dir / "reranking" / key / "reranked_top_n.jsonl"
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                obj = json.loads(line)
                out[obj["query_id"]] = obj["results"]
        logger.info("CACHE_HIT reranking key=%s n_queries=%d", key, len(out))
        return out

    def save_contexts(
        self,
        key: str,
        rows: dict[str, dict[str, Any]],
        manifest: dict[str, Any],
        timings: dict[str, dict[str, float | None]] | None = None,
    ) -> None:

        path: Path = self._jsonl_path("contexts", key, "contexts.jsonl")
        with path.open("w", encoding="utf-8") as fh:
            for qid, payload in rows.items():
                rec = {"query_id": qid, **payload}
                fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
        self._write_manifest("contexts", key,
                             {**manifest, "n_queries": len(rows)})
        logger.info("CACHE_SAVE contexts key=%s n_queries=%d", key, len(rows))
        if timings:
            self.save_stage_timings("contexts", key, timings, config=manifest)

    def load_contexts(self, key: str) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        path: Path = self.cache_dir / "contexts" / key / "contexts.jsonl"
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                obj = json.loads(line)
                qid: str = obj.pop("query_id")
                out[qid] = obj
        logger.info("CACHE_HIT contexts key=%s n_queries=%d", key, len(out))
        return out


    def clear(self, stage: str | None = None) -> None:

        targets: list[str] = [stage] if stage else list(self.STAGES)
        for st in targets:
            d: Path = self.cache_dir / st
            if d.exists():
                shutil.rmtree(d)
                d.mkdir(parents=True, exist_ok=True)
                logger.info("CACHE_CLEAR stage=%s", st)


__all__ = [
    "CacheManager",
    "query_id_for",
    "query_set_key",
]
