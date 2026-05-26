# Resumen de evaluación `run_20260517_223818_bge_base_ms_marco_l6_d426137c`

- Inicio: `2026-05-17T22:38:18`
- Fin: `2026-05-22T04:15:21`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `mistral_7b__bge-base__ms-marco-L6`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 70.0 | 0.0 | 420.0 |
| `baseline_k` | completed | 10 | 40.0 | 60.0 | 18634.1 |
| `baseline_k_grounded` | completed | 10 | 30.0 | 80.0 | 18617.7 |
| `baseline_k_rr` | completed | 10 | 60.0 | 80.0 | 15312.3 |
| `baseline_k_rr_grounded` | completed | 10 | 60.0 | 90.0 | 15145.4 |
| `baseline_s` | completed | 10 | 60.0 | 70.0 | 1398.2 |
| `baseline_s_grounded` | completed | 10 | 70.0 | 90.0 | 1314.2 |
| `baseline_s_rr` | completed | 10 | 70.0 | 70.0 | 1355.1 |
| `baseline_s_rr_grounded` | completed | 10 | 70.0 | 90.0 | 1319.1 |
| `optimized_k` | completed | 10 | 40.0 | 50.0 | 33050.2 |
| `optimized_k_grounded` | completed | 10 | 100.0 | 100.0 | 32959.8 |
| `optimized_k_rr` | completed | 10 | 50.0 | 90.0 | 39623.2 |
| `optimized_k_rr_grounded` | completed | 10 | 60.0 | 60.0 | 39443.1 |
| `optimized_s` | completed | 10 | 70.0 | 70.0 | 2010.1 |
| `optimized_s_grounded` | completed | 10 | 80.0 | 80.0 | 2035.0 |
| `optimized_s_rr` | completed | 10 | 80.0 | 89.0 | 2038.9 |
| `optimized_s_rr_grounded` | completed | 10 | 80.0 | 89.0 | 1994.1 |
