# Resumen de evaluación `run_20260517_134923_multi_qa_mini_bge_reranker_bcf075e5`

- Inicio: `2026-05-17T13:49:23`
- Fin: `2026-05-22T04:15:20`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `llama3.2_latest__multi-qa-mini__bge-reranker`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 70.0 | 0.0 | 293.3 |
| `baseline_k` | completed | 10 | 76.0 | 68.0 | 18747.0 |
| `baseline_k_grounded` | completed | 10 | 80.0 | 82.0 | 18607.0 |
| `baseline_k_rr` | completed | 10 | 70.0 | 50.0 | 15436.7 |
| `baseline_k_rr_grounded` | completed | 10 | 100.0 | 100.0 | 15267.5 |
| `baseline_s` | completed | 10 | 80.0 | 90.0 | 955.4 |
| `baseline_s_grounded` | completed | 10 | 70.0 | 100.0 | 838.0 |
| `baseline_s_rr` | completed | 10 | 90.0 | 78.0 | 1065.7 |
| `baseline_s_rr_grounded` | completed | 10 | 100.0 | 100.0 | 1051.7 |
| `optimized_k` | completed | 10 | 40.0 | 80.0 | 33025.2 |
| `optimized_k_grounded` | completed | 10 | 100.0 | 98.0 | 32921.9 |
| `optimized_k_rr` | completed | 10 | 70.0 | 80.0 | 39702.1 |
| `optimized_k_rr_grounded` | completed | 10 | 90.0 | 88.0 | 39668.6 |
| `optimized_s` | completed | 10 | 90.0 | 70.0 | 1238.5 |
| `optimized_s_grounded` | completed | 10 | 70.0 | 80.0 | 1140.2 |
| `optimized_s_rr` | completed | 10 | 71.0 | 58.0 | 1497.3 |
| `optimized_s_rr_grounded` | completed | 10 | 70.0 | 80.0 | 1336.9 |
