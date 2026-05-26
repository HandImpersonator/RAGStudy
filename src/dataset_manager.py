from __future__ import annotations

import json
import logging
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import urlretrieve
from urllib.error import URLError

from src.ingestion import EvalSample

logger: logging.Logger = logging.getLogger(__name__)


_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = _PROJECT_ROOT / "data"
EVAL_DIR: Path = DATA_DIR / "eval"
CORPUS_DIR: Path = DATA_DIR / "corpus"


@dataclass(frozen=True)
class DatasetConfig:


    name: str
    description: str
    url: str
    local_filename: str
    requires_internet: bool
    license_info: str


DATASET_CONFIGS: dict[str, DatasetConfig] = {
    "sample": DatasetConfig(
        name="sample",
        description="20 triples hand-crafted sobre RAG y AI (offline)",
        url="",
        local_filename="sample_eval.json",
        requires_internet=False,
        license_info="Creado para este TFG, uso libre",
    ),
    "rag_domain": DatasetConfig(
        name="rag_domain",
        description="25 triples curados manualmente del corpus de dominio RAG (offline)",
        url="",
        local_filename="rag_domain_eval.json",
        requires_internet=False,
        license_info="Creado para este TFG, uso libre",
    ),

    "hotpotqa_eval": DatasetConfig(
        name="hotpotqa_eval",
        description="HotpotQA dev full wiki - preguntas multi-salto con pasajes de soporte de Wikipedia",
        url="",
        local_filename="hotpotqa_eval.json",
        requires_internet=False,
        license_info="CC BY-SA 4.0 (Carnegie Mellon University)",
    ),

    "triviaqa_eval": DatasetConfig(
        name="triviaqa_eval",
        description="TriviaQA rc dev - preguntas de trivia con pasajes de evidencia de Wikipedia",
        url="",
        local_filename="triviaqa_eval.json",
        requires_internet=False,
        license_info="Apache 2.0 (University of Washington)",
    ),
}


class DatasetManager:


    def __init__(
        self,
        eval_dir: Path = EVAL_DIR,
        corpus_dir: Path = CORPUS_DIR,
    ) -> None:
        self.eval_dir: Path = eval_dir
        self.corpus_dir: Path = corpus_dir
        self.eval_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def list_available() -> list[str]:

        return list(DATASET_CONFIGS.keys())

    def is_cached(self, dataset_name: str) -> bool:

        config: DatasetConfig = self._get_config(dataset_name)
        filepath: Path = self.eval_dir / config.local_filename
        return filepath.exists()

    def load(
        self,
        dataset_name: str,
        max_samples: int = 0,
        allow_eval_rebuild: bool = True,
    ) -> list[EvalSample]:

        config: DatasetConfig = self._get_config(dataset_name)
        filepath: Path = self.eval_dir / config.local_filename


        LARGE_DATASET_DEFAULT_CAP: dict[str, int] = {
            "triviaqa": 1000,
            "triviaqa_eval": 1000,
            "hotpotqa": 1000,
            "hotpotqa_eval": 1000,
        }


        resolved: str = {"hotpotqa": "hotpotqa_eval", "triviaqa": "triviaqa_eval"}.get(
            dataset_name, dataset_name
        )

        def _run_builder(limit: int) -> bool:

            if resolved == "triviaqa_eval":

                filepath.unlink(missing_ok=True)
                return self._build_triviaqa_eval(filepath, max_samples=limit)
            if resolved == "hotpotqa_eval":
                filepath.unlink(missing_ok=True)
                return self._build_hotpotqa_eval(filepath, max_samples=limit)
            return False

        _cap: int | None = LARGE_DATASET_DEFAULT_CAP.get(dataset_name)

        if not filepath.exists():


            _build_limit: int = max_samples if max_samples > 0 else (_cap or 0)
            generated: bool = _run_builder(_build_limit)
            if not generated or not filepath.exists():
                raise FileNotFoundError(
                    f"Dataset '{dataset_name}' no encontrado en caché: {filepath}. "
                    f"Usa load_or_download() o descarga manualmente con "
                    f"scripts/download_corpus.py --source {dataset_name.replace('_eval','')} "
                    f"--max-samples {max_samples if max_samples > 0 else (_cap or 1000)}"
                )


        samples: list[EvalSample] = self._parse_dataset(filepath, dataset_name)


        _raw_source: str = dataset_name.replace("_eval", "")


        _BOLD   = "\033[1m"   if sys.stderr.isatty() else ""
        _YELLOW = "\033[33m"  if sys.stderr.isatty() else ""
        _RED    = "\033[31m"  if sys.stderr.isatty() else ""
        _RESET  = "\033[0m"   if sys.stderr.isatty() else ""
        _W      = 70

        def _banner(lines: list[str], colour: str = _YELLOW,
                    pause: float = 5.0) -> None:

            border = colour + _BOLD + "!" * _W + _RESET
            print(border, file=sys.stderr)
            for line in lines:
                print(f"{colour}{_BOLD}!{_RESET}  {line}", file=sys.stderr)
            print(border, file=sys.stderr)
            sys.stderr.flush()

            for line in lines:
                logger.warning(line)
            if pause > 0:
                logger.warning(
                    "Pausando %gs para que el mensaje sea legible…", pause
                )
                time.sleep(pause)

        if max_samples > 0 and len(samples) < max_samples:
            if allow_eval_rebuild:
                logger.info(
                    "Dataset '%s': caché contiene %d muestras pero se "
                    "solicitaron %d.  Intentando reconstruir el eval JSON "
                    "desde los datos crudos…",
                    dataset_name, len(samples), max_samples,
                )
                rebuilt: bool = _run_builder(max_samples)
                if rebuilt and filepath.exists():
                    samples = self._parse_dataset(filepath, dataset_name)
                    logger.info(
                        "Eval JSON reconstruido: %d muestras disponibles.",
                        len(samples),
                    )
                    if len(samples) < max_samples:
                        _banner([
                            f"Dataset '{dataset_name}': los datos crudos sólo",
                            f"contienen {len(samples)} muestras; se solicitaron"
                            f" {max_samples}.",
                            "",
                            "Para descargar más ejecuta primero:",
                            f"  python3 scripts/download_corpus.py \\",
                            f"      --source {_raw_source} "
                            f"--max-samples {max_samples}",
                        ], colour=_YELLOW, pause=5.0)
                else:
                    _banner([
                        f"Dataset '{dataset_name}': no se pudo reconstruir el",
                        "eval JSON (datos crudos no disponibles en disco).",
                        f"Caché tiene {len(samples)} muestras; "
                        f"se solicitaron {max_samples}.",
                        "",
                        "Para ampliar ejecuta primero:",
                        f"  python3 scripts/download_corpus.py \\",
                        f"      --source {_raw_source} "
                        f"--max-samples {max_samples}",
                    ], colour=_YELLOW, pause=5.0)
            else:

                _banner([
                    "MODO --cached-only ACTIVO — no se puede ampliar la caché.",
                    "",
                    f"  Dataset   : {dataset_name}",
                    f"  Solicitado: {max_samples} muestras",
                    f"  Disponible: {len(samples)} muestras  "
                    f"← el experimento usará SÓLO este número",
                    "",
                    "Para ampliar la caché ejecuta ESTOS COMANDOS (sin "
                    "--cached-only)",
                    "y luego vuelve a lanzar el experimento:",
                    "",
                    f"  python3 scripts/download_corpus.py \\",
                    f"      --source {_raw_source} "
                    f"--max-samples {max_samples}",
                    "",
                    f"  python3 scripts/prepare_rag_artifacts.py \\",
                    f"      --dataset {dataset_name} "
                    f"--max-samples {max_samples}",
                ], colour=_RED, pause=10.0)


        if _cap is not None and max_samples == 0 and len(samples) > _cap:
            logger.info(
                "Dataset '%s' tiene %d muestras; aplicando tope automático de %d. "
                "Pasa --max-samples N para obtener un número distinto.",
                dataset_name, len(samples), _cap,
            )
            samples = samples[:_cap]
        elif max_samples > 0:
            samples = samples[:max_samples]

        logger.info(
            "Dataset '%s' cargado: %d samples (desde caché local)",
            dataset_name,
            len(samples),
        )
        return samples

    def download(self, dataset_name: str) -> Path:

        config: DatasetConfig = self._get_config(dataset_name)

        if not config.requires_internet:
            logger.info(
                "Dataset '%s' no requiere descarga (incluido localmente)",
                dataset_name,
            )
            return self.eval_dir / config.local_filename

        filepath: Path = self.eval_dir / config.local_filename

        if filepath.exists():
            logger.info(
                "Dataset '%s' ya en caché: %s", dataset_name, filepath
            )
            return filepath

        logger.info(
            "Descargando dataset '%s' desde %s...",
            dataset_name,
            config.url,
        )

        try:
            urlretrieve(config.url, str(filepath))
            logger.info("Descarga completa: %s", filepath)
            return filepath
        except URLError as e:
            logger.error(
                "Error descargando '%s': %s. "
                "¿Hay conexión a internet?",
                dataset_name,
                e,
            )
            raise

    def load_or_download(
        self,
        dataset_name: str,
        max_samples: int = 0,
        allow_eval_rebuild: bool = True,
    ) -> list[EvalSample]:

        if not self.is_cached(dataset_name):
            self.download(dataset_name)

        return self.load(dataset_name, max_samples=max_samples,
                         allow_eval_rebuild=allow_eval_rebuild)

    def load_corpus_documents(self) -> list[Path]:

        if not self.corpus_dir.exists():
            logger.warning("Directorio de corpus no encontrado: %s", self.corpus_dir)
            return []

        extensions: list[str] = [".md", ".txt"]
        files: list[Path] = []
        for ext in extensions:
            files.extend(sorted(self.corpus_dir.glob(f"*{ext}")))

        logger.info(
            "Corpus: %d archivos encontrados en %s",
            len(files),
            self.corpus_dir,
        )
        return files


    def _build_triviaqa_eval(self, dest: Path, max_samples: int = 1000) -> bool:

        import tarfile as _tarfile

        external_dir: Path = DATA_DIR / "external"
        dev_json: Path = external_dir / "qa" / "wikipedia-dev.json"
        evidence_dir: Path = external_dir / "evidence" / "wikipedia"


        if not dev_json.exists():
            tarball: Path = external_dir / "triviaqa-rc.tar.gz"
            if not tarball.exists():
                logger.warning(
                    "_build_triviaqa_eval: ni %s ni %s encontrados. "
                    "Descarga el tarball con: "
                    "python3 scripts/download_corpus.py --source triviaqa",
                    dev_json, tarball,
                )
                return False
            logger.info("Extrayendo %s en %s …", tarball.name, external_dir)
            try:
                with _tarfile.open(tarball, "r:gz") as tf:
                    tf.extractall(path=external_dir)
                logger.info("Extracción completada. qa/ en %s", external_dir)
            except _tarfile.TarError as exc:
                logger.error("Error extrayendo %s: %s", tarball.name, exc)
                return False

        if not dev_json.exists():
            logger.error(
                "_build_triviaqa_eval: %s no encontrado después de extracción.",
                dev_json,
            )
            return False

        logger.info(
            "Generando triviaqa_eval.json desde %s (máx. %d muestras)…",
            dev_json, max_samples,
        )

        try:
            with open(dev_json, encoding="utf-8") as fh:
                data: dict[str, Any] = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("No se pudo leer %s: %s", dev_json, exc)
            return False


        def _slugify(text: str, max_len: int = 60) -> str:
            text = text.lower()
            text = re.sub(r"[^a-z0-9]+", "_", text)
            return text.strip("_")[:max_len]

        qa_pairs: list[dict[str, Any]] = []

        for item in data.get("Data", []):
            if len(qa_pairs) >= max_samples:
                break

            question: str = item.get("Question", "").strip()
            if not question:
                continue

            answer_obj: dict[str, Any] = item.get("Answer", {})
            normalized_answer: str = answer_obj.get("NormalizedValue", "").strip()
            answer_aliases: list[str] = answer_obj.get("NormalizedAliases", [])

            if not normalized_answer:
                continue


            evidence_text: str = ""
            evidence_source: str = ""

            for page in item.get("EntityPages", []):
                filename: str = page.get("Filename", "")
                if filename:
                    candidate: Path = evidence_dir / filename
                    if candidate.exists():
                        try:
                            raw: str = candidate.read_text(encoding="utf-8", errors="replace")
                            evidence_text = raw[:1500].strip()
                            evidence_source = filename
                            break
                        except OSError:
                            continue

            if not evidence_text:
                for result in item.get("SearchResults", []):
                    snippet: str = result.get("Description", "").strip()
                    if len(snippet) > 100:
                        evidence_text = snippet
                        evidence_source = result.get("Url", "search_result")
                        break

            question_id: str = item.get("QuestionId", _slugify(question, 40))


            corpus_filename: str = ""
            if evidence_text:
                corpus_filename = f"triviaqa_{_slugify(question_id, 50)}.md"
                corpus_path: Path = self.corpus_dir / corpus_filename
                if not corpus_path.exists():
                    try:
                        self.corpus_dir.mkdir(parents=True, exist_ok=True)
                        corpus_path.write_text(
                            f"# TriviaQA: {question}\n\n"
                            f"**Fuente**: {evidence_source}\n\n"
                            f"{evidence_text}\n",
                            encoding="utf-8",
                        )
                    except OSError as exc:
                        logger.warning("No se pudo guardar corpus %s: %s", corpus_filename, exc)

            qa_pairs.append(
                {
                    "question": question,
                    "answer": normalized_answer,
                    "answer_aliases": answer_aliases,
                    "context": evidence_text[:800] if evidence_text else "",
                    "source": corpus_filename if corpus_filename else "triviaqa_no_evidence",
                    "topic": "triviaqa",
                }
            )

        if not qa_pairs:
            logger.warning("_build_triviaqa_eval: no se generaron pares QA.")
            return False

        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(dest, "w", encoding="utf-8") as fh:
                json.dump(qa_pairs, fh, ensure_ascii=False, indent=2)
        except OSError as exc:
            logger.error("No se pudo escribir %s: %s", dest, exc)
            return False

        logger.info(
            "triviaqa_eval.json generado: %d muestras → %s", len(qa_pairs), dest
        )
        return True

    def _build_hotpotqa_eval(self, dest: Path, max_samples: int = 1000) -> bool:

        external_dir: Path = DATA_DIR / "external"

        candidates: list[Path] = [
            external_dir / "hotpot_dev_distractor_v1.json",
        ]
        dev_json: Path | None = next((p for p in candidates if p.exists()), None)

        if dev_json is None:
            logger.warning(
                "_build_hotpotqa_eval: ningún archivo HotpotQA encontrado en %s - "
                "ejecuta: python3 scripts/download_corpus.py --source hotpotqa",
                external_dir,
            )
            return False

        logger.info(
            "Generando hotpotqa_eval.json desde %s (máx. %d muestras)…",
            dev_json, max_samples,
        )

        try:
            with open(dev_json, encoding="utf-8") as fh:
                data: list[dict[str, Any]] = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("No se pudo leer %s: %s", dev_json, exc)
            return False

        qa_pairs: list[dict[str, Any]] = []

        for item in data:
            if max_samples > 0 and len(qa_pairs) >= max_samples:
                break

            question: str = item.get("question", "").strip()
            answer: str = item.get("answer", "").strip()
            if not question or not answer:
                continue


            supporting: list[str] = [
                title
                for title, *_ in item.get("supporting_facts", [])
            ]
            context_parts: list[str] = []
            for title, sentences in item.get("context", []):
                if title in supporting:
                    context_parts.append(" ".join(sentences))
            context: str = " ".join(context_parts)[:800]

            qa_pairs.append(
                {
                    "question": question,
                    "answer": answer,
                    "answer_aliases": [],
                    "context": context,
                    "supporting_titles": list(dict.fromkeys(supporting)),
                    "source": item.get("_id", "hotpotqa"),
                    "topic": "hotpotqa",
                }
            )

        if not qa_pairs:
            logger.warning("_build_hotpotqa_eval: no se generaron pares QA.")
            return False

        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(dest, "w", encoding="utf-8") as fh:
                json.dump(qa_pairs, fh, ensure_ascii=False, indent=2)
        except OSError as exc:
            logger.error("No se pudo escribir %s: %s", dest, exc)
            return False

        logger.info(
            "hotpotqa_eval.json generado: %d muestras → %s", len(qa_pairs), dest
        )
        return True

    @staticmethod
    def _get_config(dataset_name: str) -> DatasetConfig:


        aliases: dict[str, str] = {
            "hotpotqa": "hotpotqa_eval",
            "triviaqa": "triviaqa_eval",
        }
        resolved: str = aliases.get(dataset_name, dataset_name)
        if resolved not in DATASET_CONFIGS:
            available: str = ", ".join(
                sorted(set(list(DATASET_CONFIGS.keys()) + list(aliases.keys())))
            )
            raise ValueError(
                f"Dataset '{dataset_name}' no reconocido. "
                f"Disponibles: {available}"
            )
        return DATASET_CONFIGS[resolved]

    def _parse_dataset(
        self,
        filepath: Path,
        dataset_name: str,
    ) -> list[EvalSample]:


        aliases: dict[str, str] = {
            "hotpotqa": "hotpotqa_eval",
            "triviaqa": "triviaqa_eval",
        }
        resolved_name: str = aliases.get(dataset_name, dataset_name)

        if resolved_name == "sample":
            return self._parse_sample(filepath)
        elif resolved_name == "rag_domain":
            return self._parse_rag_domain(filepath)
        elif resolved_name in ("hotpotqa_eval", "triviaqa_eval"):


            return self._parse_standard_eval(filepath, resolved_name)
        else:
            raise ValueError(f"Parser no implementado para '{dataset_name}'")

    @staticmethod
    def _parse_standard_eval(filepath: Path, dataset_name: str) -> list[EvalSample]:

        with open(filepath, "r", encoding="utf-8") as f:
            data: list[dict[str, Any]] = json.load(f)

        samples: list[EvalSample] = []
        for item in data:

            context: str = item.get("context", "")


            supporting: list[str] = item.get("supporting_titles", [])
            if supporting and not context:

                context = f"[Documentos de soporte: {', '.join(supporting)}]"

            samples.append(
                EvalSample(
                    question=item["question"],
                    answer=item["answer"],
                    context=context,
                    source=item.get("source", dataset_name),
                )
            )

        logger.info(
            "Dataset '%s' parseado: %d muestras",
            dataset_name,
            len(samples),
        )
        return samples

    @staticmethod
    def _parse_sample(filepath: Path) -> list[EvalSample]:

        with open(filepath, "r", encoding="utf-8") as f:
            data: list[dict[str, str]] = json.load(f)

        samples: list[EvalSample] = []
        for item in data:
            samples.append(
                EvalSample(
                    question=item["question"],
                    answer=item["answer"],
                    context=item.get("context", ""),
                    source=item.get("source", "sample"),
                )
            )
        return samples

    @staticmethod
    def _parse_rag_domain(filepath: Path) -> list[EvalSample]:

        with open(filepath, "r", encoding="utf-8") as f:
            data: list[dict[str, str]] = json.load(f)
        samples: list[EvalSample] = []
        for item in data:
            samples.append(
                EvalSample(
                    question=item["question"],
                    answer=item["answer"],
                    context=item.get("context", ""),
                    source=item.get("source_file", item.get("source", "rag_domain")),
                )
            )
        return samples
