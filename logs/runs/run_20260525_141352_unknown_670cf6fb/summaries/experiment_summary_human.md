# Resumen de evaluación `run_20260525_141352_unknown_670cf6fb`

- Inicio: `2026-05-25T14:14:40`
- Fin: `2026-05-25T14:29:34`
- Dataset: `hotpotqa`
- Modo: `real`
- Modelo pipeline: `llama3.2:latest`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 425/425 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 25 | 16.6 | 0.0 | 672.9 |
| `baseline_k` | completed | 25 | 45.0 | 43.0 | 2092.7 |
| `baseline_k_grounded` | completed | 25 | 32.5 | 48.7 | 2111.5 |
| `baseline_k_rr` | completed | 25 | 38.4 | 60.8 | 1523.6 |
| `baseline_k_rr_grounded` | completed | 25 | 34.8 | 51.2 | 1465.0 |
| `baseline_s` | completed | 25 | 32.8 | 60.0 | 771.6 |
| `baseline_s_grounded` | completed | 25 | 17.0 | 86.2 | 609.3 |
| `baseline_s_rr` | completed | 25 | 40.4 | 63.1 | 783.4 |
| `baseline_s_rr_grounded` | completed | 25 | 28.0 | 64.8 | 772.2 |
| `optimized_k` | completed | 25 | 28.0 | 42.0 | 1816.5 |
| `optimized_k_grounded` | completed | 25 | 40.0 | 59.2 | 1685.3 |
| `optimized_k_rr` | completed | 25 | 40.0 | 48.0 | 1549.6 |
| `optimized_k_rr_grounded` | completed | 25 | 32.4 | 62.0 | 1451.5 |
| `optimized_s` | completed | 25 | 39.0 | 44.8 | 806.4 |
| `optimized_s_grounded` | completed | 25 | 44.6 | 43.9 | 689.6 |
| `optimized_s_rr` | completed | 25 | 48.0 | 58.8 | 769.9 |
| `optimized_s_rr_grounded` | completed | 25 | 35.2 | 50.8 | 628.8 |
