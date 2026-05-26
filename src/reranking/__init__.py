from __future__ import annotations

from abc import ABC, abstractmethod
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.retrieval import RetrievalResult

logger: logging.Logger = logging.getLogger(__name__)


class BaseReranker(ABC):


    def __init__(self, top_n: int = 3) -> None:
        self.top_n: int = top_n

    @abstractmethod
    def rerank(
        self,
        query: str,
        texts: list[str],
        scores: list[float] | None = None,
    ) -> list[tuple[str, float]]:

        ...

    def rerank_results(
        self,
        query: str,
        results: list["RetrievalResult"],
    ) -> list["RetrievalResult"]:


        if not results:
            return []
        texts: list[str] = [r.text for r in results]
        scores: list[float] = [r.score for r in results]
        reranked_pairs: list[tuple[str, float]] = self.rerank(query, texts, scores)


        text_to_result: dict[str, "RetrievalResult"] = {}
        for r in results:
            if r.text not in text_to_result:
                text_to_result[r.text] = r

        reranked_results: list["RetrievalResult"] = []
        for text, new_score in reranked_pairs:
            original: "RetrievalResult | None" = text_to_result.get(text)
            if original is None:

                from src.retrieval import RetrievalResult
                original = RetrievalResult(text=text, score=new_score, chunk_id=-1)


            from dataclasses import replace as _dc_replace
            reranked_results.append(
                _dc_replace(
                    original,
                    reranker_score=new_score,
                    reranker_score_type=self._reranker_score_type(),
                )
            )
        return reranked_results

    def _reranker_score_type(self) -> str:

        return "unknown"


class CrossEncoderReranker(BaseReranker):


    MODEL_NAME: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(self, top_n: int = 3, model_name: str | None = None) -> None:
        super().__init__(top_n=top_n)
        if model_name:
            self.MODEL_NAME = model_name
        self._model = None

    def _load_model(self) -> None:

        if self._model is None:
            try:
                import torch
                from sentence_transformers import CrossEncoder

                device: str = "cuda" if torch.cuda.is_available() else "cpu"
                self._model = CrossEncoder(self.MODEL_NAME, device=device)
                logger.info(
                    "CrossEncoder cargado: %s (device=%s)",
                    self.MODEL_NAME, device,
                )
            except ImportError as e:
                raise ImportError(
                    "sentence-transformers requerido para CrossEncoderReranker. "
                    "Instalar: pip install sentence-transformers"
                ) from e

    def _reranker_score_type(self) -> str:
        return "cross_encoder_logit"

    def rerank(
        self,
        query: str,
        texts: list[str],
        scores: list[float] | None = None,
    ) -> list[tuple[str, float]]:

        if not texts:
            return []

        self._load_model()
        assert self._model is not None


        pairs: list[list[str]] = [[query, text] for text in texts]


        ce_scores: list[float] = self._model.predict(pairs).tolist()


        paired: list[tuple[str, float]] = sorted(
            zip(texts, ce_scores),
            key=lambda x: x[1],
            reverse=True,
        )


        result: list[tuple[str, float]] = paired[: self.top_n]

        logger.info(
            "CrossEncoderReranker: %d -> %d fragmentos "
            "(score range: %.3f a %.3f)",
            len(texts),
            len(result),
            min(ce_scores),
            max(ce_scores),
        )
        return result

    def rerank_results(
        self,
        query: str,
        results: list["RetrievalResult"],
    ) -> list["RetrievalResult"]:

        if not results:
            return []

        self._load_model()
        assert self._model is not None

        texts: list[str] = [r.text for r in results]
        pairs: list[list[str]] = [[query, t] for t in texts]
        ce_scores: list[float] = self._model.predict(pairs).tolist()


        from dataclasses import replace as _dc_replace
        paired_results: list[tuple["RetrievalResult", float]] = sorted(
            zip(results, ce_scores),
            key=lambda x: x[1],
            reverse=True,
        )

        top_results: list["RetrievalResult"] = []
        for r, ce_score in paired_results[: self.top_n]:
            top_results.append(
                _dc_replace(
                    r,
                    reranker_score=ce_score,
                    reranker_score_type="cross_encoder_logit",
                )
            )

        logger.info(
            "CrossEncoderReranker: %d -> %d fragmentos "
            "(logit range: %.3f a %.3f)",
            len(results),
            len(top_results),
            min(ce_scores),
            max(ce_scores),
        )
        return top_results


class NoReranker(BaseReranker):


    def __init__(self, top_n: int = 5) -> None:
        super().__init__(top_n=top_n)

    def _reranker_score_type(self) -> str:
        return "pass_through"

    def rerank(
        self,
        query: str,
        texts: list[str],
        scores: list[float] | None = None,
    ) -> list[tuple[str, float]]:

        if scores is None:
            scores = [0.0] * len(texts)


        paired: list[tuple[str, float]] = list(zip(texts, scores))
        result: list[tuple[str, float]] = paired[: self.top_n]

        logger.info(
            "NoReranker: %d -> %d fragmentos (sin reordenar)",
            len(texts),
            len(result),
        )
        return result

    def rerank_results(
        self,
        query: str,
        results: list["RetrievalResult"],
    ) -> list["RetrievalResult"]:

        from dataclasses import replace as _dc_replace
        top: list["RetrievalResult"] = results[: self.top_n]
        promoted: list["RetrievalResult"] = [
            _dc_replace(
                r,
                reranker_score=r.score,
                reranker_score_type="pass_through",
            )
            for r in top
        ]
        logger.info(
            "NoReranker: %d -> %d fragmentos (sin reordenar)",
            len(results),
            len(promoted),
        )
        return promoted
