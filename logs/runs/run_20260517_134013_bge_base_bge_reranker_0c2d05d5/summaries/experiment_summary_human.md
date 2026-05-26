# Resumen de evaluación `run_20260517_134013_bge_base_bge_reranker_0c2d05d5`

- Inicio: `2026-05-17T13:40:13`
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
| `no_rag` | completed | 10 | 70.0 | 0.0 | 296.5 |
| `baseline_k` | completed | 10 | 90.0 | 76.0 | 18752.7 |
| `baseline_k_grounded` | completed | 10 | 80.0 | 80.0 | 18607.6 |
| `baseline_k_rr` | completed | 10 | 60.0 | 70.0 | 15435.7 |
| `baseline_k_rr_grounded` | completed | 10 | 80.0 | 100.0 | 15266.7 |
| `baseline_s` | completed | 10 | 60.0 | 80.0 | 1335.1 |
| `baseline_s_grounded` | completed | 10 | 60.0 | 90.0 | 1306.4 |
| `baseline_s_rr` | completed | 10 | 60.0 | 80.0 | 1445.2 |
| `baseline_s_rr_grounded` | completed | 10 | 100.0 | 100.0 | 1360.2 |
| `optimized_k` | completed | 10 | 50.0 | 50.0 | 33030.1 |
| `optimized_k_grounded` | completed | 10 | 100.0 | 99.0 | 32927.7 |
| `optimized_k_rr` | completed | 10 | 50.0 | 50.0 | 39703.9 |
| `optimized_k_rr_grounded` | completed | 10 | 90.0 | 90.0 | 39671.8 |
| `optimized_s` | completed | 10 | 60.0 | 68.0 | 1944.6 |
| `optimized_s_grounded` | completed | 10 | 70.0 | 70.0 | 1930.3 |
| `optimized_s_rr` | completed | 10 | 77.5 | 70.5 | 2144.1 |
| `optimized_s_rr_grounded` | completed | 10 | 80.0 | 100.0 | 2174.9 |
