from __future__ import annotations

import os
import logging
from pathlib import Path

logger: logging.Logger = logging.getLogger(__name__)


_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
_ENV_FILE: Path = _PROJECT_ROOT / "tfg.env"


_env_cache: dict[str, str] | None = None


def _load_env_file() -> dict[str, str]:

    global _env_cache

    if _env_cache is not None:

        return _env_cache

    env: dict[str, str] = {}

    if not _ENV_FILE.exists():
        logger.debug(
            "tfg.env no encontrado en %s - usando solo variables de entorno y valores por defecto",
            _ENV_FILE,
        )
        _env_cache = env
        return env

    try:
        with open(_ENV_FILE, encoding="utf-8") as fh:
            for line_num, raw_line in enumerate(fh, start=1):
                line: str = raw_line.strip()

                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    logger.warning(
                        "tfg.env línea %d: no se encontró '=', ignorando: %r",
                        line_num,
                        line[:40],
                    )
                    continue

                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                if key:
                    env[key] = value
    except OSError as e:
        logger.warning("No se pudo leer tfg.env: %s", e)

    logger.debug("Cargadas %d claves desde %s", len(env), _ENV_FILE)
    _env_cache = env
    return env


def get_config(key: str, default: str = "") -> str:


    env_value: str | None = os.environ.get(key)
    if env_value is not None:
        logger.debug("Clave '%s' resuelta desde variable de entorno", key)
        return env_value


    file_values: dict[str, str] = _load_env_file()
    if key in file_values:
        logger.debug("Clave '%s' resuelta desde tfg.env", key)
        return file_values[key]


    logger.debug("Clave '%s' no encontrada, usando valor por defecto: %r", key, default)
    return default


def get_api_key() -> str:

    return get_config("TFG_API_KEY", "tfg-rag-2026-shared-secret-change-me")


def get_server_url() -> str:

    return get_config("TFG_SERVER_URL", "http://localhost:8000")


def is_debug_mode() -> bool:

    return get_config("TFG_DEBUG_MODE", "1") == "1"


def get_auth_header_name() -> str:

    return get_config("TFG_AUTH_HEADER_NAME", "X-TFG-Auth")


def get_auth_header_prefix() -> str:

    return get_config("TFG_AUTH_HEADER_PREFIX", "TFG-RAG-2026")


def get_signature_header_name() -> str:

    return get_config("TFG_SIGNATURE_HEADER_NAME", "X-TFG-Signature")


def get_signature_prefix() -> str:

    return get_config("TFG_SIGNATURE_PREFIX", "sha256=")


def get_openai_api_key() -> str:

    return get_config("OPENAI_API_KEY", "")


def get_openai_eval_model() -> str:

    return get_config("OPENAI_EVAL_MODEL", "gpt-5.4-mini")


def get_openai_eval_sync_batch_size() -> int:

    return int(get_config("OPENAI_EVAL_SYNC_BATCH_SIZE", "10"))


def get_openai_eval_max_sync_retries() -> int:

    return int(get_config("OPENAI_EVAL_MAX_SYNC_RETRIES", "3"))


def is_openai_async_batch_fallback_enabled() -> bool:

    return get_config("OPENAI_EVAL_ASYNC_BATCH_FALLBACK", "true").lower() == "true"


def is_evaluation_enabled() -> bool:

    return bool(get_openai_api_key())
