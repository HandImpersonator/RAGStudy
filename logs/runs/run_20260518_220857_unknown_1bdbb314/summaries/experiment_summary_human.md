# Resumen de evaluación `run_20260518_220857_unknown_1bdbb314`

- Inicio: `2026-05-18T22:08:58`
- Fin: `2026-05-22T04:15:23`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `llama3:8b`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 850/850 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 50 | 68.0 | 0.0 | 479.1 |
| `baseline_k` | completed | 50 | 58.0 | 65.0 | 19426.4 |
| `baseline_k_grounded` | completed | 50 | 48.0 | 81.4 | 19382.5 |
| `baseline_k_rr` | completed | 50 | 64.0 | 65.2 | 16049.5 |
| `baseline_k_rr_grounded` | completed | 50 | 62.2 | 88.2 | 16048.4 |
| `baseline_s` | completed | 50 | 67.0 | 74.8 | 1245.9 |
| `baseline_s_grounded` | completed | 50 | 55.4 | 83.9 | 1288.5 |
| `baseline_s_rr` | completed | 50 | 76.2 | 79.0 | 1439.7 |
| `baseline_s_rr_grounded` | completed | 50 | 78.0 | 87.3 | 1450.1 |
| `optimized_k` | completed | 50 | 54.0 | 75.6 | 31550.2 |
| `optimized_k_grounded` | completed | 50 | 50.0 | 85.6 | 31382.8 |
| `optimized_k_rr` | completed | 50 | 64.0 | 66.0 | 25289.8 |
| `optimized_k_rr_grounded` | completed | 50 | 64.0 | 92.0 | 25190.8 |
| `optimized_s` | completed | 50 | 74.2 | 77.6 | 1415.4 |
| `optimized_s_grounded` | completed | 50 | 72.0 | 78.0 | 1466.3 |
| `optimized_s_rr` | completed | 50 | 80.8 | 87.5 | 1401.1 |
| `optimized_s_rr_grounded` | completed | 50 | 80.0 | 84.0 | 1461.9 |
