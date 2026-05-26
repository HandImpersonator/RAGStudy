# Resumen de evaluación `run_20260525_135720_unknown_2a36f686`

- Inicio: `2026-05-25T13:59:50`
- Fin: `2026-05-25T14:13:39`
- Dataset: `hotpotqa`
- Modo: `real`
- Modelo pipeline: `llama3.2:latest`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 425/425 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 25 | 20.4 | 0.0 | 682.6 |
| `baseline_k` | completed | 25 | 40.4 | 41.0 | 2110.4 |
| `baseline_k_grounded` | completed | 25 | 40.0 | 68.0 | 2114.6 |
| `baseline_k_rr` | completed | 25 | 40.0 | 56.8 | 1535.3 |
| `baseline_k_rr_grounded` | completed | 25 | 36.4 | 64.2 | 1478.9 |
| `baseline_s` | completed | 25 | 33.4 | 42.2 | 775.4 |
| `baseline_s_grounded` | completed | 25 | 30.0 | 76.0 | 608.7 |
| `baseline_s_rr` | completed | 25 | 43.0 | 56.0 | 782.2 |
| `baseline_s_rr_grounded` | completed | 25 | 33.8 | 64.6 | 777.7 |
| `optimized_k` | completed | 25 | 38.4 | 50.8 | 1815.4 |
| `optimized_k_grounded` | completed | 25 | 39.4 | 73.2 | 1670.9 |
| `optimized_k_rr` | completed | 25 | 38.4 | 60.0 | 1543.9 |
| `optimized_k_rr_grounded` | completed | 25 | 49.3 | 61.7 | 1451.8 |
| `optimized_s` | completed | 25 | 37.8 | 50.4 | 806.4 |
| `optimized_s_grounded` | completed | 25 | 31.4 | 51.2 | 685.5 |
| `optimized_s_rr` | completed | 25 | 48.4 | 46.6 | 763.0 |
| `optimized_s_rr_grounded` | completed | 25 | 38.8 | 65.0 | 627.3 |
