# Resumen de evaluación `run_20260525_170748_unknown_2bfce661`

- Inicio: `2026-05-25T17:08:41`
- Fin: `2026-05-25T17:23:06`
- Dataset: `hotpotqa`
- Modo: `real`
- Modelo pipeline: `mistral:7b`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 425/425 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 25 | 21.2 | 0.0 | 682.3 |
| `baseline_k` | completed | 25 | 40.6 | 67.2 | 2149.9 |
| `baseline_k_grounded` | completed | 25 | 28.0 | 76.0 | 2087.6 |
| `baseline_k_rr` | completed | 25 | 40.4 | 70.4 | 1514.2 |
| `baseline_k_rr_grounded` | completed | 25 | 37.8 | 76.1 | 1507.0 |
| `baseline_s` | completed | 25 | 25.4 | 41.4 | 771.6 |
| `baseline_s_grounded` | completed | 25 | 29.0 | 64.4 | 680.4 |
| `baseline_s_rr` | completed | 25 | 32.4 | 38.6 | 838.5 |
| `baseline_s_rr_grounded` | completed | 25 | 44.0 | 79.2 | 739.2 |
| `optimized_k` | completed | 25 | 40.2 | 51.4 | 1774.0 |
| `optimized_k_grounded` | completed | 25 | 48.6 | 63.8 | 1777.3 |
| `optimized_k_rr` | completed | 25 | 57.2 | 60.7 | 1551.6 |
| `optimized_k_rr_grounded` | completed | 25 | 40.4 | 67.8 | 1558.5 |
| `optimized_s` | completed | 25 | 28.1 | 40.5 | 898.1 |
| `optimized_s_grounded` | completed | 25 | 55.4 | 84.4 | 758.5 |
| `optimized_s_rr` | completed | 25 | 43.2 | 78.2 | 809.3 |
| `optimized_s_rr_grounded` | completed | 25 | 36.0 | 56.0 | 767.7 |
