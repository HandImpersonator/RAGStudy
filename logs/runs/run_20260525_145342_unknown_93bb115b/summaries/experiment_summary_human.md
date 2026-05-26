# Resumen de evaluación `run_20260525_145342_unknown_93bb115b`

- Inicio: `2026-05-25T14:54:30`
- Fin: `2026-05-25T15:08:21`
- Dataset: `hotpotqa`
- Modo: `real`
- Modelo pipeline: `llama3.2:latest`
- Estado de evaluación: **partial**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 420/425 (98.8%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 25 | 20.2 | 0.0 | 673.9 |
| `baseline_k` | completed | 25 | 37.0 | 66.6 | 2098.5 |
| `baseline_k_grounded` | completed | 25 | 34.0 | 44.0 | 2111.9 |
| `baseline_k_rr` | completed | 25 | 40.0 | 47.6 | 1526.7 |
| `baseline_k_rr_grounded` | completed | 25 | 34.4 | 64.2 | 1474.7 |
| `baseline_s` | partial | 25 | 30.0 | 61.0 | 775.1 |
| `baseline_s_grounded` | completed | 25 | 16.6 | 74.2 | 601.8 |
| `baseline_s_rr` | completed | 25 | 45.7 | 57.2 | 780.3 |
| `baseline_s_rr_grounded` | completed | 25 | 36.8 | 60.0 | 776.4 |
| `optimized_k` | completed | 25 | 38.8 | 51.0 | 1813.0 |
| `optimized_k_grounded` | completed | 25 | 41.4 | 60.0 | 1677.5 |
| `optimized_k_rr` | completed | 25 | 40.0 | 48.0 | 1548.4 |
| `optimized_k_rr_grounded` | completed | 25 | 44.6 | 55.4 | 1455.7 |
| `optimized_s` | completed | 25 | 38.2 | 42.0 | 804.4 |
| `optimized_s_grounded` | completed | 25 | 23.4 | 63.8 | 683.1 |
| `optimized_s_rr` | completed | 25 | 52.0 | 56.0 | 766.3 |
| `optimized_s_rr_grounded` | completed | 25 | 52.6 | 76.2 | 630.5 |
