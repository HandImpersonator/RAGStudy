from __future__ import annotations

import sys
import logging
from pathlib import Path
from typing import Any


_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

logging.basicConfig(level=logging.WARNING)
logger: logging.Logger = logging.getLogger(__name__)


SAMPLE_TEXT: str = """
The Battle of Marathon took place in 490 BC.
It was a pivotal conflict between Athens and the Persian Empire.
The Athenians, led by Miltiades, defeated a superior Persian force.

The victory at Marathon had long-term consequences for Greek history.
It boosted Athenian confidence and demonstrated that Persia could be defeated.
The messenger Pheidippides reportedly ran from Marathon to Athens to announce the victory.

Later, in 480 BC, the Persians returned under Xerxes.
The battles of Thermopylae and Salamis followed in quick succession.
The Greek city-states eventually repelled the Persian invasion.
"""

SAMPLE_DOC_SOURCE: str = "ancient_battles.txt"


def test_chunk_source_metadata() -> bool:

    from src.chunking import FixedChunker, SemanticChunker

    passed: bool = True

    for ChunkerClass, method_name in [(FixedChunker, "fixed"), (SemanticChunker, "semantic")]:
        chunker = ChunkerClass(chunk_size=200, overlap=50)
        chunks = chunker.chunk(text=SAMPLE_TEXT, doc_source=SAMPLE_DOC_SOURCE)

        if not chunks:
            print(f"  FAIL [{method_name}]: No chunks produced")
            passed = False
            continue

        prev_index: int = -1
        seen_global_ids: set[str] = set()

        for chunk in chunks:

            if not chunk.chunk_global_id:
                print(f"  FAIL [{method_name}]: chunk_global_id is empty")
                passed = False
                continue

            if chunk.chunk_global_id in seen_global_ids:
                print(f"  FAIL [{method_name}]: duplicate chunk_global_id: {chunk.chunk_global_id}")
                passed = False
            seen_global_ids.add(chunk.chunk_global_id)


            if chunk.doc_id != SAMPLE_DOC_SOURCE:
                print(f"  FAIL [{method_name}]: doc_id mismatch: {chunk.doc_id!r}")
                passed = False

            if chunk.doc_source != SAMPLE_DOC_SOURCE:
                print(f"  FAIL [{method_name}]: doc_source mismatch: {chunk.doc_source!r}")
                passed = False


            if chunk.chunk_index_in_doc != prev_index + 1:
                print(f"  FAIL [{method_name}]: expected index {prev_index + 1}, got {chunk.chunk_index_in_doc}")
                passed = False
            prev_index = chunk.chunk_index_in_doc


            if chunk.chunker_method != method_name:
                print(f"  FAIL [{method_name}]: chunker_method={chunk.chunker_method!r}, expected {method_name!r}")
                passed = False


            required_meta_fields = ["doc_source", "chunk_global_id", "chunk_index_in_doc", "chunker_method"]
            for field in required_meta_fields:
                if field not in chunk.metadata:
                    print(f"  FAIL [{method_name}]: metadata missing field: {field!r}")
                    passed = False


            if chunk.metadata.get("chunk_global_id") != chunk.chunk_global_id:
                print(f"  FAIL [{method_name}]: metadata.chunk_global_id != chunk.chunk_global_id")
                passed = False

        if passed:
            print(f"  PASS [chunk_source_metadata / {method_name}]: {len(chunks)} chunks, all fields OK")

    return passed


def test_metadata_survives_retrieval() -> bool:

    import numpy as np
    from src.chunking import FixedChunker
    from src.retrieval import FAISSRetriever, BM25Retriever

    passed: bool = True

    chunker = FixedChunker(chunk_size=200, overlap=50)
    chunks = chunker.chunk(text=SAMPLE_TEXT, doc_source=SAMPLE_DOC_SOURCE)
    texts = [c.text for c in chunks]
    metadatas = [dict(c.metadata) for c in chunks]


    bm25 = BM25Retriever(top_k=3)
    dummy_embeddings = np.zeros((len(texts), 1), dtype=np.float32)
    bm25.index(embeddings=dummy_embeddings, texts=texts, metadatas=metadatas)
    bm25_results = bm25.retrieve(query_text="Marathon battle Athenians")

    if not bm25_results:
        print("  FAIL [metadata_survives_retrieval / BM25]: No results")
        return False

    for r in bm25_results:
        if not r.chunk_global_id:
            print(f"  FAIL [BM25]: chunk_global_id empty in result")
            passed = False
        if r.source_file != SAMPLE_DOC_SOURCE and r.doc_id != SAMPLE_DOC_SOURCE:
            print(f"  FAIL [BM25]: source_file={r.source_file!r}, doc_id={r.doc_id!r} don't match {SAMPLE_DOC_SOURCE!r}")
            passed = False
        if r.retrieval_score_type != "bm25":
            print(f"  FAIL [BM25]: retrieval_score_type={r.retrieval_score_type!r}, expected 'bm25'")
            passed = False

    if passed:
        print(f"  PASS [metadata_survives_retrieval / BM25]: {len(bm25_results)} results, all fields OK")


    try:
        import faiss
        embeddings = np.random.randn(len(texts), 32).astype(np.float32)
        faiss_retriever = FAISSRetriever(top_k=3)
        faiss_retriever.index(embeddings=embeddings, texts=texts, metadatas=metadatas)
        query_emb = np.random.randn(32).astype(np.float32)
        faiss_results = faiss_retriever.retrieve(query_embedding=query_emb)

        for r in faiss_results:
            if not r.chunk_global_id:
                print("  FAIL [FAISS]: chunk_global_id empty")
                passed = False
            if r.retrieval_score_type != "cosine_similarity":
                print(f"  FAIL [FAISS]: retrieval_score_type={r.retrieval_score_type!r}")
                passed = False

        if passed:
            print(f"  PASS [metadata_survives_retrieval / FAISS]: {len(faiss_results)} results, all fields OK")
    except ImportError:
        print("  SKIP [metadata_survives_retrieval / FAISS]: faiss-cpu not installed")

    return passed


def test_metadata_survives_reranking() -> bool:

    import numpy as np
    from src.chunking import FixedChunker
    from src.retrieval import BM25Retriever
    from src.reranking import NoReranker

    passed: bool = True

    chunker = FixedChunker(chunk_size=200, overlap=50)
    chunks = chunker.chunk(text=SAMPLE_TEXT, doc_source=SAMPLE_DOC_SOURCE)
    texts = [c.text for c in chunks]
    metadatas = [dict(c.metadata) for c in chunks]

    bm25 = BM25Retriever(top_k=min(len(chunks), 5))
    bm25.index(embeddings=np.zeros((len(texts), 1), dtype=np.float32), texts=texts, metadatas=metadatas)
    results = bm25.retrieve(query_text="Marathon battle 490 BC")

    if not results:
        print("  FAIL [metadata_survives_reranking]: No retrieval results to test")
        return False

    reranker = NoReranker(top_n=min(3, len(results)))
    reranked = reranker.rerank_results(query="Marathon battle", results=results)

    for r, orig in zip(reranked, results[:len(reranked)]):
        if r.chunk_global_id != orig.chunk_global_id:
            print(f"  FAIL [reranking]: chunk_global_id changed: {orig.chunk_global_id!r} -> {r.chunk_global_id!r}")
            passed = False
        if r.reranker_score is None:
            print(f"  FAIL [reranking]: reranker_score is None for chunk {r.chunk_global_id!r}")
            passed = False
        if r.reranker_score_type != "pass_through":
            print(f"  FAIL [reranking]: reranker_score_type={r.reranker_score_type!r}, expected 'pass_through'")
            passed = False

    if passed:
        print(f"  PASS [metadata_survives_reranking]: {len(reranked)} chunks, all fields preserved")
    return passed


def test_source_info_and_labels() -> bool:

    import numpy as np
    from src.chunking import FixedChunker
    from src.retrieval import BM25Retriever
    from src.reranking import NoReranker
    from src.prompts import PromptBuilder, SourceInfo, source_info_from_result

    passed: bool = True

    chunker = FixedChunker(chunk_size=300, overlap=50)
    chunks = chunker.chunk(text=SAMPLE_TEXT, doc_source=SAMPLE_DOC_SOURCE)
    texts = [c.text for c in chunks]
    metadatas = [dict(c.metadata) for c in chunks]

    bm25 = BM25Retriever(top_k=3)
    bm25.index(embeddings=np.zeros((len(texts), 1), dtype=np.float32), texts=texts, metadatas=metadatas)
    results = bm25.retrieve(query_text="battle")
    reranker = NoReranker(top_n=3)
    reranked = reranker.rerank_results(query="battle", results=results)

    if not reranked:
        print("  FAIL [source_labels]: no reranked results")
        return False


    builder_sourced = PromptBuilder(version="grounded_sourced")
    prompt_with_sources, sources = builder_sourced.build_with_sources(
        question="Who fought at Marathon?",
        results=reranked,
    )

    if not sources:
        print("  FAIL [source_labels]: sources list is empty")
        passed = False
    else:
        for i, src in enumerate(sources):
            expected_sid = f"S{i + 1}"
            if src.source_id != expected_sid:
                print(f"  FAIL [source_labels]: source_id={src.source_id!r}, expected {expected_sid!r}")
                passed = False
            if not src.chunk_global_id:
                print(f"  FAIL [source_labels]: chunk_global_id empty for {src.source_id}")
                passed = False
            if src.source_file != SAMPLE_DOC_SOURCE:
                print(f"  FAIL [source_labels]: source_file={src.source_file!r}")
                passed = False
            if src.text_chars <= 0:
                print(f"  FAIL [source_labels]: text_chars={src.text_chars}")
                passed = False


    if "[S1]" not in prompt_with_sources:
        print("  FAIL [source_labels]: [S1] not found in grounded_sourced prompt")
        passed = False


    builder_basic = PromptBuilder(version="basic")
    prompt_basic = builder_basic.build(
        question="Who fought at Marathon?",
        contexts=[r.text for r in reranked],
    )
    if "[S1]" in prompt_basic:
        print("  FAIL [source_labels]: [S1] found in basic prompt (should not be there)")
        passed = False


    if sources:
        src_dict = sources[0].to_dict()
        required_keys = [
            "source_id", "chunk_global_id", "doc_id", "source_file",
            "chunk_index_in_doc", "chunker_method", "retrieval_score",
            "retrieval_score_type", "reranker_score", "reranker_score_type",
            "text_chars", "text_preview",
        ]
        for key in required_keys:
            if key not in src_dict:
                print(f"  FAIL [source_labels]: SourceInfo.to_dict() missing key: {key!r}")
                passed = False

    if passed:
        print(f"  PASS [source_info_and_labels]: {len(sources)} sources, [S1] in grounded_sourced, absent in basic")
    return passed


def test_token_budget_mode() -> bool:

    import numpy as np
    from src.chunking import FixedChunker
    from src.retrieval import BM25Retriever
    from src.reranking import NoReranker
    from src.pipeline import RAGPipeline

    passed: bool = True


    pipeline = RAGPipeline.__new__(RAGPipeline)
    pipeline.config = {
        "context_selection_mode": "token_budget",
        "context_token_budget": 100,
    }
    pipeline._doc_chunk_list = {}


    chunks_200: list[Any] = []
    from src.retrieval import RetrievalResult
    for i in range(5):
        text = "A" * 200
        r = RetrievalResult(
            text=text, score=1.0 - i * 0.1, chunk_id=i, metadata={},
            chunk_global_id=f"doc.txt::chunk::{i:04d}",
            doc_id="doc.txt", source_file="doc.txt",
            chunk_index_in_doc=i, retrieval_score_type="bm25",
            reranker_score=None, reranker_score_type="pass_through",
        )
        chunks_200.append(r)


    selected = pipeline._select_by_token_budget(chunks_200, budget=100)


    used_chars = sum(len(r.text) for r in selected)
    used_tokens = used_chars // 4

    if used_tokens > 110:
        print(f"  FAIL [token_budget]: used_tokens={used_tokens}, budget=100 exceeded by >10%")
        passed = False
    if len(selected) == 0:
        print("  FAIL [token_budget]: no chunks selected (budget too small)")
        passed = False

    if passed:
        print(f"  PASS [token_budget]: {len(selected)} chunks selected, ~{used_tokens} tokens (budget=100)")
    return passed


def test_neighbor_expansion() -> bool:

    import numpy as np
    from src.chunking import FixedChunker
    from src.pipeline import RAGPipeline
    from src.retrieval import RetrievalResult

    passed: bool = True


    chunker = FixedChunker(chunk_size=100, overlap=0)
    long_text = " ".join([f"Sentence {i} about topic X." for i in range(20)])
    chunks = chunker.chunk(text=long_text, doc_source=SAMPLE_DOC_SOURCE)


    pipeline = RAGPipeline.__new__(RAGPipeline)
    pipeline.config = {
        "context_selection_mode": "token_budget",
        "context_token_budget": 2000,
    }
    pipeline._doc_chunk_list = {SAMPLE_DOC_SOURCE: chunks}
    pipeline._chunk_lookup = {c.chunk_global_id: c for c in chunks}


    mid_chunk = chunks[2]
    base_result = RetrievalResult(
        text=mid_chunk.text,
        score=0.9, chunk_id=mid_chunk.chunk_id, metadata=mid_chunk.metadata,
        chunk_global_id=mid_chunk.chunk_global_id,
        doc_id=mid_chunk.doc_id, source_file=mid_chunk.doc_source,
        chunk_index_in_doc=mid_chunk.chunk_index_in_doc,
        retrieval_score_type="bm25",
        reranker_score=0.9, reranker_score_type="pass_through",
    )


    expanded = pipeline._apply_neighbor_expansion([base_result], budget=2000)


    expanded_ids = {r.chunk_global_id for r in expanded}
    expected_ids = {
        chunks[1].chunk_global_id,
        chunks[2].chunk_global_id,
        chunks[3].chunk_global_id,
    }

    if expanded_ids != expected_ids:
        print(f"  FAIL [neighbor_expansion]: got {expanded_ids}, expected {expected_ids}")
        passed = False


    if len(expanded) != len(expanded_ids):
        print(f"  FAIL [neighbor_expansion]: duplicates found ({len(expanded)} results, {len(expanded_ids)} unique)")
        passed = False


    for r in expanded:
        if r.chunk_global_id == base_result.chunk_global_id:
            if r.reranker_score != 0.9:
                print(f"  FAIL [neighbor_expansion]: base result score changed")
                passed = False

    if passed:
        print(f"  PASS [neighbor_expansion]: {len(expanded)} chunks (prev+base+next), no duplicates")
    return passed


def test_pipeline_result_has_sources() -> bool:

    from src.pipeline import PipelineResult

    passed: bool = True

    result = PipelineResult(
        query="test",
        answer="test answer",
        contexts=["context 1"],
        config_name="baseline_s",
        sources=[{"source_id": "S1", "chunk_global_id": "doc.txt::chunk::0000"}],
    )

    if not hasattr(result, "sources"):
        print("  FAIL [pipeline_result_sources]: PipelineResult has no 'sources' attribute")
        passed = False
    elif not result.sources:
        print("  FAIL [pipeline_result_sources]: sources list is empty")
        passed = False
    elif result.sources[0].get("source_id") != "S1":
        print(f"  FAIL [pipeline_result_sources]: sources[0].source_id={result.sources[0].get('source_id')!r}")
        passed = False

    if passed:
        print(f"  PASS [pipeline_result_sources]: sources field present and populated")
    return passed


def main() -> int:

    print("=" * 60)
    print("Test de Trazabilidad de Fuentes - RAG Pipeline")
    print("=" * 60)

    tests = [
        ("1. Chunk source metadata", test_chunk_source_metadata),
        ("2. Metadata survives retrieval", test_metadata_survives_retrieval),
        ("3. Metadata survives reranking", test_metadata_survives_reranking),
        ("4. SourceInfo and prompt labels", test_source_info_and_labels),
        ("5. Token budget mode", test_token_budget_mode),
        ("6. Neighbor expansion", test_neighbor_expansion),
        ("7. PipelineResult has sources", test_pipeline_result_has_sources),
    ]

    results: list[tuple[str, bool]] = []
    for name, test_fn in tests:
        print(f"\n[{name}]")
        try:
            ok: bool = test_fn()
            results.append((name, ok))
        except Exception as exc:
            print(f"  ERROR: {exc}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    print("\n" + "=" * 60)
    print("Resultados:")
    all_passed: bool = True
    for name, ok in results:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")
        if not ok:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("Todos los tests pasaron.")
    else:
        failed = sum(1 for _, ok in results if not ok)
        print(f"{failed}/{len(results)} tests fallaron.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
