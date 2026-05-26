# Resumen de evaluación `run_20260525_173756_unknown_d42408ca`

- Inicio: `2026-05-25T17:38:49`
- Fin: `2026-05-25T17:52:38`
- Dataset: `hotpotqa`
- Modo: `real`
- Modelo pipeline: `mistral:7b`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 425/425 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 25 | 32.0 | 0.0 | 688.0 |
| `baseline_k` | completed | 25 | 42.4 | 62.8 | 2149.7 |
| `baseline_k_grounded` | completed | 25 | 24.2 | 79.2 | 2084.8 |
| `baseline_k_rr` | completed | 25 | 40.0 | 71.2 | 1511.2 |
| `baseline_k_rr_grounded` | completed | 25 | 38.0 | 80.0 | 1508.7 |
| `baseline_s` | completed | 25 | 31.2 | 36.8 | 767.6 |
| `baseline_s_grounded` | completed | 25 | 36.0 | 76.0 | 678.1 |
| `baseline_s_rr` | completed | 25 | 33.2 | 34.4 | 837.0 |
| `baseline_s_rr_grounded` | completed | 25 | 44.0 | 75.0 | 739.2 |
| `optimized_k` | completed | 25 | 37.8 | 53.2 | 1773.3 |
| `optimized_k_grounded` | completed | 25 | 36.0 | 59.6 | 1777.5 |
| `optimized_k_rr` | completed | 25 | 56.8 | 65.8 | 1552.4 |
| `optimized_k_rr_grounded` | completed | 25 | 42.2 | 82.0 | 1556.6 |
| `optimized_s` | completed | 25 | 25.7 | 35.8 | 901.3 |
| `optimized_s_grounded` | completed | 25 | 48.6 | 80.8 | 759.6 |
| `optimized_s_rr` | completed | 25 | 50.8 | 72.5 | 808.5 |
| `optimized_s_rr_grounded` | completed | 25 | 31.6 | 63.0 | 764.1 |
