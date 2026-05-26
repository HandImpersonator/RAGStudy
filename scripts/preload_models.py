from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path


_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger: logging.Logger = logging.getLogger("preload_models")


@dataclass(frozen=True)
class ModelSpec:
    repo_id: str
    kind: str


def _canonical_repo_id(model_name: str) -> str:

    if "/" in model_name:
        return model_name

    return f"sentence-transformers/{model_name}"


try:
    from src.pipeline import RETRIEVAL_MODEL as _ACTIVE_RETRIEVAL_MODEL
    from src.pipeline import RERANKER_MODEL as _ACTIVE_RERANKER_MODEL
except Exception as exc:
    logger.warning(
        "No se pudieron leer RETRIEVAL_MODEL/RERANKER_MODEL desde src.pipeline: %s",
        exc,
    )
    _ACTIVE_RETRIEVAL_MODEL = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
    _ACTIVE_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


ACTIVE_RETRIEVAL_MODELS: list[str] = [
    _ACTIVE_RETRIEVAL_MODEL,
]

ACTIVE_RERANKER_MODELS: list[str] = [
    _ACTIVE_RERANKER_MODEL,
]

OPTIONAL_RETRIEVAL_MODELS: list[str] = [
    "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
    "BAAI/bge-base-en-v1.5",
]

OPTIONAL_RERANKER_MODELS: list[str] = [
    "cross-encoder/ms-marco-MiniLM-L-6-v2",
    "cross-encoder/ms-marco-MiniLM-L-12-v2",
    "BAAI/bge-reranker-base",
]


def _unique_ordered(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []

    for value in values:
        repo_id = _canonical_repo_id(value)
        if repo_id in seen:
            continue
        seen.add(repo_id)
        out.append(repo_id)

    return out


def build_model_plan() -> list[ModelSpec]:
    retrieval_models = _unique_ordered(
        ACTIVE_RETRIEVAL_MODELS
    )
    reranker_models = _unique_ordered(
        ACTIVE_RERANKER_MODELS
    )

    plan: list[ModelSpec] = []

    for repo_id in retrieval_models:
        plan.append(ModelSpec(repo_id=repo_id, kind="bi_encoder"))

    for repo_id in reranker_models:
        plan.append(ModelSpec(repo_id=repo_id, kind="cross_encoder"))

    return plan


def _ensure_online_mode() -> None:

    offline_vars = [
        "HF_HUB_OFFLINE",
        "TRANSFORMERS_OFFLINE",
        "HF_DATASETS_OFFLINE",
    ]

    for var in offline_vars:
        value = os.environ.get(var)
        if value and value not in {"0", "false", "False"}:
            logger.warning(
                "%s=%s estaba activo. Se desactiva para poder descargar modelos.",
                var,
                value,
            )
        os.environ[var] = "0"


def _download_snapshot(repo_id: str) -> bool:

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        logger.error(
            "huggingface_hub no está instalado. Instalar con: "
            "pip install huggingface_hub"
        )
        return False

    try:
        logger.debug("Descargando snapshot Hugging Face: %s", repo_id)
        snapshot_download(
            repo_id=repo_id,
            local_files_only=False,
            resume_download=True,
        )
        logger.info("  [OK] Snapshot OK: %s", repo_id)
        return True
    except Exception as exc:
        logger.error("  FALLO snapshot %s: %s", repo_id, exc)
        return False


def _validate_bi_encoder(repo_id: str) -> bool:

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        logger.error(
            "sentence-transformers no está instalado. Instalar con: "
            "pip install sentence-transformers"
        )
        return False

    try:
        logger.debug("Validando bi-encoder: %s", repo_id)
        SentenceTransformer(repo_id)
        logger.info("  [OK] Bi-encoder OK: %s", repo_id)
        return True
    except Exception as exc:
        logger.error("  FALLO validando bi-encoder %s: %s", repo_id, exc)
        return False


def _validate_cross_encoder(repo_id: str) -> bool:

    try:
        from sentence_transformers import CrossEncoder
    except ImportError:
        logger.error(
            "sentence-transformers no está instalado. Instalar con: "
            "pip install sentence-transformers"
        )
        return False

    try:
        logger.debug("Validando cross-encoder: %s", repo_id)
        CrossEncoder(repo_id)
        logger.info("  [OK] Cross-encoder OK: %s", repo_id)
        return True
    except Exception as exc:
        logger.error("  FALLO validando cross-encoder %s: %s", repo_id, exc)
        return False


def preload_model(spec: ModelSpec) -> bool:


    logger.debug("-" * 60)
    logger.debug("Modelo: %s", spec.repo_id)
    logger.debug("Tipo  : %s", spec.kind)

    downloaded = _download_snapshot(spec.repo_id)
    if not downloaded:
        return False

    if spec.kind == "bi_encoder":
        return _validate_bi_encoder(spec.repo_id)

    if spec.kind == "cross_encoder":
        return _validate_cross_encoder(spec.repo_id)

    logger.error("Tipo de modelo no soportado: %s", spec.kind)
    return False


def main() -> int:
    _ensure_online_mode()

    logger.info("=" * 60)
    logger.info("PRE-DESCARGA OBLIGATORIA DE TODOS LOS MODELOS - TFG RAG")
    logger.info("=" * 60)

    plan = build_model_plan()

    logger.info("Modelos planificados: %d", len(plan))
    for spec in plan:
        logger.info("  - %s [%s]", spec.repo_id, spec.kind)

    failed: list[ModelSpec] = []

    for spec in plan:
        ok = preload_model(spec)
        if not ok:
            failed.append(spec)

    logger.info("=" * 60)

    if failed:
        logger.error("Fallaron %d modelo(s):", len(failed))
        for spec in failed:
            logger.error("  - %s [%s]", spec.repo_id, spec.kind)

        logger.error("")
        logger.error("No se puede garantizar ejecución offline.")
        logger.error("Revisa conexión a Internet, proxy, VPN o acceso a huggingface.co.")
        logger.error("Vuelve a ejecutar este script antes de lanzar benchmarks.")
        logger.info("=" * 60)
        return 1

    logger.info("Todos los modelos han sido descargados y validados correctamente.")
    logger.info("Ya puedes ejecutar experimentos offline con:")
    logger.info("  export HF_HUB_OFFLINE=1")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
