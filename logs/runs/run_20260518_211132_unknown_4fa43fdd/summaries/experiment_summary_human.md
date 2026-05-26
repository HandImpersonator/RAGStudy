# Resumen de evaluación `run_20260518_211132_unknown_4fa43fdd`

- Inicio: `2026-05-18T21:11:32`
- Fin: `2026-05-22T04:15:22`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `llama3.2:latest`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 850/850 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 50 | 74.0 | 0.0 | 380.4 |
| `baseline_k` | completed | 50 | 64.0 | 72.0 | 19168.8 |
| `baseline_k_grounded` | completed | 50 | 64.0 | 79.8 | 19085.8 |
| `baseline_k_rr` | completed | 50 | 66.0 | 59.8 | 15803.9 |
| `baseline_k_rr_grounded` | completed | 50 | 58.0 | 78.0 | 15710.9 |
| `baseline_s` | completed | 50 | 64.4 | 70.0 | 1006.2 |
| `baseline_s_grounded` | completed | 50 | 58.0 | 90.0 | 927.5 |
| `baseline_s_rr` | completed | 50 | 67.7 | 63.2 | 1208.1 |
| `baseline_s_rr_grounded` | completed | 50 | 66.8 | 86.4 | 1150.7 |
| `optimized_k` | completed | 50 | 44.0 | 54.0 | 31280.3 |
| `optimized_k_grounded` | completed | 50 | 54.0 | 86.0 | 31137.4 |
| `optimized_k_rr` | completed | 50 | 58.0 | 66.0 | 25067.7 |
| `optimized_k_rr_grounded` | completed | 50 | 64.0 | 83.2 | 24928.8 |
| `optimized_s` | completed | 50 | 71.6 | 74.0 | 1199.8 |
| `optimized_s_grounded` | completed | 50 | 76.0 | 82.0 | 1185.9 |
| `optimized_s_rr` | completed | 50 | 74.8 | 77.6 | 1197.2 |
| `optimized_s_rr_grounded` | completed | 50 | 70.0 | 83.2 | 1236.7 |
