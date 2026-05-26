# Resumen de evaluación `run_20260517_133710_bge_base_ms_marco_l6_e48a7dfb`

- Inicio: `2026-05-17T13:37:10`
- Fin: `2026-05-22T04:15:19`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `llama3.2_latest__bge-base__ms-marco-L6`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 70.0 | 0.0 | 293.7 |
| `baseline_k` | completed | 10 | 40.0 | 66.0 | 18749.6 |
| `baseline_k_grounded` | completed | 10 | 20.0 | 82.0 | 18612.5 |
| `baseline_k_rr` | completed | 10 | 70.0 | 60.0 | 15253.7 |
| `baseline_k_rr_grounded` | completed | 10 | 70.0 | 100.0 | 15143.9 |
| `baseline_s` | completed | 10 | 70.0 | 90.0 | 1331.1 |
| `baseline_s_grounded` | completed | 10 | 90.0 | 90.0 | 1308.9 |
| `baseline_s_rr` | completed | 10 | 70.0 | 72.0 | 1351.7 |
| `baseline_s_rr_grounded` | completed | 10 | 100.0 | 100.0 | 1247.5 |
| `optimized_k` | completed | 10 | 60.0 | 60.0 | 33033.6 |
| `optimized_k_grounded` | completed | 10 | 40.0 | 90.0 | 32926.9 |
| `optimized_k_rr` | completed | 10 | 50.0 | 70.0 | 39622.0 |
| `optimized_k_rr_grounded` | completed | 10 | 60.0 | 100.0 | 39469.0 |
| `optimized_s` | completed | 10 | 60.0 | 71.0 | 1950.2 |
| `optimized_s_grounded` | completed | 10 | 70.0 | 73.0 | 1929.1 |
| `optimized_s_rr` | completed | 10 | 60.0 | 70.0 | 1994.0 |
| `optimized_s_rr_grounded` | completed | 10 | 80.0 | 80.0 | 1975.1 |
