from __future__ import annotations

import argparse
import json
import logging
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger: logging.Logger = logging.getLogger(__name__)


CORPUS_DIR: Path = Path("data/corpus")
EVAL_DIR: Path = Path("data/eval")


@dataclass
class Section:


    heading: str
    level: int
    content: str
    source_file: str


@dataclass
class QATriple:


    question: str
    answer: str
    context: str
    source: str = ""
    topic: str = ""

    def to_dict(self) -> dict[str, str]:

        return {
            "question": self.question,
            "answer": self.answer,
            "context": self.context,
            "source": self.source,
            "topic": self.topic,
        }


TOPIC_MAP: dict[str, str] = {
    "01_retrieval_augmented_generation": "rag",
    "02_alucinaciones_llm": "alucinaciones",
    "03_modelos_lenguaje": "modelos_lenguaje",
    "04_embeddings_vectores": "embeddings",
    "05_bases_datos_vectoriales": "vector_db",
    "06_estrategias_chunking": "chunking",
    "07_prompt_engineering": "prompt_engineering",
    "08_evaluacion_ragas": "evaluacion",
}


def _extract_sentences(text: str, max_n: int = 3) -> str:

    sentences: list[str] = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [
        s.strip()
        for s in sentences
        if len(s.strip()) > 40

        and not s.strip().startswith(("-", "*", "#", "`", "|", "1.", "2."))
        and "```" not in s
    ]
    return " ".join(sentences[:max_n]).strip()


def _clean_heading(heading: str) -> str:

    clean: str = re.sub(r"^[\d.]+\s*", "", heading)
    clean = re.sub(r"[*_`]", "", clean)
    return clean.strip()


def _is_generic_heading(heading: str) -> bool:

    generic_headings: set[str] = {

        "definición", "definicion", "introducción", "introduccion",
        "tipos", "variantes", "ventajas", "desventajas", "limitaciones",
        "causas", "métricas", "metricas", "estrategias", "parámetros",
        "parametros", "configuración", "configuracion", "motivación",
        "motivacion", "arquitectura", "resumen", "conclusión", "conclusion",
        "evaluación", "evaluacion", "resultados", "comparativa", "aplicaciones",
        "usos", "proceso", "flujo", "overview", "background",

        "definición del problema", "definicion del problema",
        "tipos de alucinaciones", "métricas de evaluación",
        "estrategias de mitigación", "causas principales",
        "ventajas y desventajas", "parámetros de generación",
        "limitaciones fundamentales", "medición en entornos experimentales",
    }
    return heading.lower().strip() in generic_headings


def _generate_questions_for_section(
    heading: str,
    content: str,
    topic: str,
) -> list[tuple[str, str]]:


    if _is_generic_heading(heading):
        return []

    content_lower: str = content.lower()
    pairs: list[tuple[str, str]] = []


    answer_short: str = _extract_sentences(content, max_n=2)
    answer_long: str = _extract_sentences(content, max_n=3)

    if not answer_short or len(answer_short) < 30:
        return pairs


    if len(answer_long) > 600:
        answer_long = answer_long[:600].rsplit(" ", 1)[0] + "..."
    if len(answer_short) > 400:
        answer_short = answer_short[:400].rsplit(" ", 1)[0] + "..."


    is_definition: bool = any(w in content_lower[:400] for w in [
        "es una", "es un", "se define", "se denomina", "consiste en",
        "se refiere a", "es el proceso", "es la capacidad", "es una técnica",
        "es una arquitectura", "es un algoritmo",
    ])
    heading_is_concept: bool = any(w in heading.lower() for w in [
        "rag", "embedding", "faiss", "bm25", "retrieval", "chunking",
        "reranking", "transformer", "bert", "llm", "ragas", "ollama",
        "squad", "milvus", "chroma",
    ])
    if is_definition or heading_is_concept:
        pairs.append((f"¿Qué es {heading}?", answer_short))


    has_numbered_steps: bool = bool(re.search(r'\n\s*[1-9]\.\s', content))
    has_flow_words: bool = any(w in content_lower for w in [
        "etapa", "paso", "flujo", "proceso de ", "secuencia", "pipeline",
    ])
    if has_numbered_steps or has_flow_words:
        pairs.append((f"¿Cómo funciona {heading}?", answer_long))
        if has_numbered_steps:
            pairs.append((f"¿Cuáles son las etapas de {heading}?", answer_long))


    if any(w in content_lower for w in ["ventaja", "beneficio", "permite que", "mejora "]):
        pairs.append((f"¿Cuáles son las ventajas de {heading}?", answer_long))


    if any(w in content_lower for w in [
        "limitación", "desventaja", "problema", "riesgo",
        "alucinación", "error", "fallo",
    ]):
        pairs.append((f"¿Cuáles son las limitaciones de {heading}?", answer_long))


    if any(w in content_lower for w in ["tipo", "variante", "estrategia", "método", "enfoque"]):
        pairs.append((f"¿Qué tipos de {heading} existen?", answer_long))


    if any(w in content_lower for w in [
        "métrica", "evalúa", "evalua", "mide ", "score", "precisión",
        "faithfulness", "recall", "f1",
    ]):
        pairs.append((f"¿Cómo se evalúa {heading}?", answer_long))


    if any(w in content_lower for w in ["comparado con", "frente a", "versus", "diferencia entre"]):
        pairs.append((
            f"¿En qué se diferencia {heading} de otras alternativas?",
            answer_long,
        ))


    if not pairs:
        pairs.append((
            f"¿Cuál es el propósito de {heading} en un sistema RAG?",
            answer_short,
        ))


    return pairs[:3]


def parse_markdown_sections(text: str, source_file: str) -> list[Section]:

    lines: list[str] = text.split("\n")
    sections: list[Section] = []
    current_heading: str = ""
    current_level: int = 1
    current_lines: list[str] = []

    for line in lines:
        m: re.Match[str] | None = re.match(r"^(#{1,4})\s+(.+)$", line)
        if m:
            if current_heading and current_lines:
                content: str = "\n".join(current_lines).strip()
                if len(content) > 60:
                    sections.append(Section(
                        heading=current_heading,
                        level=current_level,
                        content=content,
                        source_file=source_file,
                    ))
            current_level = len(m.group(1))
            current_heading = m.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)


    if current_heading and current_lines:
        content = "\n".join(current_lines).strip()
        if len(content) > 60:
            sections.append(Section(
                heading=current_heading,
                level=current_level,
                content=content,
                source_file=source_file,
            ))

    return sections


def generate_domain_eval(corpus_dir: Path = CORPUS_DIR) -> list[QATriple]:

    if not corpus_dir.exists():
        raise FileNotFoundError(f"Directorio no encontrado: {corpus_dir}")

    md_files: list[Path] = sorted(corpus_dir.glob("*.md"))
    if not md_files:
        raise FileNotFoundError(f"No hay archivos .md en {corpus_dir}")

    logger.info("Corpus de dominio: %d archivos", len(md_files))
    all_triples: list[QATriple] = []

    for md_file in md_files:
        text: str = md_file.read_text(encoding="utf-8")
        filename: str = md_file.stem
        topic: str = TOPIC_MAP.get(filename, "general")


        sections: list[Section] = parse_markdown_sections(text, md_file.name)
        logger.info("  %s: %d secciones (tema: %s)", md_file.name, len(sections), topic)

        for section in sections:
            clean: str = _clean_heading(section.heading)
            if not clean or len(clean) < 3:
                continue


            ctx: str = section.content
            if len(ctx) > 2000:
                ctx = ctx[:2000].rsplit(" ", 1)[0] + "..."

            pairs: list[tuple[str, str]] = _generate_questions_for_section(
                heading=clean,
                content=section.content,
                topic=topic,
            )

            for question, answer in pairs:


                if answer.strip() == ctx.strip():
                    logger.debug(
                        "Saltando triple con answer==context en sección '%s'",
                        clean,
                    )
                    continue
                all_triples.append(QATriple(
                    question=question,
                    answer=answer,
                    context=ctx,
                    source=section.source_file,
                    topic=topic,
                ))

    logger.info("Corpus de dominio: %d triples generados", len(all_triples))
    return all_triples


def save_eval(triples: list[QATriple], output_path: Path) -> Path:

    output_path.parent.mkdir(parents=True, exist_ok=True)
    data: list[dict[str, str]] = [t.to_dict() for t in triples]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info("Guardado: %s (%d triples)", output_path, len(data))
    return output_path


def parse_args() -> argparse.Namespace:

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Genera el dataset de evaluación rag_domain a partir del corpus interno",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplo:
  python3 scripts/generate_dataset.py
        """,
    )
    parser.add_argument(
        "--corpus-dir", type=Path, default=CORPUS_DIR,
        help=f"Directorio del corpus (default: {CORPUS_DIR})",
    )
    return parser.parse_args()


def main() -> int:

    args: argparse.Namespace = parse_args()

    logger.info("=" * 60)
    logger.info("GENERADOR DE DATASETS DE EVALUACIÓN RAG (rag_domain)")
    logger.info("=" * 60)
    logger.info("Corpus: %s", args.corpus_dir)

    try:
        triples: list[QATriple] = generate_domain_eval(args.corpus_dir)
    except FileNotFoundError as exc:
        logger.error("Domain eval fallido: %s", exc)
        return 1

    out: Path = save_eval(triples, EVAL_DIR / "rag_domain_eval.json")


    topics: dict[str, int] = {}
    for t in triples:
        topics[t.topic] = topics.get(t.topic, 0) + 1
    for topic, count in sorted(topics.items()):
        logger.info("  %-30s %d triples", topic, count)

    logger.info("\nArchivo generado: %s", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
