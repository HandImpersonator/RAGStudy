from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import hmac
import logging

logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:


    text: str
    model: str
    tokens_prompt: int = 0
    tokens_generated: int = 0
    latency_ms: float = 0.0
    query_type: str = "unknown"
    model_size_gb: str = ""
    model_size_category: str = "unknown"


class BaseLLM(ABC):


    def __init__(
        self,
        model_name: str,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> None:
        self.model_name: str = model_name
        self.temperature: float = temperature
        self.max_tokens: int = max_tokens

    @abstractmethod
    def generate(self, prompt: str) -> LLMResponse:

        ...


class RemoteLLM(BaseLLM):


    REQUEST_TIMEOUT: int = 300

    def __init__(
        self,
        server_url: str = "",
        model_name: str = "remote-llm",
        temperature: float = 0.0,
        max_tokens: int = 512,
        api_key: str = "",
        query_type: str = "unknown",
    ) -> None:
        super().__init__(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )


        try:
            from src.config_loader import (
                get_api_key,
                get_server_url,
                get_auth_header_name,
                get_auth_header_prefix,
                get_signature_header_name,
                get_signature_prefix,
            )
            _default_url = get_server_url()
            _default_key = get_api_key()
            self.AUTH_HEADER_NAME: str = get_auth_header_name()
            self.AUTH_HEADER_PREFIX: str = get_auth_header_prefix()
            self.SIGNATURE_HEADER_NAME: str = get_signature_header_name()
            self.SIGNATURE_PREFIX: str = get_signature_prefix()
        except ImportError:
            import os
            _default_url = os.environ.get("TFG_SERVER_URL", "http://localhost:8000")
            _default_key = os.environ.get("TFG_API_KEY", "tfg-rag-2026-shared-secret-change-me")
            self.AUTH_HEADER_NAME = os.environ.get("TFG_AUTH_HEADER_NAME", "X-TFG-Auth")
            self.AUTH_HEADER_PREFIX = os.environ.get("TFG_AUTH_HEADER_PREFIX", "TFG-RAG-2026")
            self.SIGNATURE_HEADER_NAME = os.environ.get("TFG_SIGNATURE_HEADER_NAME", "X-TFG-Signature")
            self.SIGNATURE_PREFIX = os.environ.get("TFG_SIGNATURE_PREFIX", "sha256=")

        self.server_url: str = (server_url.rstrip("/") if server_url else _default_url)
        self.api_key: str = (api_key if api_key else _default_key)
        self.query_type: str = query_type

    def _build_auth_header(self) -> str:

        return f"{self.AUTH_HEADER_PREFIX}:{self.api_key}"

    def _sign_body(self, body: bytes) -> str:

        digest: str = hmac.new(
            key=self.api_key.encode("utf-8"),
            msg=body,
            digestmod="sha256",
        ).hexdigest()
        return f"{self.SIGNATURE_PREFIX}{digest}"

    def generate(self, prompt: str) -> LLMResponse:

        url: str = f"{self.server_url}/generate"

        payload: dict[str, object] = {
            "prompt": prompt,


            "temperature": self.temperature,
            "max_tokens": self.max_tokens,

            "query_type": self.query_type,
        }

        body: bytes = json.dumps(payload).encode("utf-8")


        payload_signature: str = self._sign_body(body)

        request: Request = Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",

                self.AUTH_HEADER_NAME: self._build_auth_header(),

                self.SIGNATURE_HEADER_NAME: payload_signature,
            },
            method="POST",
        )

        start_time: float = time.perf_counter()

        try:
            with urlopen(request, timeout=self.REQUEST_TIMEOUT) as response:
                raw: bytes = response.read()
                data: dict = json.loads(raw.decode("utf-8"))
        except HTTPError as e:
            try:
                error_body: str = e.read().decode("utf-8")
            except Exception:
                error_body = "(could not read error body)"

            if e.code == 400:

                logger.error(
                    "Servidor rechazó la petición (HTTP 400). "
                    "Verifica que la API key coincide con TFG_API_KEY en servidor. "
                    "Detalle local: %s",
                    error_body,
                )
                raise RuntimeError(
                    f"El servidor en {self.server_url} rechazó la petición. "
                    f"Verifica la API key y la configuración del servidor."
                ) from e
            elif e.code == 503:
                logger.error("Ollama no disponible en servidor remoto (HTTP 503): %s", error_body)
                raise RuntimeError(
                    f"El servidor ({self.server_url}) está activo pero Ollama no responde. "
                    f"Asegúrate de que 'ollama serve' está ejecutándose en el servidor."
                ) from e
            else:
                logger.error("Servidor HTTP %d: %s", e.code, error_body)
                raise RuntimeError(
                    f"El servidor devolvió HTTP {e.code}. Consulta los logs del servidor."
                ) from e
        except TimeoutError as e:


            raise TimeoutError(
                f"El servidor ({self.server_url}) no respondió en {self.REQUEST_TIMEOUT}s. "
                f"El modelo puede estar cargando o el prompt es demasiado largo. "
                f"Considera reducir top_k o aumentar REQUEST_TIMEOUT."
            ) from e
        except URLError as e:
            raise ConnectionError(
                f"No se pudo conectar al servidor remoto en {self.server_url}. "
                f"¿Está activo el SSH tunnel? Error: {e}"
            ) from e

        elapsed_ms: float = (time.perf_counter() - start_time) * 1000


        generated_text: str = data.get("text", "").strip()
        tokens_prompt: int = data.get("tokens_prompt", 0)
        tokens_generated: int = data.get("tokens_generated", 0)
        server_latency: float = data.get("latency_ms", 0.0)


        configured_model: str = data.get("model", self.model_name)
        actual_model: str = data.get("actual_model", configured_model)


        if actual_model != configured_model:
            logger.warning(
                "Discrepancia de modelo en servidor: configurado=%s, en memoria=%s. "
                "El log usará el modelo detectado: %s",
                configured_model, actual_model, actual_model,
            )

        model_size_gb: str = data.get("model_size_gb", "")
        model_size_category: str = data.get("model_size_category", "unknown")
        echoed_query_type: str = data.get("query_type", self.query_type)

        logger.info(
            "RemoteLLM [configurado=%s / actual=%s / query_type=%s @ %s]: "
            "%d prompt tokens, %d generated tokens, "
            "%.0f ms total (%.0f ms server-side)",
            configured_model,
            actual_model,
            echoed_query_type,
            self.server_url,
            tokens_prompt,
            tokens_generated,
            elapsed_ms,
            server_latency,
        )

        return LLMResponse(
            text=generated_text,
            model=actual_model,
            tokens_prompt=tokens_prompt,
            tokens_generated=tokens_generated,
            latency_ms=elapsed_ms,
            query_type=echoed_query_type,
            model_size_gb=model_size_gb,
            model_size_category=model_size_category,
        )
