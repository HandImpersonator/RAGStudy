# Resumen de evaluación `run_20260525_155806_unknown_2624b74f`

- Inicio: `2026-05-25T15:58:54`
- Fin: `2026-05-25T16:14:11`
- Dataset: `hotpotqa`
- Modo: `real`
- Modelo pipeline: `llama3:8b`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 425/425 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 25 | 12.0 | 0.0 | 830.0 |
| `baseline_k` | completed | 25 | 37.6 | 41.4 | 2392.2 |
| `baseline_k_grounded` | completed | 25 | 42.4 | 62.8 | 2519.2 |
| `baseline_k_rr` | completed | 25 | 52.8 | 60.9 | 1819.8 |
| `baseline_k_rr_grounded` | completed | 25 | 52.8 | 66.6 | 2010.4 |
| `baseline_s` | completed | 25 | 42.2 | 61.2 | 1027.8 |
| `baseline_s_grounded` | completed | 25 | 37.4 | 80.0 | 920.5 |
| `baseline_s_rr` | completed | 25 | 41.2 | 66.6 | 1068.1 |
| `baseline_s_rr_grounded` | completed | 25 | 43.6 | 68.8 | 1231.8 |
| `optimized_k` | completed | 25 | 35.8 | 39.0 | 2001.1 |
| `optimized_k_grounded` | completed | 25 | 45.4 | 81.0 | 2084.4 |
| `optimized_k_rr` | completed | 25 | 64.8 | 75.2 | 1821.6 |
| `optimized_k_rr_grounded` | completed | 25 | 44.4 | 72.0 | 2017.8 |
| `optimized_s` | completed | 25 | 32.6 | 71.2 | 1003.0 |
| `optimized_s_grounded` | completed | 25 | 56.4 | 76.8 | 1035.7 |
| `optimized_s_rr` | completed | 25 | 44.6 | 60.6 | 1116.3 |
| `optimized_s_rr_grounded` | completed | 25 | 53.8 | 71.4 | 1187.3 |
