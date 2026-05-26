# Resumen de evaluación `run_20260525_175252_unknown_2d38151f`

- Inicio: `2026-05-25T17:53:40`
- Fin: `2026-05-25T18:06:58`
- Dataset: `hotpotqa`
- Modo: `real`
- Modelo pipeline: `mistral:7b`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 425/425 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 25 | 28.0 | 0.0 | 688.5 |
| `baseline_k` | completed | 25 | 42.0 | 74.1 | 2151.5 |
| `baseline_k_grounded` | completed | 25 | 32.0 | 52.8 | 2088.4 |
| `baseline_k_rr` | completed | 25 | 44.0 | 63.4 | 1511.6 |
| `baseline_k_rr_grounded` | completed | 25 | 38.4 | 79.2 | 1510.7 |
| `baseline_s` | completed | 25 | 25.8 | 30.4 | 770.5 |
| `baseline_s_grounded` | completed | 25 | 36.8 | 76.0 | 684.2 |
| `baseline_s_rr` | completed | 25 | 30.8 | 41.2 | 840.6 |
| `baseline_s_rr_grounded` | completed | 25 | 38.4 | 67.6 | 741.8 |
| `optimized_k` | completed | 25 | 46.2 | 65.8 | 1775.8 |
| `optimized_k_grounded` | completed | 25 | 38.4 | 63.2 | 1780.7 |
| `optimized_k_rr` | completed | 25 | 52.0 | 68.0 | 1552.1 |
| `optimized_k_rr_grounded` | completed | 25 | 54.6 | 80.2 | 1557.4 |
| `optimized_s` | completed | 25 | 27.4 | 31.1 | 901.9 |
| `optimized_s_grounded` | completed | 25 | 42.4 | 83.8 | 759.1 |
| `optimized_s_rr` | completed | 25 | 54.4 | 68.2 | 810.3 |
| `optimized_s_rr_grounded` | completed | 25 | 30.1 | 88.0 | 766.3 |
