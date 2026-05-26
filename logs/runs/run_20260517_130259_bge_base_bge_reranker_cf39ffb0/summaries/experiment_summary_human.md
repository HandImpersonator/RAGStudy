# Resumen de evaluación `run_20260517_130259_bge_base_bge_reranker_cf39ffb0`

- Inicio: `2026-05-17T13:02:59`
- Fin: `2026-05-22T04:15:19`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `llama3.2_latest__bge-base__bge-reranker`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 60.0 | 0.0 | 293.0 |
| `baseline_k` | completed | 10 | 50.0 | 80.0 | 18746.0 |
| `baseline_k_grounded` | completed | 10 | 70.0 | 70.0 | 18609.5 |
| `baseline_k_rr` | completed | 10 | 70.0 | 60.0 | 15431.0 |
| `baseline_k_rr_grounded` | completed | 10 | 50.0 | 100.0 | 15261.2 |
| `baseline_s` | completed | 10 | 70.0 | 70.0 | 1327.9 |
| `baseline_s_grounded` | completed | 10 | 80.0 | 90.0 | 1302.9 |
| `baseline_s_rr` | completed | 10 | 80.0 | 80.0 | 1439.9 |
| `baseline_s_rr_grounded` | completed | 10 | 80.0 | 100.0 | 1356.5 |
| `optimized_k` | completed | 10 | 60.0 | 40.0 | 33026.6 |
| `optimized_k_grounded` | completed | 10 | 100.0 | 98.5 | 32918.7 |
| `optimized_k_rr` | completed | 10 | 50.0 | 47.0 | 39699.0 |
| `optimized_k_rr_grounded` | completed | 10 | 40.0 | 87.0 | 39663.8 |
| `optimized_s` | completed | 10 | 60.0 | 60.0 | 1941.0 |
| `optimized_s_grounded` | completed | 10 | 70.0 | 70.0 | 1923.3 |
| `optimized_s_rr` | completed | 10 | 79.0 | 82.0 | 2136.3 |
| `optimized_s_rr_grounded` | completed | 10 | 70.0 | 60.0 | 2169.8 |
