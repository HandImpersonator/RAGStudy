# Resumen de evaluación `run_20260521_141011_unknown_d95c0ab0`

- Inicio: `2026-05-21T14:10:51`
- Fin: `2026-05-22T04:15:51`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `mistral:7b`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 4375/4375 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 625 | 67.5 | 0.0 | 409.4 |
| `baseline_s` | completed | 625 | 73.7 | 82.0 | 1180.8 |
| `baseline_s_rr` | completed | 625 | 78.6 | 84.3 | 1072.2 |
| `baseline_s_rr_grounded` | completed | 625 | 77.3 | 89.2 | 1001.3 |
| `optimized_s` | completed | 625 | 71.5 | 79.7 | 1379.5 |
| `optimized_s_rr` | completed | 625 | 76.3 | 84.9 | 1292.6 |
| `optimized_s_rr_grounded` | completed | 625 | 76.7 | 87.5 | 1255.3 |
