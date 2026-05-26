from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from pathlib import Path
from typing import Any

_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))


_SEP = "─" * 72
_BOLD = "\033[1m"
_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"
_RESET = "\033[0m"


def _c(colour: str, text: str) -> str:

    if sys.stdout.isatty():
        return f"{colour}{text}{_RESET}"
    return text


def _wrap(text: str, width: int = 70, indent: str = "  ") -> str:
    return textwrap.fill(text, width=width, initial_indent=indent,
                         subsequent_indent=indent)


def _score_colour(val: float) -> str:
    if val >= 70:
        return _GREEN
    if val >= 40:
        return _YELLOW
    return _RED


def display_sample(
    sample: dict[str, Any],
    index: int,
    show_prompt: bool = False,
) -> None:


    ev: dict[str, Any] = sample.get("eval", {})
    scores: dict[str, float] = ev.get("scores") or {}
    notes: dict[str, Any] = ev.get("judge_notes") or {}
    status: str = ev.get("status", "pending")

    print()
    print(_c(_BOLD, f"{'=' * 72}"))
    print(_c(_BOLD, f"  SAMPLE {index}  -  {sample.get('eval_item_id', 'unknown')}"))
    print(_c(_BOLD, f"{'=' * 72}"))


    print(_c(_CYAN, "\n  QUESTION"))
    print(_wrap(sample.get("question", "-")))


    print(_c(_CYAN, "\n  GROUND TRUTH"))
    print(f"  {sample.get('ground_truth', '-')}")


    print(_c(_CYAN, "\n  PIPELINE"))
    print(f"  retriever={sample.get('retriever_type','?')}  "
          f"chunker={sample.get('chunker','?')}  "
          f"reranker={sample.get('reranker','none')}  "
          f"prompt={sample.get('prompt_version','?')}")
    print(f"  chunks_retrieved={sample.get('num_chunks_retrieved','?')}  "
          f"chunks_final={sample.get('num_chunks_final','?')}  "
          f"context_chars={sample.get('context_chars_total','?')}")


    contexts: list[str] = sample.get("contexts", [])
    sources: list[dict] = sample.get("context_sources", [])
    print(_c(_CYAN, f"\n  RETRIEVED CONTEXT  ({len(contexts)} chunks)"))
    for i, ctx in enumerate(contexts):
        src_label = ""
        if i < len(sources):
            src = sources[i]
            rr_score = src.get("reranker_score", src.get("retrieval_score", ""))
            src_label = f" [{src.get('source_file','').replace('hotpotqa_','').replace('.md','')}  score={rr_score:.3f}]" \
                if isinstance(rr_score, float) else \
                f" [{src.get('source_file','').replace('hotpotqa_','').replace('.md','')}]"
        preview = ctx[:200].replace("\n", " ")
        if len(ctx) > 200:
            preview += "…"
        print(f"  [S{i+1}]{src_label}")
        print(f"  {preview}")
        print()


    print(_c(_CYAN, "  LLM ANSWER"))
    timings: dict = sample.get("timings_ms", {})
    gen_s = timings.get("llm_generation", 0) / 1000
    print(_wrap(sample.get("answer", "-")))
    print(f"  [{sample.get('model','?')}  gen={gen_s:.1f}s  "
          f"tokens_prompt={sample.get('tokens_prompt','?')}  "
          f"tokens_gen={sample.get('tokens_generated','?')}]")


    print(_c(_CYAN, "\n  EVALUATION"))
    print(f"  status={status}  "
          f"model={ev.get('model','?')}  "
          f"evaluated_at={ev.get('evaluated_at','?')}")

    if scores:
        score_parts = []
        for k, label in [
            ("correctness", "Correctness"),
            ("faithfulness", "Faithfulness"),
            ("context_support", "CtxSupport"),
            ("answer_relevance", "Relevance"),
            ("overall", "Overall"),
        ]:
            v = scores.get(k)
            if v is not None:
                score_parts.append(
                    f"{label}={_c(_score_colour(v), f'{v:.0f}')}"
                )
        print("  " + "  ".join(score_parts))
    else:
        print("  (no scores - evaluation pending or failed)")


    if notes:
        print(_c(_CYAN, "\n  JUDGE NOTES"))
        flags = []
        if notes.get("has_contradiction"):
            flags.append(_c(_RED, "CONTRADICTION"))
        if notes.get("is_false_refusal"):
            flags.append(_c(_RED, "FALSE_REFUSAL"))
        if notes.get("is_correct_refusal"):
            flags.append(_c(_GREEN, "CORRECT_REFUSAL"))
        if flags:
            print("  flags: " + "  ".join(flags))

        atype = notes.get("answer_type", "")
        if atype:
            print(f"  answer_type={atype}")


        failure_type = notes.get("failure_type")
        if failure_type:
            colour = _RED if failure_type != "none" else _GREEN
            print(f"  failure_type={_c(colour, failure_type)}")
        if "answer_correct" in notes:
            ac = notes["answer_correct"]
            print(f"  answer_correct={_c(_GREEN if ac else _RED, str(ac))}"
                  f"  context_sufficient={notes.get('context_sufficient','?')}"
                  f"  answer_supported={notes.get('answer_supported_by_context','?')}")
        judge_summary = notes.get("judge_summary", "")
        if judge_summary:
            print(_c(_CYAN, "\n  JUDGE SUMMARY"))
            print(_wrap(judge_summary))
        evidence = notes.get("evidence_quotes", [])
        if evidence:
            print(_c(_CYAN, "\n  EVIDENCE QUOTES"))
            for q in evidence:
                print(_wrap(f'"{q}"'))


    if show_prompt:
        print(_c(_CYAN, "\n  RECONSTRUCTED JUDGE PROMPT"))
        print(_SEP)
        try:
            from src.prompts import build_user_prompt
            prompt = build_user_prompt([sample])
            print(prompt)
        except Exception as exc:
            print(f"  (could not reconstruct prompt: {exc})")
        print(_SEP)

    print()


def re_judge_sample(sample: dict[str, Any]) -> None:

    try:
        from src.config_loader import get_config as _get_config
        api_key: str = _get_config("OPENAI_API_KEY", "")
    except ImportError:
        api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print(_c(_RED, "  OPENAI_API_KEY not set in env or tfg.env - cannot re-judge."))
        return

    try:
        from src.prompts import build_user_prompt, SYSTEM_PROMPT
        from src.evaluation.schemas import RAG_EVAL_BATCH_SCHEMA
        from openai import OpenAI
    except ImportError as exc:
        print(f"  Import error: {exc}")
        return

    client = OpenAI(api_key=api_key)
    model = os.environ.get("OPENAI_EVAL_MODEL", "gpt-4o-mini")

    prompt_text = build_user_prompt([sample])

    print(_c(_CYAN, f"\n  RE-JUDGING with {model}…"))
    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt_text},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": RAG_EVAL_BATCH_SCHEMA["name"],
                    "strict": True,
                    "schema": RAG_EVAL_BATCH_SCHEMA["schema"],
                }
            },
            temperature=0,
            store=False,
        )
        raw: str = response.output_text
        parsed: dict[str, Any] = json.loads(raw)
        print(_c(_CYAN, "  RAW JUDGE RESPONSE (structured JSON):"))
        print(json.dumps(parsed, indent=2))
    except Exception as exc:
        print(f"  {_c(_RED, 'Judge call failed')}: {exc}")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Inspect evaluated RAG samples from an experiment JSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("experiment_json", type=Path,
                   help="Path to experiments/<config>.json")
    p.add_argument("--sample", "-s", type=int, default=0,
                   help="Sample index to inspect (default: 0)")
    p.add_argument("--all", "-a", action="store_true",
                   help="Inspect all samples in the file")
    p.add_argument("--show-prompt", "-p", action="store_true",
                   help="Print the reconstructed judge prompt")
    p.add_argument("--re-judge", action="store_true",
                   help="Re-run the judge on the selected sample (needs OPENAI_API_KEY)")
    p.add_argument("--list", "-l", action="store_true",
                   help="List all samples with one-line summary and exit")
    return p.parse_args()


def main() -> int:
    args = _parse_args()

    if not args.experiment_json.exists():
        print(f"File not found: {args.experiment_json}", file=sys.stderr)
        return 1

    data: dict[str, Any] = json.loads(args.experiment_json.read_text())
    samples: list[dict[str, Any]] = data.get("samples", [])

    if not samples:
        print("No samples in this file.")
        return 0

    config_name: str = data.get("config_name", args.experiment_json.stem)
    n_eval: int = sum(
        1 for s in samples if s.get("eval", {}).get("status") == "completed"
    )
    print(f"\n{_c(_BOLD, config_name)}  -  {len(samples)} samples, {n_eval} evaluated")


    if args.list:
        print()
        for i, s in enumerate(samples):
            ev = s.get("eval", {})
            scores = ev.get("scores") or {}
            overall = scores.get("overall")
            corr = scores.get("correctness")
            status = ev.get("status", "pending")
            notes = ev.get("judge_notes") or {}
            contradict = "CONTRADICTION" if notes.get("has_contradiction") else ""
            q_short = s.get("question", "")[:60]
            gt = s.get("ground_truth", "")[:20]
            score_str = (
                f"overall={overall:.0f} correctness={corr:.0f}"
                if overall is not None else status
            )
            print(f"  [{i}] {q_short:<62}  GT={gt:<22}  {score_str}  {contradict}")
        return 0


    indices: list[int] = list(range(len(samples))) if args.all else [args.sample]

    for idx in indices:
        if idx < 0 or idx >= len(samples):
            print(f"Sample index {idx} out of range (0-{len(samples)-1}).",
                  file=sys.stderr)
            continue
        display_sample(samples[idx], idx, show_prompt=args.show_prompt)
        if args.re_judge and not args.all:
            re_judge_sample(samples[idx])

    return 0


if __name__ == "__main__":
    sys.exit(main())
