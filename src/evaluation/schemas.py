from __future__ import annotations

from typing import Any


SCHEMA_NAME: str = "rag_eval_batch_result"


ANSWER_TYPES: list[str] = [
    "yes_no",
    "entity",
    "date",
    "number",
    "descriptive",
    "unknown",
]


PERFORMANCE_METRIC_NAMES: frozenset[str] = frozenset({
    "latency_mean_ms",
    "total_pipeline_mean_ms",
    "query_embedding_time_mean_ms",
    "retrieval_time_mean_ms",
    "reranking_time_mean_ms",
    "context_selection_time_mean_ms",
    "prompt_build_time_mean_ms",
    "generation_time_mean_ms",
    "tokens_prompt_mean",
    "tokens_generated_mean",
    "answer_length_tokens_mean",
    "memory_peak_mb",
    "num_samples",
})


QUALITY_METRIC_NAMES: tuple[str, ...] = (

    "correctness_mean",
    "faithfulness_mean",
    "answer_relevance_mean",
    "context_support_mean",
    "refusal_quality_mean",
    "overall_mean",

    "contradiction_rate",
    "refusal_rate",
    "correct_refusal_rate",
    "false_refusal_rate",


    "answer_accuracy",
    "context_sufficiency_rate",
    "faithfulness_rate",
    "retrieval_failure_rate",
    "generation_failure_rate",
    "combined_failure_rate",
    "uncertain_rate",

    "eval_completion_rate",
    "eval_pending_count",
    "eval_failed_count",
)


NUMERIC_QUALITY_METRICS: tuple[str, ...] = (
    "correctness_mean",
    "faithfulness_mean",
    "answer_relevance_mean",
    "context_support_mean",
    "refusal_quality_mean",
    "overall_mean",
)


RATE_QUALITY_METRICS: tuple[str, ...] = (
    "contradiction_rate",
    "refusal_rate",
    "correct_refusal_rate",
    "false_refusal_rate",
    "answer_accuracy",
    "context_sufficiency_rate",
    "faithfulness_rate",
    "retrieval_failure_rate",
    "generation_failure_rate",
    "combined_failure_rate",
    "uncertain_rate",
    "eval_completion_rate",
)


FAILURE_TYPES: list[str] = [
    "none",
    "retrieval_failure",
    "generation_failure",
    "both",
    "uncertain",
]


RAG_EVAL_BATCH_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "received_count": {
            "type": "integer",
            "description": (
                "Number of items received - must equal the number of input "
                "samples sent in this batch."
            ),
        },
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "eval_item_id": {
                        "type": "string",
                        "description": (
                            "Stable identifier copied verbatim from the input "
                            "item. Format: run_id::config_name::NNNN"
                        ),
                    },


                    "correctness": {
                        "type": "number",
                        "description": (
                            "0-100. Whether the answer matches the ground_truth "
                            "in meaning."
                        ),
                    },
                    "faithfulness": {
                        "type": "number",
                        "description": (
                            "0-100. Whether factual claims in the answer are "
                            "supported by the context. Use 0 for no_rag or "
                            "empty context."
                        ),
                    },
                    "answer_relevance": {
                        "type": "number",
                        "description": (
                            "0-100. Whether the answer directly addresses the "
                            "question."
                        ),
                    },
                    "context_support": {
                        "type": "number",
                        "description": (
                            "0-100. Whether the context contains enough evidence "
                            "to answer the question."
                        ),
                    },
                    "refusal_quality": {
                        "type": "number",
                        "description": (
                            "0-100. Appropriateness of refusal behaviour. Use "
                            "100 for a non-refusal when context supports answering."
                        ),
                    },
                    "overall": {
                        "type": "number",
                        "description": (
                            "0-100. Holistic score combining correctness, "
                            "faithfulness, relevance, context support, and "
                            "refusal behaviour."
                        ),
                    },


                    "is_refusal": {
                        "type": "boolean",
                        "description": "True if the answer is a refusal.",
                    },
                    "is_correct_refusal": {
                        "type": "boolean",
                        "description": (
                            "True if the answer correctly refuses because "
                            "the context is insufficient."
                        ),
                    },
                    "is_false_refusal": {
                        "type": "boolean",
                        "description": (
                            "True if the answer incorrectly refuses despite "
                            "the context being sufficient."
                        ),
                    },
                    "has_contradiction": {
                        "type": "boolean",
                        "description": (
                            "True if the answer contradicts the context or "
                            "ground truth."
                        ),
                    },
                    "answer_type": {
                        "type": "string",
                        "enum": ANSWER_TYPES,
                        "description": "Semantic type of the expected answer.",
                    },


                    "answer_correct": {
                        "type": "boolean",
                        "description": (
                            "True if the answer is factually correct according "
                            "to the ground_truth (binary verdict, independent of "
                            "the continuous correctness score)."
                        ),
                    },
                    "context_sufficient": {
                        "type": "boolean",
                        "description": (
                            "True if the retrieved context contains enough "
                            "evidence to answer the question correctly. "
                            "False signals a retrieval failure. "
                            "Always False for no_rag configurations."
                        ),
                    },
                    "answer_supported_by_context": {
                        "type": "boolean",
                        "description": (
                            "True if every factual claim in the answer can be "
                            "traced back to the provided context. "
                            "False when the answer invents facts or ignores context."
                        ),
                    },
                    "failure_type": {
                        "type": "string",
                        "enum": FAILURE_TYPES,
                        "description": (
                            "Root cause of the failure for this sample. "
                            "'none': context sufficient and answer correct. "
                            "'retrieval_failure': context_sufficient=False; "
                            "the evidence was not retrieved or retrieval was disabled "
                            "(no_rag/empty context). Always used for no_rag regardless "
                            "of whether the answer happens to be correct. "
                            "'generation_failure': context_sufficient=True but "
                            "answer_correct=False; the LLM failed despite having "
                            "the evidence (hallucination, confusion, wrong entity). "
                            "Only valid when context is non-empty. "
                            "'both': context insufficient AND answer wrong in a way "
                            "that would persist even with better context. "
                            "Only valid when context is non-empty. "
                            "'uncertain': cannot be determined (no ground_truth, "
                            "deeply ambiguous question, or judge cannot decide). "
                            "Never use for no_rag."
                        ),
                    },
                    "judge_summary": {
                        "type": "string",
                        "description": (
                            "1 sentence plain English explanation of the "
                            "evaluation verdict. Must state whether the answer "
                            "is correct, why the failure_type was assigned, "
                            "and whether the context was sufficient."
                        ),
                    },
                    "evidence_quotes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Up to 3 short verbatim quotes from the context "
                            "that support (or contradict) the judgment. "
                            "Empty array if context is absent (no_rag)."
                        ),
                    },
                },
                "required": [
                    "eval_item_id",
                    "correctness",
                    "faithfulness",
                    "answer_relevance",
                    "context_support",
                    "refusal_quality",
                    "overall",
                    "is_refusal",
                    "is_correct_refusal",
                    "is_false_refusal",
                    "has_contradiction",
                    "answer_type",

                    "answer_correct",
                    "context_sufficient",
                    "answer_supported_by_context",
                    "failure_type",
                    "judge_summary",
                    "evidence_quotes",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": ["received_count", "results"],
    "additionalProperties": False,
}

__all__: list[str] = [
    "SCHEMA_NAME",
    "ANSWER_TYPES",
    "FAILURE_TYPES",
    "PERFORMANCE_METRIC_NAMES",
    "QUALITY_METRIC_NAMES",
    "NUMERIC_QUALITY_METRICS",
    "RATE_QUALITY_METRICS",
    "RAG_EVAL_BATCH_SCHEMA",
]
