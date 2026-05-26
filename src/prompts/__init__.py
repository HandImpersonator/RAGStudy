from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class SourceInfo:


    source_id: str = ""
    chunk_global_id: str = ""
    doc_id: str = ""
    source_file: str = ""
    chunk_index_in_doc: int = -1
    chunker_method: str = ""
    retrieval_score: float = 0.0
    retrieval_score_type: str = ""
    reranker_score: float | None = None
    reranker_score_type: str = ""
    start_char: int | None = None
    end_char: int | None = None
    text_chars: int = 0
    text_preview: str = ""

    def to_dict(self) -> dict:

        return {
            "source_id": self.source_id,
            "chunk_global_id": self.chunk_global_id,
            "doc_id": self.doc_id,
            "source_file": self.source_file,
            "chunk_index_in_doc": self.chunk_index_in_doc,
            "chunker_method": self.chunker_method,
            "retrieval_score": round(self.retrieval_score, 6),
            "retrieval_score_type": self.retrieval_score_type,
            "reranker_score": (
                round(self.reranker_score, 6)
                if self.reranker_score is not None else None
            ),
            "reranker_score_type": self.reranker_score_type,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "text_chars": self.text_chars,
            "text_preview": self.text_preview,
        }


def source_info_from_result(
    result: object,
    source_id: str,
) -> SourceInfo:

    text: str = getattr(result, "text", "")
    meta: dict = getattr(result, "metadata", {}) or {}
    return SourceInfo(
        source_id=source_id,
        chunk_global_id=getattr(result, "chunk_global_id", ""),
        doc_id=getattr(result, "doc_id", ""),
        source_file=getattr(result, "source_file", ""),
        chunk_index_in_doc=getattr(result, "chunk_index_in_doc", -1),
        chunker_method=str(meta.get("chunker_method", "")),
        retrieval_score=float(getattr(result, "score", 0.0)),
        retrieval_score_type=getattr(result, "retrieval_score_type", ""),
        reranker_score=getattr(result, "reranker_score", None),
        reranker_score_type=getattr(result, "reranker_score_type", ""),
        start_char=int(meta["start_char"]) if "start_char" in meta else None,
        end_char=int(meta["end_char"]) if "end_char" in meta else None,
        text_chars=len(text),
        text_preview=text[:150].replace("\n", " "),
    )


class PromptBuilder:


    TEMPLATE_DIRECT: str = (
        "Answer the following question accurately and concisely.\n\n"
        "Question: {question}\n\n"
        "Answer:"
    )


    TEMPLATE_BASIC: str = (
        "Use the following context to answer the question.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Answer:"
    )


    TEMPLATE_GROUNDED_ARCHIVED: str = (
        "You are a question-answering assistant. Answer using the provided "
        "context as evidence.\n\n"
        "Rules:\n"
        "1. Use the context as the primary source of truth.\n"
        "2. The answer may be stated indirectly. If one entity in the context "
        "satisfies the clues in the question, answer with that entity.\n"
        "3. You may combine facts from different passages in the context.\n"
        "4. Do not require the context to repeat the exact wording of the question.\n"
        "5. Do not invent names, dates, numbers, titles, or facts that are not "
        "supported by the context.\n"
        "6. If the context is clearly unrelated or does not provide enough evidence, "
        "reply exactly: \"The provided context does not contain enough information "
        "to answer.\"\n"
        "7. Be concise and factual.\n\n"
        "<context>\n{context}\n</context>\n\n"
        "<question>{question}</question>\n\n"
        "Answer:"
    )


    TEMPLATE_GROUNDED_SOURCED: str = (
        "You are a question-answering assistant. Answer using the provided "
        "context as evidence. Each passage is labelled [S1], [S2], etc.\n\n"
        "Rules:\n"
        "1. Use the context as the primary source of truth.\n"
        "2. The answer may be stated indirectly. If one entity in the context "
        "satisfies the clues in the question, answer with that entity.\n"
        "3. You may combine facts from different passages in the context.\n"
        "4. Do not require the context to use the exact wording of the question.\n"
        "5. Do not invent names, dates, numbers, titles, or facts that are not "
        "supported by the context.\n"
        "6. Refuse only if the context is unrelated or no answer can be supported "
        "from the provided passages. If refusing, reply exactly: "
        "\"The provided context does not contain enough information to answer.\"\n"
        "7. Be concise and factual.\n"
        "8. Cite the source labels [S1], [S2], etc. at the end of sentences "
        "that use that source.\n\n"
        "<context>\n{context}\n</context>\n\n"
        "<question>{question}</question>\n\n"
        "Answer:"
    )


    _TEMPLATES: dict[str, str] = {
        "direct": TEMPLATE_DIRECT,
        "basic": TEMPLATE_BASIC,
        "grounded_sourced": TEMPLATE_GROUNDED_SOURCED,
    }


    CONTEXT_SEPARATOR: str = "\n---\n"

    def __init__(self, version: str = "basic") -> None:

        if version not in self._TEMPLATES:
            available: str = ", ".join(self._TEMPLATES.keys())
            raise ValueError(
                f"Version de prompt '{version}' no reconocida. "
                f"Disponibles: {available}"
            )
        self.version: str = version
        self.template: str = self._TEMPLATES[version]

    def build(
        self,
        question: str,
        contexts: list[str] | None = None,
    ) -> str:

        context_text: str = ""
        if contexts:
            if self.version == "grounded_sourced":

                labelled: list[str] = [
                    f"[S{i + 1}] {c}" for i, c in enumerate(contexts)
                ]
                context_text = self.CONTEXT_SEPARATOR.join(labelled)
            else:
                context_text = self.CONTEXT_SEPARATOR.join(contexts)

        prompt: str = self.template.format(
            question=question,
            context=context_text,
        )

        logger.info(
            "Prompt construido: version=%s, contexts=%d, "
            "prompt_length=%d chars",
            self.version,
            len(contexts) if contexts else 0,
            len(prompt),
        )
        return prompt

    def build_with_sources(
        self,
        question: str,
        results: list,
    ) -> tuple[str, list[SourceInfo]]:

        sources: list[SourceInfo] = []
        contexts: list[str] = []
        for i, r in enumerate(results):
            sid: str = f"S{i + 1}"
            sources.append(source_info_from_result(r, sid))
            contexts.append(getattr(r, "text", ""))

        prompt: str = self.build(question=question, contexts=contexts)
        return prompt, sources

    @classmethod
    def available_versions(cls) -> list[str]:

        return list(cls._TEMPLATES.keys())


SYSTEM_PROMPT: str = (
    "You are a strict deterministic evaluator for a RAG question-answering "
    "thesis. Evaluate each item independently. Do not let one item influence "
    "another. Use only the fields inside each item. Return exactly one JSON "
    "object that conforms to the supplied schema. Do not include prose, "
    "markdown, or explanations outside the JSON."
)

_EVAL_USER_TEMPLATE: str = """\
Evaluate the following {n} independent question-answering samples.

Rules:
- Treat each item as a separate evaluation.
- Do not transfer evidence, facts, or judgments between items.
- Return exactly {n} result objects.
- Each result must contain the same eval_item_id as the input item.
- Include received_count = {n}.
- The input item must include config_name. Use config_name == "no_rag" to identify the no-RAG control.
- Treat context as empty if it is missing, null, an empty string, or only whitespace.
- If an answer refuses because the context is insufficient, judge whether that refusal is appropriate.
- Penalize false refusals, unsupported claims, contradictions, wrong entities, wrong dates, wrong numbers, wrong yes/no polarity, and facts not supported by context.
- Ground truth is used only to judge correctness. Do not treat ground_truth as retrieved context.
- evidence_quotes must come only from the provided context, never from ground_truth.

No-context / no_rag override:
If config_name == "no_rag" OR the provided context is empty:
- faithfulness must be 0.0
- context_support must be 0.0
- context_sufficient must be false
- answer_supported_by_context must be false
- evidence_quotes must be []
- is_false_refusal must be false: context is never sufficient for no_rag, so a refusal can never be "false" (unnecessary). Set is_false_refusal=false regardless of what the answer says.
- is_correct_refusal: set to true if is_refusal is true; set to false if is_refusal is false. A refusal when context is absent is always a correct refusal.
- do not assign support from ground_truth
- these rules apply even if the answer is correct, incorrect, a refusal, or a correct refusal

Failure attribution override for no_rag / empty context:
- If config_name == "no_rag" OR the provided context is empty:
  - failure_type MUST be "retrieval_failure" regardless of answer_correct.
  - Rationale: failure_type measures PIPELINE-LEVEL failure attribution.
    When retrieval is disabled (no_rag), the pipeline failed at the retrieval
    layer for every sample. The LLM answer quality is captured independently
    by answer_correct and the correctness score - do not conflate it with failure_type.
  - Do NOT use "uncertain", "generation_failure", "none", or "both" for no_rag.

Scores (floats 0.0-100.0, 100.0 = excellent, 0.0 = completely wrong):
- correctness: whether the answer matches the ground_truth in meaning
- faithfulness: whether factual claims in the answer are supported by the context; use 0.0 for no_rag or empty context
- answer_relevance: whether the answer directly addresses the question
- context_support: whether the context contains enough evidence to answer; use 0.0 for no_rag or empty context
- refusal_quality: whether refusal behavior is appropriate; use 100.0 for a non-refusal when context supports answering
- overall: holistic score using correctness, faithfulness, answer relevance, context support, and refusal behavior

Classic boolean flags:
- is_refusal: true if the answer is a refusal
- is_correct_refusal: true if the answer correctly refuses because context is insufficient
- is_false_refusal: true if the answer refuses despite context being sufficient
- has_contradiction: true if the answer contradicts the context or ground_truth
- answer_type: one of yes_no, entity, date, number, descriptive, unknown

Failure attribution fields (required for thesis analysis):
- answer_correct: boolean - true if the answer is factually correct per ground_truth
- context_sufficient: boolean - true if the context contains enough evidence to answer correctly; always false for no_rag or empty context
- answer_supported_by_context: boolean - true if every factual claim in the answer can be traced to the provided context; always false for no_rag or empty context
- failure_type: one of:
    "none"               context was sufficient AND answer is correct
    "retrieval_failure"  context_sufficient=false; the evidence was not retrieved or retrieval was disabled (no_rag/empty context). ALWAYS use this for no_rag regardless of answer_correct.
    "generation_failure" context_sufficient=true but answer_correct=false; the LLM failed despite having the evidence (hallucination, wrong entity, confusion). Only valid when context is non-empty.
    "both"               context insufficient AND the answer would still be wrong even with perfect context. Only valid when context is non-empty.
    "uncertain"          cannot determine; deeply ambiguous question or judge cannot decide. Never use for no_rag.
- judge_summary: 1-2 sentence plain English explanation of the verdict; must state whether answer is correct, the failure_type assigned, and whether context was sufficient
- evidence_quotes: list of up to 3 short verbatim quotes from the context that support or contradict the judgment; empty list if context is absent

Items:
{items_json}

Return JSON only."""


def build_user_prompt(samples: list[dict]) -> str:

    n: int = len(samples)
    items: list[dict] = [
        {
            "eval_item_id": s["eval_item_id"],
            "config_name": s.get("config_name", ""),
            "question": s["question"],
            "answer": s["answer"],
            "ground_truth": s.get("ground_truth", ""),
            "contexts": s.get("contexts", []),
        }
        for s in samples
    ]
    return _EVAL_USER_TEMPLATE.format(
        n=n,
        items_json=json.dumps(items, ensure_ascii=False, indent=2),
    )


__all__: list[str] = [
    "PromptBuilder",
    "SourceInfo",
    "source_info_from_result",
    "SYSTEM_PROMPT",
    "build_user_prompt",
]
