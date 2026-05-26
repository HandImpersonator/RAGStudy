# Resumen de evaluación `run_20260517_125943_bge_base_ms_marco_l6_322e12c6`

- Inicio: `2026-05-17T12:59:43`
- Fin: `2026-05-22T04:15:19`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `llama3.2_latest__bge-base__ms-marco-L6`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 70.0 | 0.0 | 296.7 |
| `baseline_k` | completed | 10 | 60.0 | 76.0 | 18748.0 |
| `baseline_k_grounded` | completed | 10 | 80.0 | 80.0 | 18604.8 |
| `baseline_k_rr` | completed | 10 | 60.0 | 80.0 | 15243.6 |
| `baseline_k_rr_grounded` | completed | 10 | 60.0 | 100.0 | 15140.4 |
| `baseline_s` | completed | 10 | 60.0 | 70.0 | 1326.3 |
| `baseline_s_grounded` | completed | 10 | 70.0 | 90.0 | 1304.7 |
| `baseline_s_rr` | completed | 10 | 70.0 | 65.0 | 1339.8 |
| `baseline_s_rr_grounded` | completed | 10 | 90.0 | 100.0 | 1226.1 |
| `optimized_k` | completed | 10 | 50.0 | 30.0 | 33033.3 |
| `optimized_k_grounded` | completed | 10 | 100.0 | 98.5 | 32919.0 |
| `optimized_k_rr` | completed | 10 | 70.0 | 60.0 | 39613.5 |
| `optimized_k_rr_grounded` | completed | 10 | 100.0 | 100.0 | 39461.1 |
| `optimized_s` | completed | 10 | 60.0 | 70.0 | 1941.0 |
| `optimized_s_grounded` | completed | 10 | 80.0 | 82.0 | 1923.8 |
| `optimized_s_rr` | completed | 10 | 60.0 | 80.0 | 1986.7 |
| `optimized_s_rr_grounded` | completed | 10 | 70.0 | 80.0 | 1959.0 |
