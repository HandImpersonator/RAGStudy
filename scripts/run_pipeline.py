from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline import RAGPipeline, PIPELINE_CONFIGS, PipelineResult


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger: logging.Logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Pipeline RAG para evaluación de arquitecturas",
    )
    parser.add_argument(
        "--config",
        type=int,
        default=1,
        choices=[1, 2, 3, 4, 5, 6, 7, 8, 9],
        help=(
            "Configuración del pipeline: "
            "1=no_rag, 2=baseline_k, 3=baseline_s, "
            "4=baseline_k_rr, 5=baseline_s_rr, "
            "6=optimized_k, 7=optimized_k_rr, "
            "8=optimized_s, 9=optimized_s_rr"
        ),
    )
    parser.add_argument(
        "--query",
        type=str,
        default="¿Qué es RAG?",
        help="Pregunta para el pipeline",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Ejecutar en modo batch con el dataset sample",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=5,
        help="Máximo de samples en modo batch (default: 5)",
    )
    parser.add_argument(
        "--save-log",
        action="store_true",
        help="Guardar resultados en logs/ (formato simple, sin evaluación)",
    )
    parser.add_argument(
        "--cache-index",
        action="store_true",
        help=(
            "Activar persistencia del índice FAISS en disco (data/index_cache/). "
            "En la primera ejecución se construye y guarda. "
            "En ejecuciones posteriores se carga directamente. "
            "Solo aplica a configuraciones con retriever FAISS. "
            "Útil cuando el corpus es grande y el embedding es lento."
        ),
    )
    return parser.parse_args()


def save_results(
    results: list[PipelineResult],
    config_name: str,
) -> Path:

    log_dir: Path = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp: str = time.strftime("%Y%m%d_%H%M%S")
    filename: str = f"{config_name}_{timestamp}.json"
    filepath: Path = log_dir / filename

    data: list[dict] = []
    for r in results:
        data.append({
            "query": r.query,
            "answer": r.answer,
            "contexts": r.contexts,
            "config_name": r.config_name,
            "timings": r.timings,
            "metadata": r.metadata,
        })

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info("Resultados guardados: %s", filepath)
    return filepath


def main() -> int:

    args: argparse.Namespace = parse_args()

    logger.info("=" * 60)
    logger.info("PIPELINE RAG - TFG")
    logger.info("=" * 60)


    config_name: str = RAGPipeline.CONFIG_MAP[args.config]
    config: dict = PIPELINE_CONFIGS[config_name]
    logger.info("Configuración: %s", config_name)
    for key, value in config.items():
        logger.info("  %s: %s", key, value)

    try:

        pipeline: RAGPipeline = RAGPipeline(config_option=args.config)


        if config_name != "no_rag":
            corpus_dir: Path = (
                Path(__file__).resolve().parent.parent / "data" / "corpus"
            )
            logger.info("Construyendo índice desde %s...", corpus_dir)
            num_chunks: int = pipeline.build_index(
                corpus_dir=corpus_dir,
                persist_index=args.cache_index,
            )
            logger.info("Índice construido: %d chunks", num_chunks)

        if args.batch:

            from src.dataset_manager import DatasetManager

            manager: DatasetManager = DatasetManager()
            samples = manager.load("sample", max_samples=args.max_samples)
            queries: list[str] = [s.question for s in samples]

            logger.info("Modo batch: %d consultas", len(queries))
            results: list[PipelineResult] = pipeline.run_batch(queries)


            for i, result in enumerate(results):
                logger.info("-" * 40)
                logger.info("Q%d: %s", i + 1, result.query[:80])
                logger.info("A%d: %s", i + 1, result.answer[:200])
                if result.timings:
                    logger.info(
                        "   Total: %.0f ms",
                        result.timings.get("total_pipeline_ms", 0),
                    )

            if args.save_log:
                save_results(results, config_name)
        else:

            result: PipelineResult = pipeline.run(query=args.query)

            logger.info("=" * 60)
            logger.info("RESULTADO")
            logger.info("=" * 60)
            logger.info("Pregunta: %s", result.query)
            logger.info("Respuesta: %s", result.answer)
            logger.info("Contextos usados: %d", len(result.contexts))
            for key, val in result.timings.items():
                logger.info("  %s: %.1f ms", key, val)

            if args.save_log:
                save_results([result], config_name)

        return 0

    except ConnectionError as e:
        logger.error(
            "Error de conexión con el LLM: %s\n"
            "Asegúrate de que el servidor remoto está accesible "
            "y el túnel SSH está abierto.",
            e,
        )
        return 1
    except FileNotFoundError as e:
        logger.error("Archivo o directorio no encontrado: %s", e)
        return 1
    except ImportError as e:
        logger.error(
            "Dependencia no instalada: %s\n"
            "Ejecuta: pip install -r requirements.txt",
            e,
        )
        return 1
    except (RuntimeError, ValueError) as e:
        logger.error("Error en pipeline: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
