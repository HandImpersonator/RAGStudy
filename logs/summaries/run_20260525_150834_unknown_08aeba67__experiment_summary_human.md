# Resumen de evaluación `run_20260525_150834_unknown_08aeba67`

- Inicio: `2026-05-25T15:09:27`
- Fin: `2026-05-25T15:22:43`
- Dataset: `hotpotqa`
- Modo: `real`
- Modelo pipeline: `llama3.2:latest`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 425/425 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 25 | 23.2 | 0.0 | 672.4 |
| `baseline_k` | completed | 25 | 45.2 | 61.4 | 2095.2 |
| `baseline_k_grounded` | completed | 25 | 28.0 | 52.0 | 2105.7 |
| `baseline_k_rr` | completed | 25 | 40.0 | 61.2 | 1526.4 |
| `baseline_k_rr_grounded` | completed | 25 | 36.4 | 62.6 | 1470.9 |
| `baseline_s` | completed | 25 | 30.0 | 54.6 | 773.5 |
| `baseline_s_grounded` | completed | 25 | 16.4 | 83.8 | 603.8 |
| `baseline_s_rr` | completed | 25 | 41.4 | 57.4 | 782.9 |
| `baseline_s_rr_grounded` | completed | 25 | 32.4 | 69.8 | 777.2 |
| `optimized_k` | completed | 25 | 29.2 | 42.6 | 1815.4 |
| `optimized_k_grounded` | completed | 25 | 38.8 | 64.8 | 1676.8 |
| `optimized_k_rr` | completed | 25 | 40.0 | 48.0 | 1547.4 |
| `optimized_k_rr_grounded` | completed | 25 | 44.2 | 63.0 | 1451.0 |
| `optimized_s` | completed | 25 | 42.2 | 46.9 | 812.6 |
| `optimized_s_grounded` | completed | 25 | 36.0 | 58.4 | 684.8 |
| `optimized_s_rr` | completed | 25 | 46.6 | 60.2 | 769.8 |
| `optimized_s_rr_grounded` | completed | 25 | 32.4 | 82.8 | 623.0 |
