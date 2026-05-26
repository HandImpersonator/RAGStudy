# Resumen de evaluación `run_20260518_214033_unknown_ac2bbe71`

- Inicio: `2026-05-18T21:40:33`
- Fin: `2026-05-22T04:15:22`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `llama3:8b`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 850/850 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 50 | 68.0 | 0.0 | 479.4 |
| `baseline_k` | completed | 50 | 62.0 | 68.0 | 19424.5 |
| `baseline_k_grounded` | completed | 50 | 52.0 | 84.0 | 19385.0 |
| `baseline_k_rr` | completed | 50 | 64.0 | 63.4 | 16049.6 |
| `baseline_k_rr_grounded` | completed | 50 | 62.0 | 86.4 | 16052.7 |
| `baseline_s` | completed | 50 | 67.0 | 71.0 | 1243.5 |
| `baseline_s_grounded` | completed | 50 | 58.4 | 69.8 | 1285.9 |
| `baseline_s_rr` | completed | 50 | 80.0 | 84.0 | 1437.6 |
| `baseline_s_rr_grounded` | completed | 50 | 78.2 | 87.6 | 1453.0 |
| `optimized_k` | completed | 50 | 54.0 | 74.1 | 31548.9 |
| `optimized_k_grounded` | completed | 50 | 66.0 | 87.2 | 31387.2 |
| `optimized_k_rr` | completed | 50 | 64.0 | 69.8 | 25298.3 |
| `optimized_k_rr_grounded` | completed | 50 | 64.2 | 90.4 | 25192.4 |
| `optimized_s` | completed | 50 | 68.0 | 72.8 | 1421.1 |
| `optimized_s_grounded` | completed | 50 | 72.0 | 78.0 | 1467.2 |
| `optimized_s_rr` | completed | 50 | 82.5 | 83.8 | 1405.8 |
| `optimized_s_rr_grounded` | completed | 50 | 80.0 | 83.8 | 1460.5 |
