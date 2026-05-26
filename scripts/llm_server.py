from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger: logging.Logger = logging.getLogger(__name__)


import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.config_loader import (
        get_api_key,
        is_debug_mode,
        get_auth_header_name,
        get_auth_header_prefix,
        get_signature_header_name,
        get_signature_prefix,
    )
    _CONFIG_LOADER_AVAILABLE: bool = True
except ImportError:

    _CONFIG_LOADER_AVAILABLE = False
    logger.warning(
        "src/config_loader not found - falling back to environment variables only"
    )


OLLAMA_URL: str = "http://localhost:11434"


OLLAMA_TIMEOUT: int = 300


SERVER_HOST: str = "127.0.0.1"
SERVER_PORT: int = 8000


MODEL_CATALOGUE: dict[str, dict[str, Any]] = {

    "llama3.2:latest": {
        "size_gb":    "1.9",
        "category":   "small",


        "num_ctx":    4096,
        "chunk_size": 512,
        "top_k":      3,
    },
    "mistral:7b": {
        "size_gb":    "4.1",
        "category":   "medium",
        "num_ctx":    8192,
        "chunk_size": 1024,
        "top_k":      5,
    },
    "llama3:8b": {
        "size_gb":    "4.3",
        "category":   "medium",
        "num_ctx":    8192,
        "chunk_size": 1024,
        "top_k":      5,
    },
}


DEFAULT_MODEL_PARAMS: dict[str, Any] = {
    "size_gb":    "?",
    "category":   "unknown",
    "num_ctx":    4096,
    "chunk_size": 512,
    "top_k":      3,
}


NO_MODEL_NAME: str = "unknown"


def resolve_active_model() -> tuple[str, dict[str, Any]]:

    detected: str | None = ollama_get_running_model()
    if detected is None:
        return NO_MODEL_NAME, DEFAULT_MODEL_PARAMS
    params: dict[str, Any] = MODEL_CATALOGUE.get(detected, DEFAULT_MODEL_PARAMS)
    return detected, params


import hmac
import os


AUTH_HEADER_NAME: str = get_auth_header_name() if _CONFIG_LOADER_AVAILABLE else os.environ.get("TFG_AUTH_HEADER_NAME", "X-TFG-Auth")


AUTH_HEADER_PREFIX: str = get_auth_header_prefix() if _CONFIG_LOADER_AVAILABLE else os.environ.get("TFG_AUTH_HEADER_PREFIX", "TFG-RAG-2026")


if _CONFIG_LOADER_AVAILABLE:
    API_KEY: str = get_api_key()
else:

    API_KEY = os.environ.get("TFG_API_KEY", "tfg-rag-2026-shared-secret-change-me")


AUTH_ENABLED: bool = True


SIGNATURE_HEADER_NAME: str = get_signature_header_name() if _CONFIG_LOADER_AVAILABLE else os.environ.get("TFG_SIGNATURE_HEADER_NAME", "X-TFG-Signature")


SIGNATURE_PREFIX: str = get_signature_prefix() if _CONFIG_LOADER_AVAILABLE else os.environ.get("TFG_SIGNATURE_PREFIX", "sha256=")


DEBUG_MODE: bool = is_debug_mode() if _CONFIG_LOADER_AVAILABLE else (
    os.environ.get("TFG_DEBUG_MODE", "1") == "1"
)


@dataclass
class GenerationResult:


    text: str
    model: str
    tokens_prompt: int = 0
    tokens_generated: int = 0
    latency_ms: float = 0.0


def ollama_generate(
    prompt: str,
    model: str,
    num_ctx: int,
    temperature: float = 0.0,
    max_tokens: int = 512,
) -> GenerationResult:

    url: str = f"{OLLAMA_URL}/api/generate"


    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
            "num_ctx": num_ctx,
        },
    }

    body: bytes = json.dumps(payload).encode("utf-8")
    request: Request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    start_time: float = time.perf_counter()

    try:
        with urlopen(request, timeout=OLLAMA_TIMEOUT) as response:
            raw: bytes = response.read()
            data: dict[str, Any] = json.loads(raw.decode("utf-8"))
    except URLError as e:
        raise ConnectionError(
            f"Cannot connect to Ollama at {OLLAMA_URL}. "
            f"Is 'ollama serve' running? Error: {e}"
        ) from e

    elapsed_ms: float = (time.perf_counter() - start_time) * 1000

    return GenerationResult(
        text=data.get("response", "").strip(),
        model=model,
        tokens_prompt=data.get("prompt_eval_count", 0),
        tokens_generated=data.get("eval_count", 0),
        latency_ms=elapsed_ms,
    )


def ollama_list_models() -> list[dict[str, Any]]:

    url: str = f"{OLLAMA_URL}/models"
    request: Request = Request(url, method="post")

    try:
        with urlopen(request, timeout=10) as response:
            raw: bytes = response.read()
            data: dict[str, Any] = json.loads(raw.decode("utf-8"))
    except URLError as e:
        raise ConnectionError(
            f"Cannot connect to Ollama at {OLLAMA_URL}: {e}"
        ) from e

    return data.get("models", [])


def ollama_get_running_model() -> str | None:

    import subprocess

    try:

        proc: subprocess.CompletedProcess = subprocess.run(
            ["ollama", "ps"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as e:

        logger.debug("ollama ps no disponible: %s", e)
        return None

    if proc.returncode != 0:
        logger.debug("ollama ps retornó código %d: %s", proc.returncode, proc.stderr.strip())
        return None


    lines: list[str] = proc.stdout.strip().splitlines()

    for line in lines[1:]:
        stripped: str = line.strip()
        if not stripped:
            continue

        parts: list[str] = stripped.split()
        if parts:
            model_name: str = parts[0]
            logger.debug("ollama ps: modelo activo detectado = %s", model_name)
            return model_name


    logger.debug("ollama ps: no hay modelos cargados actualmente")
    return None


try:
    from fastapi import FastAPI, HTTPException, Request as FastAPIRequest, Depends, Header
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
except ImportError:
    logger.error(
        "FastAPI not installed. Install with: pip install fastapi uvicorn"
    )
    sys.exit(1)


_GENERIC_ERROR: str = "Malformed request."


def _reject(reason: str) -> None:


    logger.warning("Request rejected: %s", reason)

    if DEBUG_MODE:

        raise HTTPException(status_code=400, detail=f"[DEBUG] {reason}")
    else:

        raise HTTPException(status_code=400, detail=_GENERIC_ERROR)


def _compute_hmac_signature(body: bytes) -> str:


    digest: str = hmac.new(
        key=API_KEY.encode("utf-8"),
        msg=body,
        digestmod="sha256",
    ).hexdigest()

    return f"{SIGNATURE_PREFIX}{digest}"


async def verify_request_header(
    request: FastAPIRequest,
) -> str:

    if not AUTH_ENABLED:

        logger.debug("Auth check skipped (AUTH_ENABLED=False)")
        return "auth-disabled"


    raw_value: str | None = request.headers.get(AUTH_HEADER_NAME.lower())
    if raw_value is None:
        _reject(
            f"Missing required header '{AUTH_HEADER_NAME}'. "
            f"Expected format: {AUTH_HEADER_NAME}: {AUTH_HEADER_PREFIX}:<key>"
        )


    expected_prefix: str = f"{AUTH_HEADER_PREFIX}:"
    if not raw_value.startswith(expected_prefix):
        _reject(
            f"Header '{AUTH_HEADER_NAME}' has wrong format. "
            f"Value must start with '{expected_prefix}'"
        )


    provided_key: str = raw_value[len(expected_prefix):]
    if not hmac.compare_digest(
        provided_key.encode("utf-8"),
        API_KEY.encode("utf-8"),
    ):
        _reject("API key in X-TFG-Auth header does not match configured key")


    raw_sig: str | None = request.headers.get(SIGNATURE_HEADER_NAME.lower())
    if raw_sig is None:
        _reject(
            f"Missing required header '{SIGNATURE_HEADER_NAME}'. "
            f"Expected format: {SIGNATURE_HEADER_NAME}: {SIGNATURE_PREFIX}<hex_digest>"
        )


    if not raw_sig.startswith(SIGNATURE_PREFIX):
        _reject(
            f"Header '{SIGNATURE_HEADER_NAME}' must start with '{SIGNATURE_PREFIX}'. "
            f"Only SHA-256 signatures are accepted."
        )


    raw_body: bytes = await request.body()


    expected_sig: str = _compute_hmac_signature(raw_body)


    if not hmac.compare_digest(
        raw_sig.encode("utf-8"),
        expected_sig.encode("utf-8"),
    ):
        _reject(
            "HMAC-SHA256 payload signature mismatch. "
            "The request body was modified in transit, "
            "or the client used a different shared secret."
        )

    logger.debug(
        "Request auth OK: key_prefix=%s... sig_prefix=%s...",
        provided_key[:4],
        raw_sig[7:15],
    )


    return provided_key


class GenerateRequest(BaseModel):

    prompt: str
    temperature: float = 0.0
    max_tokens: int = 512


    query_type: str = "unknown"


class GenerateResponse(BaseModel):

    text: str
    model: str
    actual_model: str
    model_size_gb: str
    model_size_category: str
    query_type: str
    tokens_prompt: int = 0
    tokens_generated: int = 0
    latency_ms: float = 0.0


class HealthResponse(BaseModel):

    status: str
    ollama_connected: bool
    ollama_url: str


class ModelInfo(BaseModel):

    name: str
    size: str = ""
    modified_at: str = ""


class ModelsResponse(BaseModel):

    models: list[ModelInfo]


class ActiveModelResponse(BaseModel):


    model: str


    actual_model: str

    model_size_gb: str

    model_size_category: str

    num_ctx: int

    recommended_chunk_size: int

    recommended_top_k: int


app: FastAPI = FastAPI(
    title="RAG - LLM Server",
    description=(
        "Remote LLM inference server for the RAG pipeline. "
        "Wraps Ollama and exposes generation via REST API."
    ),
    version="1.0.0",
)


@app.post("/generate", response_model=GenerateResponse)
async def generate_endpoint(
    request: GenerateRequest,
    _key: str = Depends(verify_request_header),
) -> GenerateResponse:


    active_name: str
    params: dict[str, Any]
    active_name, params = resolve_active_model()

    logger.info(
        "Generate request: model=%s (%s, %s GB) query_type=%s "
        "prompt_len=%d temp=%.1f max_tokens=%d",
        active_name,
        params["category"],
        params["size_gb"],
        request.query_type,
        len(request.prompt),
        request.temperature,
        request.max_tokens,
    )

    if active_name == NO_MODEL_NAME:
        logger.warning(
            "No hay ningún modelo cargado en Ollama (ollama ps vacío). "
            "Se intentará la generación pero podría fallar o cargar un "
            "modelo por defecto del servidor."
        )

    try:
        result: GenerationResult = ollama_generate(
            prompt=request.prompt,
            model=active_name,
            num_ctx=params["num_ctx"],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
    except ConnectionError as e:
        logger.error("Ollama connection error: %s", e)
        if DEBUG_MODE:
            raise HTTPException(status_code=503, detail=f"[DEBUG] Ollama not available: {e}") from e
        else:
            raise HTTPException(status_code=503, detail="Service temporarily unavailable.") from e
    except RuntimeError as e:
        logger.error("Generation error: %s", e)
        if DEBUG_MODE:
            raise HTTPException(status_code=500, detail=f"[DEBUG] Generation failed: {e}") from e
        else:
            raise HTTPException(status_code=500, detail="Internal error.") from e

    logger.info(
        "Generated [model=%s / query_type=%s]: "
        "%d prompt tokens, %d generated tokens, %.0f ms",
        active_name,
        request.query_type,
        result.tokens_prompt,
        result.tokens_generated,
        result.latency_ms,
    )

    return GenerateResponse(
        text=result.text,
        model=active_name,
        actual_model=active_name,
        model_size_gb=params["size_gb"],
        model_size_category=params["category"],
        query_type=request.query_type,
        tokens_prompt=result.tokens_prompt,
        tokens_generated=result.tokens_generated,
        latency_ms=result.latency_ms,
    )


@app.post("/health", response_model=HealthResponse)
async def health_endpoint(
    _key: str = Depends(verify_request_header),
) -> HealthResponse:

    ollama_ok: bool = False
    try:
        ollama_list_models()
        ollama_ok = True
    except ConnectionError:
        pass

    return HealthResponse(
        status="ok" if ollama_ok else "degraded",
        ollama_connected=ollama_ok,
        ollama_url=OLLAMA_URL,
    )


@app.post("/models", response_model=ModelsResponse)
async def models_endpoint(
    _key: str = Depends(verify_request_header),
) -> ModelsResponse:

    try:
        models_data: list[dict[str, Any]] = ollama_list_models()
    except ConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot list models: {e}",
        ) from e

    models: list[ModelInfo] = []
    for m in models_data:
        name: str = m.get("name", "unknown")
        size_bytes: int = m.get("size", 0)
        size_str: str = f"{size_bytes / (1024**3):.1f} GB" if size_bytes else ""
        models.append(ModelInfo(
            name=name,
            size=size_str,
            modified_at=m.get("modified_at", ""),
        ))

    return ModelsResponse(models=models)


@app.post("/active-model", response_model=ActiveModelResponse)
async def active_model_endpoint(
    _key: str = Depends(verify_request_header),
) -> ActiveModelResponse:


    active_name: str
    params: dict[str, Any]
    active_name, params = resolve_active_model()

    if active_name == NO_MODEL_NAME:
        logger.warning(
            "Preflight /active-model: ollama ps no reporta ningún modelo cargado. "
            "Devolviendo parámetros por defecto."
        )

    logger.info(
        "Preflight /active-model: model=%s num_ctx=%d chunk=%d top_k=%d",
        active_name,
        params["num_ctx"],
        params["chunk_size"],
        params["top_k"],
    )

    return ActiveModelResponse(
        model=active_name,
        actual_model=active_name,
        model_size_gb=params["size_gb"],
        model_size_category=params["category"],
        num_ctx=params["num_ctx"],
        recommended_chunk_size=params["chunk_size"],
        recommended_top_k=params["top_k"],
    )


def parse_args() -> argparse.Namespace:

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="FastAPI LLM Server for TFG RAG Pipeline",
    )
    parser.add_argument(
        "--no-auth",
        action="store_true",
        help="Disable API key authentication. Only for local-only debugging.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (detailed error messages in HTTP responses).",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable uvicorn auto-reload (development only).",
    )
    return parser.parse_args()


def main() -> int:

    args: argparse.Namespace = parse_args()


    global AUTH_ENABLED, DEBUG_MODE
    if args.no_auth:
        AUTH_ENABLED = False
        logger.warning("Authentication DISABLED (--no-auth flag). Do NOT use in production.")
    if args.debug:
        DEBUG_MODE = True
        logger.info("Debug mode ENABLED via --debug flag.")


    startup_name: str
    startup_params: dict[str, Any]
    startup_name, startup_params = resolve_active_model()

    logger.info("=" * 60)
    logger.info("TFG RAG - LLM SERVER")
    logger.info("=" * 60)
    logger.info("Host:           %s", SERVER_HOST)
    logger.info("Port:           %d", SERVER_PORT)
    logger.info("Ollama URL:     %s", OLLAMA_URL)
    logger.info("Active model:   %s  (auto-detected via 'ollama ps')", startup_name)
    logger.info("Model size:     %s GB  (%s)", startup_params["size_gb"], startup_params["category"])
    logger.info("Auth:           %s", "ENABLED" if AUTH_ENABLED else "DISABLED")
    logger.info("Debug mode:     %s", "ON" if DEBUG_MODE else "OFF (generic errors)")
    logger.info("Config source:  %s", "tfg.env / env vars" if _CONFIG_LOADER_AVAILABLE else "env vars only")
    logger.info("Auth header:    %s: %s:<key>", AUTH_HEADER_NAME, AUTH_HEADER_PREFIX)
    logger.info("Sig header:     %s: sha256=<hmac_hex>", SIGNATURE_HEADER_NAME)
    logger.info("Key prefix:     %s...", API_KEY[:8])
    logger.info("Docs:           http://%s:%d/docs  (local only)", SERVER_HOST, SERVER_PORT)

    try:
        import uvicorn
        uvicorn.run(


            app if not args.reload else "scripts.llm_server:app",
            host=SERVER_HOST,
            port=SERVER_PORT,
            reload=args.reload,
            log_level="info",
        )
    except ImportError:
        logger.error("uvicorn not installed. Install: pip install uvicorn")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
