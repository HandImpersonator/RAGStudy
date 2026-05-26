from __future__ import annotations

from abc import ABC, abstractmethod
import logging
import numpy as np
from numpy.typing import NDArray

logger: logging.Logger = logging.getLogger(__name__)


class BaseEmbedder(ABC):


    def __init__(self, model_name: str, dimension: int) -> None:
        self.model_name: str = model_name
        self.dimension: int = dimension

    @abstractmethod
    def embed(self, texts: list[str], show_progress: bool = True) -> NDArray[np.float32]:

        ...

    @abstractmethod
    def embed_query(self, query: str) -> NDArray[np.float32]:

        ...


class SentenceTransformerEmbedder(BaseEmbedder):


    DEFAULT_BATCH_SIZE: int = 32


    _KNOWN_DIMENSIONS: dict[str, int] = {

        "BAAI/bge-base-en-v1.5":                            768,
        "sentence-transformers/multi-qa-MiniLM-L6-cos-v1":  384,

        "multi-qa-MiniLM-L6-cos-v1":                        384,

        "all-MiniLM-L6-v2":                                 384,
        "all-mpnet-base-v2":                                768,
    }


    _FALLBACK_DIMENSION: int = 768

    def __init__(
        self,
        model_name: str = "BAAI/bge-base-en-v1.5",
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> None:
        dimension: int = self._KNOWN_DIMENSIONS.get(
            model_name, self._FALLBACK_DIMENSION
        )
        super().__init__(model_name=model_name, dimension=dimension)


        self.batch_size: int = batch_size
        self._model = None

    def _load_model(self) -> None:

        if self._model is None:
            try:
                import torch
                from sentence_transformers import SentenceTransformer

                device: str = "cuda" if torch.cuda.is_available() else "cpu"
                self._model = SentenceTransformer(self.model_name, device=device)
                logger.info(
                    "Modelo cargado: %s (dim=%d, batch_size=%d, device=%s)",
                    self.model_name,
                    self.dimension,
                    self.batch_size,
                    device,
                )
            except ImportError as e:
                raise ImportError(
                    "sentence-transformers requerido. "
                    "Instalar: pip install sentence-transformers"
                ) from e

    def embed(self, texts: list[str], show_progress: bool = True) -> NDArray[np.float32]:

        self._load_model()
        assert self._model is not None
        embeddings: NDArray[np.float32] = self._model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )


        logger.debug(
            "Embeddings generados: %d textos → shape %s (batch_size=%d)",
            len(texts),
            embeddings.shape,
            self.batch_size,
        )
        return embeddings.astype(np.float32)

    def embed_query(self, query: str) -> NDArray[np.float32]:

        result: NDArray[np.float32] = self.embed([query])
        return result[0]
