# Resumen de evaluación `run_20260525_152301_unknown_c697a8fe`

- Inicio: `2026-05-25T15:23:49`
- Fin: `2026-05-25T15:38:48`
- Dataset: `hotpotqa`
- Modo: `real`
- Modelo pipeline: `llama3:8b`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 425/425 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 25 | 24.0 | 0.0 | 819.8 |
| `baseline_k` | completed | 25 | 37.8 | 38.8 | 2093.9 |
| `baseline_k_grounded` | completed | 25 | 32.4 | 52.4 | 2113.1 |
| `baseline_k_rr` | completed | 25 | 40.2 | 56.6 | 1528.8 |
| `baseline_k_rr_grounded` | completed | 25 | 35.2 | 45.2 | 1463.5 |
| `baseline_s` | completed | 25 | 36.0 | 48.8 | 777.8 |
| `baseline_s_grounded` | completed | 25 | 28.8 | 84.0 | 608.6 |
| `baseline_s_rr` | completed | 25 | 45.8 | 50.2 | 781.6 |
| `baseline_s_rr_grounded` | completed | 25 | 32.0 | 64.0 | 775.2 |
| `optimized_k` | completed | 25 | 38.0 | 53.2 | 1817.2 |
| `optimized_k_grounded` | completed | 25 | 40.6 | 73.8 | 1677.3 |
| `optimized_k_rr` | completed | 25 | 42.0 | 50.0 | 1544.1 |
| `optimized_k_rr_grounded` | completed | 25 | 46.0 | 70.6 | 1445.8 |
| `optimized_s` | completed | 25 | 40.0 | 49.6 | 807.7 |
| `optimized_s_grounded` | completed | 25 | 37.8 | 56.2 | 685.9 |
| `optimized_s_rr` | completed | 25 | 54.0 | 59.0 | 766.1 |
| `optimized_s_rr_grounded` | completed | 25 | 52.0 | 64.0 | 627.9 |
