# Resumen de evaluación `run_20260525_172319_unknown_b32c0817`

- Inicio: `2026-05-25T17:24:07`
- Fin: `2026-05-25T17:37:41`
- Dataset: `hotpotqa`
- Modo: `real`
- Modelo pipeline: `mistral:7b`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 425/425 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 25 | 28.0 | 0.0 | 674.3 |
| `baseline_k` | completed | 25 | 45.0 | 51.2 | 2148.9 |
| `baseline_k_grounded` | completed | 25 | 30.8 | 76.6 | 2085.3 |
| `baseline_k_rr` | completed | 25 | 46.0 | 63.2 | 1509.0 |
| `baseline_k_rr_grounded` | completed | 25 | 42.0 | 75.8 | 1509.7 |
| `baseline_s` | completed | 25 | 33.2 | 31.0 | 766.7 |
| `baseline_s_grounded` | completed | 25 | 40.0 | 68.0 | 680.9 |
| `baseline_s_rr` | completed | 25 | 32.2 | 61.2 | 834.6 |
| `baseline_s_rr_grounded` | completed | 25 | 48.0 | 72.0 | 739.1 |
| `optimized_k` | completed | 25 | 37.6 | 50.8 | 1774.4 |
| `optimized_k_grounded` | completed | 25 | 37.0 | 70.6 | 1777.5 |
| `optimized_k_rr` | completed | 25 | 52.4 | 68.4 | 1549.6 |
| `optimized_k_rr_grounded` | completed | 25 | 44.8 | 80.8 | 1558.2 |
| `optimized_s` | completed | 25 | 25.7 | 54.4 | 898.5 |
| `optimized_s_grounded` | completed | 25 | 52.0 | 72.8 | 759.0 |
| `optimized_s_rr` | completed | 25 | 55.6 | 66.8 | 808.2 |
| `optimized_s_rr_grounded` | completed | 25 | 40.0 | 72.0 | 766.4 |
