# Resumen de evaluación `run_20260518_204035_unknown_e7e4e2d8`

- Inicio: `2026-05-18T20:40:35`
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
| `no_rag` | completed | 50 | 78.0 | 0.0 | 381.4 |
| `baseline_k` | completed | 50 | 61.6 | 71.6 | 19166.5 |
| `baseline_k_grounded` | completed | 50 | 58.0 | 76.0 | 19085.5 |
| `baseline_k_rr` | completed | 50 | 66.0 | 69.6 | 15802.3 |
| `baseline_k_rr_grounded` | completed | 50 | 60.0 | 86.0 | 15713.1 |
| `baseline_s` | completed | 50 | 65.0 | 73.0 | 1003.0 |
| `baseline_s_grounded` | completed | 50 | 58.0 | 77.0 | 925.1 |
| `baseline_s_rr` | completed | 50 | 69.9 | 68.4 | 1206.2 |
| `baseline_s_rr_grounded` | completed | 50 | 67.6 | 80.4 | 1148.7 |
| `optimized_k` | completed | 50 | 50.0 | 66.4 | 31279.0 |
| `optimized_k_grounded` | completed | 50 | 54.0 | 88.0 | 31135.6 |
| `optimized_k_rr` | completed | 50 | 62.0 | 70.0 | 25064.2 |
| `optimized_k_rr_grounded` | completed | 50 | 66.0 | 91.6 | 24921.8 |
| `optimized_s` | completed | 50 | 70.0 | 74.8 | 1197.7 |
| `optimized_s_grounded` | completed | 50 | 68.4 | 84.8 | 1181.1 |
| `optimized_s_rr` | completed | 50 | 74.0 | 76.0 | 1191.8 |
| `optimized_s_rr_grounded` | completed | 50 | 70.0 | 81.6 | 1230.4 |
