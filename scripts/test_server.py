from __future__ import annotations


import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.config_loader import get_api_key, get_server_url
    _CORRECT_API_KEY_DEFAULT: str = get_api_key()
    _SERVER_URL_DEFAULT: str = get_server_url()
except ImportError:
    _CORRECT_API_KEY_DEFAULT = os.environ.get(
        "TFG_API_KEY", "tfg-rag-2026-shared-secret-change-me"
    )
    _SERVER_URL_DEFAULT = os.environ.get("TFG_SERVER_URL", "http://localhost:8000")


TEST_SERVER_URL: str = _SERVER_URL_DEFAULT


CORRECT_API_KEY: str = _CORRECT_API_KEY_DEFAULT


AUTH_HEADER_NAME: str = "X-TFG-Auth"


AUTH_HEADER_PREFIX: str = "TFG-RAG-2026"


SIGNATURE_HEADER_NAME: str = "X-TFG-Signature"


SIGNATURE_PREFIX: str = "sha256="


TEST_PROMPT: str = "Responde en una frase: ¿Qué es RAG?"


REQUEST_TIMEOUT: int = 60


import json
import sys
import time
import hmac
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


GREEN: str = "\033[92m"
RED: str = "\033[91m"
YELLOW: str = "\033[93m"
CYAN: str = "\033[96m"
RESET: str = "\033[0m"
BOLD: str = "\033[1m"


def ok(msg: str) -> None:

    print(f"  {GREEN}[PASS]{RESET}  {msg}")


def fail(msg: str) -> None:

    print(f"  {RED}[FAIL]{RESET}  {msg}")


def info(msg: str) -> None:

    print(f"  {CYAN}→{RESET}      {msg}")


def header(msg: str) -> None:

    print(f"\n{BOLD}{YELLOW}{msg}{RESET}")


def http_get(url: str, timeout: int = REQUEST_TIMEOUT) -> tuple[int, dict]:

    req: Request = Request(url, method="GET")
    try:
        with urlopen(req, timeout=timeout) as resp:

            raw: bytes = resp.read()
            body: dict = json.loads(raw.decode("utf-8"))
            return resp.status, body
    except HTTPError as e:

        try:
            body = json.loads(e.read().decode("utf-8"))
        except Exception:
            body = {"detail": str(e)}
        return e.code, body
    except URLError as e:

        return 0, {"error": str(e)}


def http_post(
    url: str,
    payload: dict,
    extra_headers: dict[str, str] | None = None,
    timeout: int = REQUEST_TIMEOUT,
    body_bytes: bytes | None = None,
) -> tuple[int, dict, bytes]:


    actual_bytes: bytes = body_bytes if body_bytes is not None else json.dumps(payload).encode("utf-8")


    all_headers: dict[str, str] = {"Content-Type": "application/json"}
    if extra_headers:
        all_headers.update(extra_headers)

    req: Request = Request(url, data=actual_bytes, headers=all_headers, method="POST")

    try:
        with urlopen(req, timeout=timeout) as resp:
            raw: bytes = resp.read()
            body: dict = json.loads(raw.decode("utf-8"))
            return resp.status, body, actual_bytes
    except HTTPError as e:

        try:
            body = json.loads(e.read().decode("utf-8"))
        except Exception:
            body = {"detail": str(e)}
        return e.code, body, actual_bytes
    except URLError as e:
        return 0, {"error": str(e)}, actual_bytes


def make_auth_header(api_key: str) -> dict[str, str]:

    return {AUTH_HEADER_NAME: f"{AUTH_HEADER_PREFIX}:{api_key}"}


def _sign_body(api_key: str, body: bytes) -> str:


    digest: str = hmac.new(
        key=api_key.encode("utf-8"),
        msg=body,
        digestmod="sha256",
    ).hexdigest()
    return f"{SIGNATURE_PREFIX}{digest}"


def make_full_headers(api_key: str, body: bytes) -> dict[str, str]:

    return {
        AUTH_HEADER_NAME: f"{AUTH_HEADER_PREFIX}:{api_key}",
        SIGNATURE_HEADER_NAME: _sign_body(api_key, body),
    }


def test_health(base_url: str) -> bool:

    header("Test 1: POST /health  (auth required)")
    url: str = f"{base_url}/health"


    payload: dict = {}
    payload_bytes: bytes = b"{}"
    headers: dict[str, str] = make_full_headers(CORRECT_API_KEY, payload_bytes)

    status, body, _ = http_post(url, payload, extra_headers=headers, body_bytes=payload_bytes)

    if status == 0:
        fail(f"Server unreachable: {body.get('error', 'unknown')}")
        print(f"  {YELLOW}Check that the server is running at {base_url}{RESET}")
        print(f"  {YELLOW}If the server is remote, open the SSH forward tunnel from the server first:{RESET}")
        print(f"  {YELLOW}  ssh -L 8000:127.0.0.1:8000 -o ServerAliveInterval=60 \\{RESET}")
        print(f"  {YELLOW}      -o ServerAliveCountMax=10 usuario@host.cliente -p 22{RESET}")
        return False

    if status == 200:
        ollama_ok: bool = body.get("ollama_connected", False)
        info(f"HTTP {status} - status={body.get('status')} ollama_connected={ollama_ok}")
        if not ollama_ok:
            print(f"  {YELLOW}[WARN] Ollama not connected - /generate tests will return 503{RESET}")
        ok("Health endpoint reachable")
        return True
    else:
        fail(f"Unexpected HTTP {status}: {body}")
        return False


def test_models(base_url: str) -> bool:

    header("Test 2: POST /models  (auth required)")
    url: str = f"{base_url}/models"


    payload: dict = {}
    payload_bytes: bytes = b"{}"
    headers: dict[str, str] = make_full_headers(CORRECT_API_KEY, payload_bytes)

    status, body, _ = http_post(url, payload, extra_headers=headers, body_bytes=payload_bytes)

    if status == 0:
        fail(f"Server unreachable: {body.get('error', 'unknown')}")
        return False

    if status == 200:
        models: list = body.get("models", [])
        info(f"HTTP {status} - {len(models)} model(s) available")
        for m in models:
            info(f"  model={m.get('name')} size={m.get('size')}")
        ok("Models endpoint reachable")
        return True
    elif status == 503:
        info(f"HTTP {status} - Ollama unavailable (expected if Ollama not running)")
        ok("Server responded correctly (503 = Ollama down, not server down)")
        return True
    else:
        fail(f"Unexpected HTTP {status}: {body}")
        return False


def test_generate_correct_auth(base_url: str) -> bool:

    header("Test 3: POST /generate - correct auth header  [CONNECTIVITY TEST]")
    url: str = f"{base_url}/generate"


    payload: dict = {
        "prompt": TEST_PROMPT,
        "temperature": 0.0,
        "max_tokens": 64,
        "query_type": "test",
    }


    payload_bytes: bytes = json.dumps(payload).encode("utf-8")


    headers: dict[str, str] = make_full_headers(CORRECT_API_KEY, payload_bytes)
    info(f"Sending header: {AUTH_HEADER_NAME}: {headers[AUTH_HEADER_NAME]}")
    info(f"Sending header: {SIGNATURE_HEADER_NAME}: {headers[SIGNATURE_HEADER_NAME][:40]}...")
    info(f"Payload max_tokens=64 (model selected by server)")

    t0: float = time.perf_counter()

    status, body, _ = http_post(url, payload, extra_headers=headers, body_bytes=payload_bytes)
    elapsed_ms: float = (time.perf_counter() - t0) * 1000

    if status == 0:
        fail(f"Server unreachable: {body.get('error', 'unknown')}")
        return False

    if status == 200:
        answer: str = body.get("text", "")[:80]


        actual_model: str = body.get("actual_model") or body.get("model", "unknown")
        size_gb: str = body.get("model_size_gb", "?")
        category: str = body.get("model_size_category", "?")
        info(f"HTTP {status} ({elapsed_ms:.0f} ms) - answer preview: {answer!r}")
        info(f"Modelo activo (ollama ps): {actual_model}  ({category}, {size_gb} GB)")
        ok("Auth accepted, generation returned 200 - server is working correctly")
        return True
    elif status == 503:
        info(f"HTTP {status} - Ollama not available on server side (expected if Ollama not running)")
        ok("Auth accepted (503 = Ollama problem, not auth problem)")
        return True
    else:

        fail(f"HTTP {status}: {body.get('detail', body)}")
        return False


def test_generate_wrong_key(base_url: str) -> bool:

    header("Test 4: POST /generate - wrong API key (should be rejected)")
    url: str = f"{base_url}/generate"

    payload: dict = {
        "prompt": TEST_PROMPT,
        "temperature": 0.0,
        "max_tokens": 16,
        "query_type": "test",
    }
    payload_bytes: bytes = json.dumps(payload).encode("utf-8")


    wrong_key: str = "this-is-the-wrong-key-000000000000"
    bad_headers: dict[str, str] = make_full_headers(wrong_key, payload_bytes)
    info(f"Sending header: {AUTH_HEADER_NAME}: {bad_headers[AUTH_HEADER_NAME]}")
    info(f"Sending header: {SIGNATURE_HEADER_NAME}: {bad_headers[SIGNATURE_HEADER_NAME][:40]}...")

    status, body, _ = http_post(url, payload, extra_headers=bad_headers, body_bytes=payload_bytes)

    if status in (400, 403):

        info(f"HTTP {status} - detail: {body.get('detail', '(no detail)')}")
        ok(f"Correctly rejected wrong key with HTTP {status}")
        return True
    elif status == 200:
        fail("Server accepted a WRONG API key - auth is broken!")
        return False
    else:
        fail(f"Unexpected HTTP {status}: {body}")
        return False


def test_generate_missing_header(base_url: str) -> bool:

    header("Test 5: POST /generate - missing auth header")
    url: str = f"{base_url}/generate"

    payload: dict = {
        "prompt": TEST_PROMPT,
        "temperature": 0.0,
        "max_tokens": 16,
        "query_type": "test",
    }

    info("Sending NO auth header at all")


    status, body, _ = http_post(url, payload, extra_headers=None)

    if status in (400, 403):
        info(f"HTTP {status} - detail: {body.get('detail', '(no detail)')}")
        ok(f"Correctly rejected missing header with HTTP {status}")
        return True
    elif status == 200:
        fail("Server accepted request with NO auth header - auth is broken!")
        return False
    else:
        fail(f"Unexpected HTTP {status}: {body}")
        return False


def test_generate_malformed_header_value(base_url: str) -> bool:

    header("Test 6: POST /generate - correct header name, wrong value format")
    url: str = f"{base_url}/generate"

    payload: dict = {
        "prompt": TEST_PROMPT,
        "temperature": 0.0,
        "max_tokens": 16,
        "query_type": "test",
    }


    bad_format: dict[str, str] = {AUTH_HEADER_NAME: CORRECT_API_KEY}
    info(f"Sending: {AUTH_HEADER_NAME}: {CORRECT_API_KEY[:20]}... (no prefix)")

    status, body, _ = http_post(url, payload, extra_headers=bad_format)

    if status in (400, 403):
        info(f"HTTP {status} - detail: {body.get('detail', '(no detail)')}")
        ok(f"Correctly rejected malformed header value with HTTP {status}")
        return True
    elif status == 200:
        fail("Server accepted malformed header format - format validation is broken!")
        return False
    else:
        fail(f"Unexpected HTTP {status}: {body}")
        return False


def test_generate_wrong_header_name(base_url: str) -> bool:

    header("Test 7: POST /generate - wrong header name (old X-API-Key format)")
    url: str = f"{base_url}/generate"

    payload: dict = {
        "prompt": TEST_PROMPT,
        "temperature": 0.0,
        "max_tokens": 16,
        "query_type": "test",
    }


    old_style: dict[str, str] = {"X-API-Key": CORRECT_API_KEY}
    info(f"Sending: X-API-Key: {CORRECT_API_KEY[:20]}... (wrong header name)")

    status, body, _ = http_post(url, payload, extra_headers=old_style)

    if status in (400, 403):
        info(f"HTTP {status} - detail: {body.get('detail', '(no detail)')}")
        ok(f"Correctly rejected wrong header name with HTTP {status}")
        return True
    elif status == 200:
        fail("Server accepted request with wrong header name - header validation broken!")
        return False
    else:
        fail(f"Unexpected HTTP {status}: {body}")
        return False


def test_generate_missing_signature(base_url: str) -> bool:

    header("Test 8: POST /generate - missing X-TFG-Signature header")
    url: str = f"{base_url}/generate"

    payload: dict = {
        "prompt": TEST_PROMPT,
        "temperature": 0.0,
        "max_tokens": 16,
        "query_type": "test",
    }
    payload_bytes: bytes = json.dumps(payload).encode("utf-8")


    auth_only: dict[str, str] = make_auth_header(CORRECT_API_KEY)
    info(f"Sending ONLY: {AUTH_HEADER_NAME}: {auth_only[AUTH_HEADER_NAME]}")
    info(f"NOT sending: {SIGNATURE_HEADER_NAME}")

    status, body, _ = http_post(url, payload, extra_headers=auth_only, body_bytes=payload_bytes)

    if status in (400, 403):
        info(f"HTTP {status} - detail: {body.get('detail', '(no detail)')}")
        ok(f"Correctly rejected missing signature header with HTTP {status}")
        return True
    elif status == 200:
        fail("Server accepted request with NO signature header - HMAC check is broken!")
        return False
    else:
        fail(f"Unexpected HTTP {status}: {body}")
        return False


def test_generate_tampered_payload(base_url: str) -> bool:

    header("Test 9: POST /generate - tampered payload (HMAC mismatch)")
    url: str = f"{base_url}/generate"


    original_payload: dict = {
        "prompt": TEST_PROMPT,
        "temperature": 0.0,
        "max_tokens": 16,
        "query_type": "test",
    }
    original_bytes: bytes = json.dumps(original_payload).encode("utf-8")


    tampered_payload: dict = {
        "prompt": TEST_PROMPT,
        "temperature": 0.0,
        "max_tokens": 9999,
        "query_type": "test",
    }
    tampered_bytes: bytes = json.dumps(tampered_payload).encode("utf-8")


    headers: dict[str, str] = make_full_headers(CORRECT_API_KEY, original_bytes)
    info(f"Signed bytes (original):  max_tokens=16")
    info(f"Sending bytes (tampered): max_tokens=9999")
    info(f"Signature was computed for the original body - should mismatch on server")


    status, body, _ = http_post(url, tampered_payload, extra_headers=headers, body_bytes=tampered_bytes)

    if status in (400, 403):
        info(f"HTTP {status} - detail: {body.get('detail', '(no detail)')}")
        ok(f"Correctly rejected tampered payload with HTTP {status}")
        return True
    elif status == 200:
        fail("Server accepted a TAMPERED payload - HMAC verification is broken!")
        return False
    else:
        fail(f"Unexpected HTTP {status}: {body}")
        return False


def main() -> int:

    import argparse


    global CORRECT_API_KEY


    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="FastAPI server test suite for TFG RAG",
    )
    parser.add_argument(
        "--url",
        type=str,
        default=TEST_SERVER_URL,
        help=f"Server base URL (default: {TEST_SERVER_URL})",
    )

    parser.add_argument(
        "--key",
        type=str,
        default=CORRECT_API_KEY,
        help="Correct API key to use in auth tests",
    )
    parser.add_argument(
        "--skip-generate",
        action="store_true",
        help="Skip /generate tests (only test /health and /models)",
    )
    args: argparse.Namespace = parser.parse_args()

    base_url: str = args.url.rstrip("/")

    print()
    print(f"{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}  TFG RAG - FastAPI Server Test Suite{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")
    print(f"  Target:       {base_url}")
    print(f"  Auth header:  {AUTH_HEADER_NAME}: {AUTH_HEADER_PREFIX}:<key>")
    print(f"  Sig header:   {SIGNATURE_HEADER_NAME}: sha256=<hmac_hex>")
    print(f"  Key used:     {args.key[:16]}... ({len(args.key)} chars)")
    print()


    CORRECT_API_KEY = args.key


    results: list[tuple[str, bool]] = []


    results.append(("POST /health (auth)", test_health(base_url)))
    results.append(("POST /models (auth)", test_models(base_url)))


    if not args.skip_generate:
        results.append(("POST /generate correct auth", test_generate_correct_auth(base_url)))
        results.append(("POST /generate wrong key",    test_generate_wrong_key(base_url)))
        results.append(("POST /generate missing header", test_generate_missing_header(base_url)))
        results.append(("POST /generate malformed value", test_generate_malformed_header_value(base_url)))
        results.append(("POST /generate wrong header name", test_generate_wrong_header_name(base_url)))
        results.append(("POST /generate missing signature", test_generate_missing_signature(base_url)))
        results.append(("POST /generate tampered payload", test_generate_tampered_payload(base_url)))


    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}  Summary{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")

    passed: int = 0
    failed_tests: list[str] = []

    for test_name, result in results:
        symbol: str = f"{GREEN}[OK]{RESET}" if result else f"{RED}[FAIL]{RESET}"
        status_str: str = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {symbol} {test_name:<40} {status_str}")
        if result:
            passed += 1
        else:
            failed_tests.append(test_name)

    print()
    print(f"  Results: {passed}/{len(results)} tests passed")

    if failed_tests:
        print(f"\n  {RED}Failed tests:{RESET}")
        for t in failed_tests:
            print(f"    - {t}")
        print()
        return 1

    print(f"\n  {GREEN}All tests passed.{RESET}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
