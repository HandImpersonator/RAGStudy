from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
import tarfile
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlretrieve


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger: logging.Logger = logging.getLogger(__name__)


_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
CORPUS_DIR: Path = _PROJECT_ROOT / "data" / "corpus"
EVAL_DIR: Path = _PROJECT_ROOT / "data" / "eval"
EXTERNAL_DIR: Path = _PROJECT_ROOT / "data" / "external"


TRIVIAQA_MAX_SAMPLES: int = 1000
HOTPOTQA_MAX_SAMPLES: int = -1


TRIVIAQA_DEV_URL: str = (
    "https://nlp.cs.washington.edu/triviaqa/data/triviaqa-rc.tar.gz"
)


HOTPOTQA_DEV_URL: str = (
    "http://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json"
)


def slugify(text: str, max_len: int = 60) -> str:

    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:max_len]


def save_eval_dataset(
    qa_pairs: list[dict[str, str | list[str]]],
    output_path: Path,
    source_name: str,
) -> None:

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(qa_pairs, fh, ensure_ascii=False, indent=2)

    size_kb: float = output_path.stat().st_size / 1024
    logger.info(
        "Guardado %s: %d pares QA en %s (%.1f KB)",
        source_name,
        len(qa_pairs),
        output_path,
        size_kb,
    )


def download_file(url: str, dest: Path, description: str) -> bool:

    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists():
        logger.info("Ya existe en caché: %s", dest.name)
        return True

    logger.info("Descargando %s desde %s ...", description, url)

    def _progress(block_num: int, block_size: int, total_size: int) -> None:
        if total_size > 0 and block_num % 100 == 0:
            downloaded: float = block_num * block_size / (1024 * 1024)
            total: float = total_size / (1024 * 1024)
            logger.info("  %.1f / %.1f MB", downloaded, total)

    try:
        urlretrieve(url, str(dest), reporthook=_progress)
        logger.info("Descarga completada: %s (%.1f MB)", dest.name, dest.stat().st_size / (1024 * 1024))
        return True
    except URLError as exc:
        logger.error("Error de red al descargar %s: %s", description, exc)
        if dest.exists():
            dest.unlink()
        return False
    except OSError as exc:
        logger.error("Error de sistema de archivos al guardar %s: %s", dest, exc)
        return False


def process_triviaqa(
    max_samples: int = TRIVIAQA_MAX_SAMPLES,
) -> list[dict[str, str | list[str]]]:

    tarball: Path = EXTERNAL_DIR / "triviaqa-rc.tar.gz"


    extracted_qa_dir: Path = EXTERNAL_DIR / "qa"
    extracted_evidence_dir: Path = EXTERNAL_DIR / "evidence" / "wikipedia"


    if not tarball.exists():
        ok: bool = download_file(TRIVIAQA_DEV_URL, tarball, "TriviaQA rc")
        if not ok:
            logger.error("No se pudo descargar TriviaQA.")
            return []


    if not extracted_qa_dir.exists():
        logger.info("Extrayendo TriviaQA en %s ...", EXTERNAL_DIR)
        try:
            with tarfile.open(tarball, "r:gz") as tf:
                tf.extractall(path=EXTERNAL_DIR)
            logger.info("Extracción completada. qa/ en %s", EXTERNAL_DIR)
        except tarfile.TarError as exc:
            logger.error("Error al extraer TriviaQA: %s", exc)
            return []


    dev_json: Path | None = None
    for candidate in [
        extracted_qa_dir / "wikipedia-dev.json",
        EXTERNAL_DIR / "qa" / "wikipedia-dev.json",
    ]:
        if candidate.exists():
            dev_json = candidate
            break

    if dev_json is None:

        found: list[Path] = list(EXTERNAL_DIR.rglob("wikipedia-dev.json"))
        if found:
            dev_json = found[0]
            logger.info("wikipedia-dev.json encontrado en: %s", dev_json)

    if dev_json is None:
        logger.error(
            "No se encontró wikipedia-dev.json en %s. "
            "Comprueba que el tarball se extrajo correctamente.",
            EXTERNAL_DIR,
        )
        return []

    logger.info("Procesando TriviaQA desde %s ...", dev_json)

    try:
        with open(dev_json, encoding="utf-8") as fh:
            data: dict = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Error leyendo %s: %s", dev_json, exc)
        return []

    qa_pairs: list[dict[str, str | list[str]]] = []
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)

    for item in data.get("Data", []):
        if len(qa_pairs) >= max_samples:
            break

        question: str = item.get("Question", "").strip()
        if not question:
            continue


        answer_obj: dict = item.get("Answer", {})
        normalized_answer: str = answer_obj.get("NormalizedValue", "").strip()
        answer_aliases: list[str] = answer_obj.get("NormalizedAliases", [])

        if not normalized_answer:
            continue


        evidence_text: str = ""
        evidence_source: str = ""


        for page in item.get("EntityPages", []):
            filename: str = page.get("Filename", "")
            if filename:
                evidence_file: Path | None = None
                for candidate_dir in [
                    extracted_evidence_dir,
                    EXTERNAL_DIR / "evidence" / "wikipedia",
                ]:
                    candidate_path: Path = candidate_dir / filename
                    if candidate_path.exists():
                        evidence_file = candidate_path
                        break

                if evidence_file and evidence_file.exists():
                    try:
                        raw: str = evidence_file.read_text(encoding="utf-8", errors="replace")

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


        question_id: str = item.get("QuestionId", slugify(question, 40))


        if evidence_text:
            corpus_filename: str = f"triviaqa_{slugify(question_id, 50)}.md"
            corpus_path: Path = CORPUS_DIR / corpus_filename

            if not corpus_path.exists():
                md_content: str = (
                    f"# TriviaQA: {question}\n\n"
                    f"**Fuente**: {evidence_source}\n\n"
                    f"{evidence_text}\n"
                )
                try:
                    corpus_path.write_text(md_content, encoding="utf-8")
                except OSError as exc:
                    logger.warning("No se pudo guardar corpus: %s: %s", corpus_filename, exc)
        else:
            corpus_filename = ""

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

    logger.info(
        "TriviaQA: procesados %d pares QA (máximo solicitado: %d)",
        len(qa_pairs),
        max_samples,
    )
    return qa_pairs


def short_hash(text: str, length: int = 10) -> str:

    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:length]


def make_unique_hotpotqa_filename(
    title: str,
    title_to_filename: dict[str, str],
    filename_to_title: dict[str, str],
) -> str:

    if title in title_to_filename:
        return title_to_filename[title]

    base_slug: str = slugify(title, 80)
    if not base_slug:
        base_slug = f"untitled_{short_hash(title)}"

    filename: str = f"hotpotqa_{base_slug}.md"

    existing_title: str | None = filename_to_title.get(filename)
    if existing_title is not None and existing_title != title:
        filename = f"hotpotqa_{base_slug}_{short_hash(title)}.md"

    title_to_filename[title] = filename
    filename_to_title[filename] = title
    return filename


def process_hotpotqa(
    max_samples: int = HOTPOTQA_MAX_SAMPLES,
) -> list[dict[str, str | list[str]]]:

    hotpot_file: Path = EXTERNAL_DIR / "hotpot_dev_distractor_v1.json"

    if not hotpot_file.exists():
        ok: bool = download_file(
            HOTPOTQA_DEV_URL,
            hotpot_file,
            "HotpotQA dev distractor",
        )
        if not ok:
            logger.error("No se pudo descargar HotpotQA.")
            return []

    logger.info("Procesando HotpotQA distractor desde %s ...", hotpot_file)

    try:
        with open(hotpot_file, encoding="utf-8") as fh:
            data: list[dict] = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Error leyendo HotpotQA: %s", exc)
        return []

    qa_pairs: list[dict[str, str | list[str]]] = []
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)


    title_to_filename: dict[str, str] = {}
    filename_to_title: dict[str, str] = {}

    corpus_written: int = 0
    corpus_reused: int = 0
    skipped_missing_support: int = 0

    for item in data:
        question: str = item.get("question", "").strip()
        answer: str = item.get("answer", "").strip()
        question_id: str = item.get("_id", slugify(question, 40))

        if not question or not answer:
            continue


        context_by_title: dict[str, list[str]] = {}

        for title_sentences in item.get("context", []):
            if not isinstance(title_sentences, list) or len(title_sentences) != 2:
                continue

            title: str = str(title_sentences[0]).strip()
            sentences_raw = title_sentences[1]

            if not title or not isinstance(sentences_raw, list):
                continue

            sentences: list[str] = [str(sentence) for sentence in sentences_raw]
            context_by_title[title] = sentences

        if not context_by_title:
            continue


        supporting_titles: list[str] = []
        seen_supporting_titles: set[str] = set()

        for sf in item.get("supporting_facts", []):
            if not isinstance(sf, list) or not sf:
                continue

            title = str(sf[0]).strip()
            if title and title not in seen_supporting_titles:
                supporting_titles.append(title)
                seen_supporting_titles.add(title)

        missing_support_titles: list[str] = [
            title for title in supporting_titles if title not in context_by_title
        ]

        if missing_support_titles:
            skipped_missing_support += 1
            logger.warning(
                "HotpotQA item %s omitido: faltan títulos soporte en context: %s",
                question_id,
                missing_support_titles,
            )
            continue


        all_context_corpus_files: list[str] = []

        for title, sentences in context_by_title.items():
            passage: str = " ".join(sentences).strip()
            if not passage:
                continue

            corpus_filename: str = make_unique_hotpotqa_filename(
                title=title,
                title_to_filename=title_to_filename,
                filename_to_title=filename_to_title,
            )
            corpus_path: Path = CORPUS_DIR / corpus_filename
            all_context_corpus_files.append(corpus_filename)

            if corpus_path.exists():
                corpus_reused += 1
                continue

            md_content: str = (
                f"# {title}\n\n"
                f"**Dataset**: HotpotQA dev distractor\n\n"
                f"{passage}\n"
            )

            try:
                corpus_path.write_text(md_content, encoding="utf-8")
                corpus_written += 1
            except OSError as exc:
                logger.warning(
                    "No se pudo guardar corpus HotpotQA: %s: %s",
                    corpus_filename,
                    exc,
                )


        supporting_corpus_files: list[str] = [
            make_unique_hotpotqa_filename(
                title=title,
                title_to_filename=title_to_filename,
                filename_to_title=filename_to_title,
            )
            for title in supporting_titles
        ]


        if max_samples > 0 and len(qa_pairs) >= max_samples:
            continue

        context_parts: list[str] = []
        for title in supporting_titles:
            passage = " ".join(context_by_title[title]).strip()
            context_parts.append(f"**{title}**: {passage}")

        combined_context: str = "\n\n".join(context_parts)

        qa_pairs.append(
            {
                "question": question,
                "answer": answer,
                "answer_aliases": [answer],
                "context": combined_context[:1200],
                "supporting_titles": supporting_titles,
                "supporting_corpus_files": supporting_corpus_files,
                "corpus_files": all_context_corpus_files,
                "source": f"hotpotqa_{question_id}",
                "topic": "hotpotqa",
            }
        )

    logger.info(
        "HotpotQA: eval generados=%d, corpus escritos=%d, corpus reutilizados=%d, items omitidos por soporte faltante=%d",
        len(qa_pairs),
        corpus_written,
        corpus_reused,
        skipped_missing_support,
    )

    return qa_pairs


def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "Descarga benchmarks RAG estándar con ground truth preexistente. "
            "Opciones: triviaqa, hotpotqa, all."
        )
    )
    parser.add_argument(
        "--source",
        choices=["triviaqa", "hotpotqa", "all"],
        default="all",
        help="Dataset a descargar (default: all)",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=0,
        help="Límite de muestras (0 = usar valores por defecto del script)",
    )
    return parser.parse_args()


def main() -> None:

    args: argparse.Namespace = parse_args()


    triviaqa_limit: int = args.max_samples if args.max_samples > 0 else TRIVIAQA_MAX_SAMPLES
    hotpotqa_limit: int = args.max_samples if args.max_samples > 0 else HOTPOTQA_MAX_SAMPLES

    sources: set[str] = (
        {"triviaqa", "hotpotqa"} if args.source == "all" else {args.source}
    )

    if "triviaqa" in sources:
        qa: list[dict[str, str | list[str]]] = process_triviaqa(triviaqa_limit)
        if qa:
            save_eval_dataset(qa, EVAL_DIR / "triviaqa_eval.json", "TriviaQA")
        else:
            logger.warning(
                "TriviaQA: sin datos. Verificar descarga en %s/triviaqa-rc.tar.gz",
                EXTERNAL_DIR,
            )


    if "hotpotqa" in sources:
        qa = process_hotpotqa(hotpotqa_limit)
        if qa:
            save_eval_dataset(qa, EVAL_DIR / "hotpotqa_eval.json", "HotpotQA")
        else:
            logger.warning("HotpotQA: sin datos.")

    logger.info("Proceso completado.")


if __name__ == "__main__":
    main()
