# Resumen de evaluación `run_20260517_184154_multi_qa_mini_bge_reranker_0b9bd05c`

- Inicio: `2026-05-17T18:41:54`
- Fin: `2026-05-22T04:15:20`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `llama3_8b__multi-qa-mini__bge-reranker`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 70.0 | 0.0 | 333.8 |
| `baseline_k` | completed | 10 | 50.0 | 50.0 | 18986.4 |
| `baseline_k_grounded` | completed | 10 | 70.0 | 70.0 | 18900.4 |
| `baseline_k_rr` | completed | 10 | 60.0 | 50.0 | 15641.2 |
| `baseline_k_rr_grounded` | completed | 10 | 90.0 | 90.0 | 15721.3 |
| `baseline_s` | completed | 10 | 70.0 | 70.0 | 1148.6 |
| `baseline_s_grounded` | completed | 10 | 70.0 | 90.0 | 1061.6 |
| `baseline_s_rr` | completed | 10 | 70.0 | 80.0 | 1298.4 |
| `baseline_s_rr_grounded` | completed | 10 | 90.0 | 80.0 | 1347.7 |
| `optimized_k` | completed | 10 | 30.0 | 50.0 | 33387.6 |
| `optimized_k_grounded` | completed | 10 | 100.0 | 100.0 | 33048.1 |
| `optimized_k_rr` | completed | 10 | 60.0 | 100.0 | 39931.5 |
| `optimized_k_rr_grounded` | completed | 10 | 100.0 | 100.0 | 39673.7 |
| `optimized_s` | completed | 10 | 80.0 | 80.0 | 1442.1 |
| `optimized_s_grounded` | completed | 10 | 80.0 | 90.0 | 1381.1 |
| `optimized_s_rr` | completed | 10 | 70.0 | 69.0 | 1552.7 |
| `optimized_s_rr_grounded` | completed | 10 | 70.0 | 70.0 | 1569.9 |
