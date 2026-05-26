# Resumen de evaluación `run_20260518_231903_unknown_5e34e77c`

- Inicio: `2026-05-18T23:19:03`
- Fin: `2026-05-22T04:15:23`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `mistral:7b`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 850/850 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 50 | 56.0 | 0.0 | 506.2 |
| `baseline_k` | completed | 50 | 62.4 | 74.0 | 19170.6 |
| `baseline_k_grounded` | completed | 50 | 62.0 | 78.0 | 19155.1 |
| `baseline_k_rr` | completed | 50 | 68.4 | 76.1 | 15861.4 |
| `baseline_k_rr_grounded` | completed | 50 | 66.4 | 85.6 | 15727.2 |
| `baseline_s` | completed | 50 | 64.0 | 78.6 | 1088.9 |
| `baseline_s_grounded` | completed | 50 | 64.4 | 80.4 | 984.7 |
| `baseline_s_rr` | completed | 50 | 78.0 | 76.4 | 1272.2 |
| `baseline_s_rr_grounded` | completed | 50 | 74.0 | 87.2 | 1184.5 |
| `optimized_k` | completed | 50 | 60.0 | 63.0 | 31384.6 |
| `optimized_k_grounded` | completed | 50 | 62.0 | 82.0 | 31206.7 |
| `optimized_k_rr` | completed | 50 | 64.2 | 68.4 | 25140.2 |
| `optimized_k_rr_grounded` | completed | 50 | 66.0 | 88.0 | 25004.4 |
| `optimized_s` | completed | 50 | 74.0 | 75.6 | 1271.6 |
| `optimized_s_grounded` | completed | 50 | 72.0 | 84.0 | 1227.3 |
| `optimized_s_rr` | completed | 50 | 82.0 | 82.0 | 1265.8 |
| `optimized_s_rr_grounded` | completed | 50 | 72.0 | 85.6 | 1231.3 |
