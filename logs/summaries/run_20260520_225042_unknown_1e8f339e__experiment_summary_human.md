# Resumen de evaluación `run_20260520_225042_unknown_1e8f339e`

- Inicio: `2026-05-20T22:51:20`
- Fin: `2026-05-22T04:15:30`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `llama3:8b`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 4375/4375 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 625 | 70.1 | 0.0 | 399.7 |
| `baseline_s` | completed | 625 | 73.0 | 79.9 | 1301.3 |
| `baseline_s_rr` | completed | 625 | 78.9 | 85.0 | 1219.2 |
| `baseline_s_rr_grounded` | completed | 625 | 77.9 | 87.8 | 1290.2 |
| `optimized_s` | completed | 625 | 70.4 | 79.7 | 1493.8 |
| `optimized_s_rr` | completed | 625 | 77.1 | 83.5 | 1410.7 |
| `optimized_s_rr_grounded` | completed | 625 | 77.2 | 86.3 | 1479.9 |
