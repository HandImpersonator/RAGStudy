# Resumen de evaluación `run_20260518_225310_unknown_c2696cd2`

- Inicio: `2026-05-18T22:53:11`
- Fin: `2026-05-22T04:15:23`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `mistral:7b`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 850/850 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 50 | 54.0 | 0.0 | 498.0 |
| `baseline_k` | completed | 50 | 61.8 | 70.0 | 19169.6 |
| `baseline_k_grounded` | completed | 50 | 56.0 | 82.0 | 19155.8 |
| `baseline_k_rr` | completed | 50 | 70.8 | 76.7 | 15862.5 |
| `baseline_k_rr_grounded` | completed | 50 | 66.4 | 84.4 | 15727.2 |
| `baseline_s` | completed | 50 | 64.0 | 72.0 | 1086.0 |
| `baseline_s_grounded` | completed | 50 | 57.8 | 81.8 | 985.7 |
| `baseline_s_rr` | completed | 50 | 76.0 | 76.0 | 1274.2 |
| `baseline_s_rr_grounded` | completed | 50 | 74.0 | 90.0 | 1186.8 |
| `optimized_k` | completed | 50 | 52.0 | 58.0 | 31386.2 |
| `optimized_k_grounded` | completed | 50 | 52.0 | 76.0 | 31206.7 |
| `optimized_k_rr` | completed | 50 | 68.1 | 68.4 | 25139.4 |
| `optimized_k_rr_grounded` | completed | 50 | 70.0 | 92.0 | 25007.1 |
| `optimized_s` | completed | 50 | 76.0 | 81.6 | 1271.3 |
| `optimized_s_grounded` | completed | 50 | 70.4 | 88.0 | 1227.8 |
| `optimized_s_rr` | completed | 50 | 82.0 | 82.0 | 1266.9 |
| `optimized_s_rr_grounded` | completed | 50 | 72.0 | 90.0 | 1235.0 |
