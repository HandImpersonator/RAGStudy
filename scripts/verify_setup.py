from __future__ import annotations

import argparse
import hmac
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger: logging.Logger = logging.getLogger(__name__)


REQUIRED_MODELS: list[str] = ["llama3.2:latest", "mistral:7b", "llama3:8b"]


REQUIRED_PACKAGES: dict[str, str] = {
    "numpy": "numpy",
    "torch": "torch",
    "sentence_transformers": "sentence-transformers",
    "faiss": "faiss-cpu",
    "rank_bm25": "rank-bm25",
    "openai": "openai",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "httpx": "httpx",
    "tqdm": "tqdm",
    "matplotlib": "matplotlib",
    "scipy": "scipy",
}


OPTIONAL_PACKAGES: dict[str, str] = {
    "wikipediaapi": "wikipedia-api",
}


CORPUS_DIR: Path = Path("data/corpus")
EVAL_DIR: Path = Path("data/eval")
LOG_DIR: Path = Path("logs")
OUTPUT_DIR: Path = Path("output")
CACHE_DIR: Path = Path(".cache/rag")
ENV_FILE: Path = Path("tfg.env")


try:
    from src.config_loader import get_config as _get_config
    OLLAMA_URL: str = _get_config("TFG_SERVER_URL", "http://localhost:8000")
except Exception:
    OLLAMA_URL: str = "http://localhost:8000"


class CheckResult:


    def __init__(self, name: str, passed: bool, message: str, critical: bool = True) -> None:
        self.name: str = name
        self.passed: bool = passed
        self.message: str = message
        self.critical: bool = critical

    def __str__(self) -> str:
        status: str = "OK" if self.passed else ("FAIL" if self.critical else "WARN")
        return f"  [{status}] {self.name}: {self.message}"


def check_python_version() -> CheckResult:

    version: tuple[int, ...] = sys.version_info[:3]
    version_str: str = f"{version[0]}.{version[1]}.{version[2]}"

    if version >= (3, 10):
        return CheckResult(
            "Python version", True,
            f"{version_str} (OK, requires 3.10+)",
        )
    return CheckResult(
        "Python version", False,
        f"{version_str} (FAILED: requires 3.10+)",
    )


def check_required_packages() -> list[CheckResult]:

    results: list[CheckResult] = []

    for import_name, pip_name in REQUIRED_PACKAGES.items():
        try:
            __import__(import_name)
            results.append(CheckResult(
                f"Package: {pip_name}", True,
                "installed",
            ))
        except ImportError:
            results.append(CheckResult(
                f"Package: {pip_name}", False,
                f"NOT installed. Run: pip install {pip_name}",
            ))

    return results


def check_optional_packages() -> list[CheckResult]:

    results: list[CheckResult] = []

    for import_name, pip_name in OPTIONAL_PACKAGES.items():
        try:
            __import__(import_name)
            results.append(CheckResult(
                f"Optional: {pip_name}", True,
                "installed",
                critical=False,
            ))
        except ImportError:
            results.append(CheckResult(
                f"Optional: {pip_name}", False,
                f"not installed (optional). pip install {pip_name}",
                critical=False,
            ))

    return results


def check_ollama_running() -> CheckResult:

    url: str = f"{OLLAMA_URL}/health"
    request: Request = Request(url, method="post")

    try:
        with urlopen(request, timeout=5) as response:
            raw: bytes = response.read()
            data: dict[str, Any] = json.loads(raw.decode("utf-8"))
            models: list[dict[str, Any]] = data.get("models", [])
            return CheckResult(
                "Ollama service", True,
                f"running at {OLLAMA_URL} ({len(models)} models available)",
            )
    except URLError:
        return CheckResult(
            "Ollama service", False,
            f"NOT running at {OLLAMA_URL}. Start with: ollama serve",
        )
    except (json.JSONDecodeError, KeyError):
        return CheckResult(
            "Ollama service", False,
            f"running but returned unexpected response",
        )


def check_ollama_models() -> list[CheckResult]:

    results: list[CheckResult] = []

    url: str = f"{OLLAMA_URL}/models"
    request: Request = Request(url, method="post")

    try:
        with urlopen(request, timeout=5) as response:
            raw: bytes = response.read()
            data: dict[str, Any] = json.loads(raw.decode("utf-8"))
            available_models: set[str] = set()
            for model_info in data.get("models", []):
                name: str = model_info.get("name", "")
                available_models.add(name)

                if ":" in name:
                    available_models.add(name)
                else:
                    available_models.add(f"{name}:latest")

            for required in REQUIRED_MODELS:

                found: bool = (
                    required in available_models
                    or f"{required}:latest" in available_models
                    or any(required in m for m in available_models)
                )
                if found:
                    results.append(CheckResult(
                        f"Model: {required}", True,
                        "available",
                    ))
                else:
                    results.append(CheckResult(
                        f"Model: {required}", False,
                        f"NOT found. Run: ollama pull {required}",
                    ))

    except URLError:
        for required in REQUIRED_MODELS:
            results.append(CheckResult(
                f"Model: {required}", False,
                "cannot check (Ollama not running)",
            ))

    return results


def check_corpus() -> CheckResult:

    if not CORPUS_DIR.exists():
        return CheckResult(
            "Corpus directory", False,
            f"{CORPUS_DIR} does not exist",
        )

    files: list[Path] = list(CORPUS_DIR.glob("**/*.md")) + list(CORPUS_DIR.glob("**/*.txt"))
    if not files:
        return CheckResult(
            "Corpus directory", False,
            f"{CORPUS_DIR} exists but has no .md or .txt files",
        )

    return CheckResult(
        "Corpus directory", True,
        f"{len(files)} documents found in {CORPUS_DIR}",
    )


def check_eval_dataset() -> CheckResult:

    if not EVAL_DIR.exists():
        return CheckResult(
            "Eval datasets", False,
            f"{EVAL_DIR} does not exist",
        )

    json_files: list[Path] = list(EVAL_DIR.glob("*.json"))
    if not json_files:
        return CheckResult(
            "Eval datasets", False,
            f"{EVAL_DIR} exists but has no .json files",
        )


    sample_path: Path = EVAL_DIR / "sample_eval.json"
    if not sample_path.exists():
        return CheckResult(
            "Eval datasets", False,
            f"sample_eval.json not found in {EVAL_DIR}",
        )

    return CheckResult(
        "Eval datasets", True,
        f"{len(json_files)} dataset files found",
    )


def check_output_dirs() -> CheckResult:

    dirs_to_check: list[Path] = [LOG_DIR, OUTPUT_DIR]

    for d in dirs_to_check:
        d.mkdir(parents=True, exist_ok=True)
        test_file: Path = d / ".write_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except OSError as e:
            return CheckResult(
                "Output directories", False,
                f"Cannot write to {d}: {e}",
            )

    return CheckResult(
        "Output directories", True,
        f"{LOG_DIR} and {OUTPUT_DIR} are writable",
    )


from src.config_loader import get_api_key, get_config

_AUTH_HEADER_NAME: str = get_config("TFG_AUTH_HEADER_NAME", "X-TFG-Auth")
_AUTH_HEADER_PREFIX: str = get_config("TFG_AUTH_HEADER_PREFIX", "TFG-RAG-2026")
_SIGNATURE_HEADER_NAME: str = get_config("TFG_SIGNATURE_HEADER_NAME", "X-TFG-Signature")
_SIGNATURE_PREFIX: str = get_config("TFG_SIGNATURE_PREFIX", "sha256=")
_API_KEY: str = get_api_key()


def _signed_post(url: str, payload: dict[str, Any], timeout: int = 10) -> dict[str, Any]:

    body: bytes = json.dumps(payload).encode("utf-8")
    digest: str = hmac.new(
        key=_API_KEY.encode("utf-8"),
        msg=body,
        digestmod="sha256",
    ).hexdigest()
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        _AUTH_HEADER_NAME: f"{_AUTH_HEADER_PREFIX}:{_API_KEY}",
        _SIGNATURE_HEADER_NAME: f"{_SIGNATURE_PREFIX}{digest}",
    }
    request: Request = Request(url, data=body, headers=headers, method="POST")
    with urlopen(request, timeout=timeout) as response:
        raw: bytes = response.read()
        return json.loads(raw.decode("utf-8"))


def check_remote_server(server_url: str) -> CheckResult:

    health_url: str = f"{server_url.rstrip('/')}/health"
    try:
        data: dict[str, Any] = _signed_post(health_url, payload={}, timeout=10)
        if data.get("status") in ("ok", "degraded"):
            return CheckResult(
                f"Remote server ({server_url})", True,
                f"reachable (status={data.get('status')}, "
                f"ollama_connected={data.get('ollama_connected')})",
                critical=False,
            )
        return CheckResult(
            f"Remote server ({server_url})", False,
            f"respuesta inesperada: {data}",
            critical=False,
        )
    except URLError as e:
        return CheckResult(
            f"Remote server ({server_url})", False,
            f"not reachable: {e}",
            critical=False,
        )
    except (json.JSONDecodeError, KeyError) as e:
        return CheckResult(
            f"Remote server ({server_url})", False,
            f"respuesta inválida: {e}",
            critical=False,
        )


def check_openai_eval() -> CheckResult:


    try:
        import openai
        pkg_ok: bool = True
    except ImportError:
        return CheckResult(
            "OpenAI evaluation",
            False,
            "openai package not installed. Install: pip install 'openai>=1.60.0' "
            "(required only for Phase 2 LLM-as-judge evaluation)",
            critical=False,
        )


    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from src.config_loader import get_config
        api_key: str = get_config("OPENAI_API_KEY", "")
    except ImportError:
        api_key = os.environ.get("OPENAI_API_KEY", "")

    if not api_key:
        return CheckResult(
            "OpenAI evaluation",
            False,
            "OPENAI_API_KEY not set. Add it to tfg.env. "
            "Phase 2 LLM judge evaluation will be skipped until set.",
            critical=False,
        )


    if not (api_key.startswith("sk-") and len(api_key) > 20):
        return CheckResult(
            "OpenAI evaluation",
            False,
            f"OPENAI_API_KEY format looks invalid (got {api_key[:6]}...). "
            "Expected format: sk-...",
            critical=False,
        )


    try:
        from src.config_loader import get_config as _gc
        eval_model: str = _gc("OPENAI_EVAL_MODEL", "gpt-5.4-mini")
    except ImportError:
        eval_model = os.environ.get("OPENAI_EVAL_MODEL", "gpt-5.4-mini")

    return CheckResult(
        "OpenAI evaluation",
        True,
        f"API key set ({api_key[:6]}…), model={eval_model}. "
        "Phase 2 LLM judge evaluation is enabled.",
        critical=False,
    )


def pull_missing_models() -> None:

    url: str = f"{OLLAMA_URL}/api/tags"
    request: Request = Request(url, method="GET")

    try:
        with urlopen(request, timeout=5) as response:
            raw: bytes = response.read()
            data: dict[str, Any] = json.loads(raw.decode("utf-8"))
            available: set[str] = {
                m.get("name", "") for m in data.get("models", [])
            }
    except URLError:
        logger.error("Ollama not running. Cannot pull models.")
        return

    for model in REQUIRED_MODELS:
        if not any(model in m for m in available):
            logger.info("Pulling model: %s ...", model)
            try:
                subprocess.run(
                    ["ollama", "pull", model],
                    check=True,
                    timeout=600,
                )
                logger.info("Model %s pulled successfully", model)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logger.error("Failed to pull %s: %s", model, e)
            except subprocess.TimeoutExpired:
                logger.error("Timeout pulling %s (>600s)", model)
        else:
            logger.info("Model %s already available", model)


def run_all_checks(
    check_remote_url: str | None = None,
    skip_ollama: bool = True,
) -> tuple[list[CheckResult], bool]:

    results: list[CheckResult] = []


    results.append(check_python_version())


    results.extend(check_required_packages())


    results.extend(check_optional_packages())


    if not skip_ollama:
        results.append(check_ollama_running())
        results.extend(check_ollama_models())


    results.append(check_corpus())
    results.append(check_eval_dataset())


    results.append(check_output_dirs())


    if check_remote_url:
        results.append(check_remote_server(check_remote_url))


    results.append(check_openai_eval())


    all_critical_pass: bool = all(
        r.passed for r in results if r.critical
    )

    return results, all_critical_pass


def parse_args() -> argparse.Namespace:

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Pre-flight setup verification for TFG RAG experiments",
    )
    parser.add_argument(
        "--check-remote", type=str, default=None,
        help="Also check remote LLM server (e.g. http://servidor.uni:8000)",
    )
    parser.add_argument(
        "--pull-models", action="store_true",
        help="Download missing Ollama models",
    )
    parser.add_argument(
        "--skip-ollama", action="store_true",
        help=(
            "Skip local Ollama checks. Use this in the remote-server "
            "architecture: Ollama runs on the university server and the "
            "client only validates the FastAPI endpoint via --check-remote."
        ),
    )
    return parser.parse_args()


def main() -> int:

    args: argparse.Namespace = parse_args()

    print()
    print("=" * 60)
    print("  TFG RAG - Pre-flight Setup Verification")
    print("=" * 60)
    print()


    if args.pull_models:
        print("Pulling missing models...")
        pull_missing_models()
        print()


    results, all_pass = run_all_checks(
        check_remote_url=args.check_remote,
        skip_ollama=args.skip_ollama,
    )


    print("CHECKS:")
    print("-" * 60)
    for r in results:
        print(str(r))

    print()
    print("-" * 60)

    if all_pass:
        print("  [OK] ALL CRITICAL CHECKS PASSED")
        print("    Ready to run: python3 scripts/run_experiments.py")
    else:
        failed_critical: list[CheckResult] = [
            r for r in results if r.critical and not r.passed
        ]
        print(f"  [FAIL] {len(failed_critical)} CRITICAL CHECK(S) FAILED")
        print()
        print("  Fix these issues before running experiments:")
        for r in failed_critical:
            print(f"    {r.name}: {r.message}")

    print()
    print("=" * 60)
    print()

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
