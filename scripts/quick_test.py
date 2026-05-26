from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger: logging.Logger = logging.getLogger(__name__)


DEFAULT_QUERY: str = "¿Qué es Retrieval-Augmented Generation y cómo reduce las alucinaciones?"
CORPUS_DIR: Path = Path("data/corpus")


def test_config(
    config_option: int,
    query: str,
) -> tuple[bool, str, float, str]:

    from src.pipeline import RAGPipeline, PipelineResult

    start: float = time.perf_counter()

    try:
        pipeline: RAGPipeline = RAGPipeline(config_option=config_option)

        if pipeline.config_name != "no_rag":
            num_chunks: int = pipeline.build_index(corpus_dir=CORPUS_DIR)
            logger.info("  Indexed %d chunks", num_chunks)

        result: PipelineResult = pipeline.run(query=query)
        elapsed_ms: float = (time.perf_counter() - start) * 1000


        answer: str = result.answer.strip()
        if not answer:
            return False, "", elapsed_ms, "Empty answer received"

        if "dry-run" in answer.lower() or "simulada" in answer.lower():
            return False, answer[:150], elapsed_ms, "Got dry-run stub answer (real LLM not connected)"


        if elapsed_ms < 50 and pipeline.config_name != "no_rag":
            return False, answer[:150], elapsed_ms, f"Suspiciously fast ({elapsed_ms:.0f}ms), likely not a real LLM"

        return True, answer[:200], elapsed_ms, ""

    except ConnectionError as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return False, "", elapsed_ms, f"Connection error: {e}"
    except ImportError as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return False, "", elapsed_ms, f"Missing dependency: {e}"
    except (RuntimeError, FileNotFoundError) as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return False, "", elapsed_ms, f"Runtime error: {e}"


def parse_args() -> argparse.Namespace:

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Quick single-query test for each pipeline configuration",
    )
    parser.add_argument(
        "--configs", nargs="+", type=int, default=[3, 1, 2],
        choices=[1, 2, 3, 4, 5],
        help="Configs to test (default: 3 1 2 = no_rag, baseline, optimized)",
    )
    parser.add_argument(
        "--query", type=str, default=DEFAULT_QUERY,
        help="Test query to use",
    )
    return parser.parse_args()


def main() -> int:

    args: argparse.Namespace = parse_args()

    from src.pipeline import RAGPipeline

    print()
    print("=" * 70)
    print("  TFG RAG - Quick Test (single query per config)")
    print("=" * 70)
    print(f"  Query: {args.query[:80]}...")
    print()

    all_pass: bool = True
    results_summary: list[tuple[str, bool, str, float, str]] = []

    for config_option in args.configs:
        config_name: str = RAGPipeline.CONFIG_MAP.get(config_option, f"config_{config_option}")
        print(f"  Testing [{config_option}] {config_name}...")

        success, answer_preview, latency_ms, error_msg = test_config(
            config_option=config_option,
            query=args.query,
        )

        results_summary.append((config_name, success, answer_preview, latency_ms, error_msg))

        if success:
            print(f"    [PASS] ({latency_ms:.0f} ms)")
            print(f"    Answer: {answer_preview}...")
        else:
            print(f"    [FAIL] ({latency_ms:.0f} ms)")
            print(f"    Error: {error_msg}")
            all_pass = False

        print()


    print("-" * 70)
    print(f"  {'Config':<20} {'Status':<10} {'Latency':<15}")
    print("-" * 70)
    for name, success, _, latency, _ in results_summary:
        status: str = "PASS" if success else "FAIL"
        print(f"  {name:<20} {status:<10} {latency:.0f} ms")

    print()
    if all_pass:
        print("  [PASS] ALL TESTS PASSED - Ready for full experiments")
        print("    Run: python3 scripts/run_experiments.py")
    else:
        print("  [FAIL] SOME TESTS FAILED")
        print("    Fix issues above, then retry.")
        print("    Check: python3 scripts/verify_setup.py")

    print("=" * 70)
    print()

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
