# Resumen de evaluación `run_20260520_204251_unknown_0ae208b6`

- Inicio: `2026-05-20T20:43:33`
- Fin: `2026-05-22T04:15:28`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `llama3:8b`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 4375/4375 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 625 | 69.6 | 0.0 | 404.1 |
| `baseline_s` | completed | 625 | 73.0 | 80.0 | 1299.6 |
| `baseline_s_rr` | completed | 625 | 80.0 | 85.3 | 1216.4 |
| `baseline_s_rr_grounded` | completed | 625 | 78.4 | 87.9 | 1286.2 |
| `optimized_s` | completed | 625 | 70.9 | 80.4 | 1487.4 |
| `optimized_s_rr` | completed | 625 | 77.1 | 83.1 | 1405.7 |
| `optimized_s_rr_grounded` | completed | 625 | 77.1 | 87.0 | 1472.9 |
