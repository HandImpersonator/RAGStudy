from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import logging

logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class EvalSample:


    question: str
    answer: str
    context: str
    source: str = ""


@dataclass
class Document:


    content: str
    metadata: dict[str, str] = field(default_factory=dict)
    source_path: Path | None = None


class DocumentLoader:


    SUPPORTED_EXTENSIONS: list[str] = [".txt", ".md"]

    def __init__(self, data_dir: Path, file_prefixes: list[str] | None = None) -> None:

        self.data_dir: Path = data_dir


        self.file_prefixes: list[str] | None = file_prefixes
        if not self.data_dir.exists():
            raise FileNotFoundError(
                f"Directorio de datos no encontrado: {self.data_dir}"
            )

    def load_all(self, show_progress: bool = True) -> list[Document]:


        filepaths: list[Path] = []
        for ext in self.SUPPORTED_EXTENSIONS:
            for filepath in sorted(self.data_dir.glob(f"**/*{ext}")):
                if self.file_prefixes is not None:
                    if not any(filepath.name.startswith(p) for p in self.file_prefixes):
                        continue
                filepaths.append(filepath)

        documents: list[Document] = []
        iterator: Any = filepaths
        if show_progress:
            try:
                from tqdm.auto import tqdm
                iterator = tqdm(filepaths, desc="ingestion", unit="doc")
            except ImportError:
                iterator = filepaths

        for filepath in iterator:
            try:
                doc: Document = self._load_file(filepath)
                documents.append(doc)


                logger.debug("Documento cargado: %s", filepath.name)
            except (OSError, UnicodeDecodeError) as e:
                logger.error("Error cargando %s: %s", filepath, e)

        logger.info("Total documentos cargados: %d", len(documents))
        return documents

    def _load_file(self, filepath: Path) -> Document:

        content: str = filepath.read_text(encoding="utf-8")


        content = self._preprocess(content)

        metadata: dict[str, str] = {
            "filename": filepath.name,
            "extension": filepath.suffix,
            "path": str(filepath),
        }

        return Document(
            content=content,
            metadata=metadata,
            source_path=filepath,
        )

    @staticmethod
    def _preprocess(text: str) -> str:


        import re
        text = re.sub(r"\n{3,}", "\n\n", text)

        text = "\n".join(line.rstrip() for line in text.splitlines())
        return text.strip()
