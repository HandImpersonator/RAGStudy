# Resumen de evaluación `run_20260525_142947_unknown_972884f2`

- Inicio: `2026-05-25T14:30:35`
- Fin: `2026-05-25T14:53:28`
- Dataset: `hotpotqa`
- Modo: `real`
- Modelo pipeline: `llama3.2:latest`
- Estado de evaluación: **partial**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 420/425 (98.8%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 25 | 26.4 | 0.0 | 667.1 |
| `baseline_k` | completed | 25 | 40.4 | 45.4 | 2090.2 |
| `baseline_k_grounded` | completed | 25 | 40.8 | 63.6 | 2109.3 |
| `baseline_k_rr` | completed | 25 | 36.4 | 57.8 | 1528.4 |
| `baseline_k_rr_grounded` | completed | 25 | 38.6 | 60.2 | 1466.6 |
| `baseline_s` | completed | 25 | 28.0 | 41.6 | 774.1 |
| `baseline_s_grounded` | completed | 25 | 23.0 | 75.4 | 601.9 |
| `baseline_s_rr` | completed | 25 | 42.6 | 55.6 | 782.6 |
| `baseline_s_rr_grounded` | completed | 25 | 28.0 | 61.4 | 774.2 |
| `optimized_k` | completed | 25 | 34.0 | 33.2 | 1808.5 |
| `optimized_k_grounded` | completed | 25 | 45.2 | 63.6 | 1674.5 |
| `optimized_k_rr` | completed | 25 | 40.0 | 48.0 | 1542.6 |
| `optimized_k_rr_grounded` | completed | 25 | 44.0 | 66.2 | 1446.1 |
| `optimized_s` | completed | 25 | 38.6 | 60.8 | 805.4 |
| `optimized_s_grounded` | completed | 25 | 42.6 | 50.8 | 680.5 |
| `optimized_s_rr` | completed | 25 | 49.0 | 59.0 | 764.0 |
| `optimized_s_rr_grounded` | partial | 25 | 41.5 | 85.8 | 624.8 |
