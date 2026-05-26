# Resumen de evaluación `run_20260517_205857_bge_base_ms_marco_l6_5360729b`

- Inicio: `2026-05-17T20:58:57`
- Fin: `2026-05-22T04:15:20`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `llama3_8b__bge-base__ms-marco-L6`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 70.0 | 0.0 | 364.7 |
| `baseline_k` | completed | 10 | 30.0 | 40.0 | 18828.2 |
| `baseline_k_grounded` | completed | 10 | 40.0 | 90.0 | 18819.8 |
| `baseline_k_rr` | completed | 10 | 60.0 | 60.0 | 15582.3 |
| `baseline_k_rr_grounded` | completed | 10 | 60.0 | 100.0 | 15378.9 |
| `baseline_s` | completed | 10 | 60.0 | 60.0 | 1600.3 |
| `baseline_s_grounded` | completed | 10 | 90.0 | 90.0 | 1617.0 |
| `baseline_s_rr` | completed | 10 | 90.0 | 100.0 | 1589.0 |
| `baseline_s_rr_grounded` | completed | 10 | 80.0 | 100.0 | 1491.9 |
| `optimized_k` | completed | 10 | 30.0 | 30.0 | 33342.6 |
| `optimized_k_grounded` | completed | 10 | 100.0 | 100.0 | 32990.7 |
| `optimized_k_rr` | completed | 10 | 50.0 | 74.0 | 39725.8 |
| `optimized_k_rr_grounded` | completed | 10 | 90.0 | 90.0 | 39623.6 |
| `optimized_s` | completed | 10 | 60.0 | 60.0 | 2102.6 |
| `optimized_s_grounded` | completed | 10 | 80.0 | 80.0 | 2364.6 |
| `optimized_s_rr` | completed | 10 | 70.0 | 60.0 | 2198.2 |
| `optimized_s_rr_grounded` | completed | 10 | 70.0 | 69.0 | 2312.6 |
