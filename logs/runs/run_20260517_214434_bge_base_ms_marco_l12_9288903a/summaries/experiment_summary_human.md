# Resumen de evaluación `run_20260517_214434_bge_base_ms_marco_l12_9288903a`

- Inicio: `2026-05-17T21:44:34`
- Fin: `2026-05-22T04:15:21`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `mistral_7b__bge-base__ms-marco-L12`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 80.0 | 0.0 | 690.9 |
| `baseline_k` | completed | 10 | 40.0 | 70.0 | 18640.7 |
| `baseline_k_grounded` | completed | 10 | 40.0 | 80.0 | 18618.6 |
| `baseline_k_rr` | completed | 10 | 50.0 | 90.0 | 15288.2 |
| `baseline_k_rr_grounded` | completed | 10 | 50.0 | 90.0 | 15204.6 |
| `baseline_s` | completed | 10 | 60.0 | 60.0 | 1402.8 |
| `baseline_s_grounded` | completed | 10 | 70.0 | 100.0 | 1314.6 |
| `baseline_s_rr` | completed | 10 | 70.0 | 90.0 | 1430.7 |
| `baseline_s_rr_grounded` | completed | 10 | 80.0 | 90.0 | 1426.4 |
| `optimized_k` | completed | 10 | 40.0 | 60.0 | 33051.3 |
| `optimized_k_grounded` | completed | 10 | 100.0 | 100.0 | 32961.1 |
| `optimized_k_rr` | completed | 10 | 40.0 | 90.0 | 39680.3 |
| `optimized_k_rr_grounded` | completed | 10 | 90.0 | 90.0 | 39548.0 |
| `optimized_s` | completed | 10 | 70.0 | 70.0 | 2013.1 |
| `optimized_s_grounded` | completed | 10 | 70.0 | 90.0 | 2038.1 |
| `optimized_s_rr` | completed | 10 | 80.0 | 90.0 | 2175.4 |
| `optimized_s_rr_grounded` | completed | 10 | 80.0 | 70.0 | 2100.2 |
