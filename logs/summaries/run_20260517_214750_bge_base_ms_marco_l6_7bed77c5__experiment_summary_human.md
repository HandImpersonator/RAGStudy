# Resumen de evaluación `run_20260517_214750_bge_base_ms_marco_l6_7bed77c5`

- Inicio: `2026-05-17T21:47:50`
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
| `no_rag` | completed | 10 | 70.0 | 0.0 | 423.0 |
| `baseline_k` | completed | 10 | 40.0 | 60.0 | 18639.8 |
| `baseline_k_grounded` | completed | 10 | 60.0 | 80.0 | 18619.7 |
| `baseline_k_rr` | completed | 10 | 60.0 | 82.0 | 15316.7 |
| `baseline_k_rr_grounded` | completed | 10 | 60.0 | 90.0 | 15143.8 |
| `baseline_s` | completed | 10 | 60.0 | 70.0 | 1401.6 |
| `baseline_s_grounded` | completed | 10 | 70.0 | 100.0 | 1314.5 |
| `baseline_s_rr` | completed | 10 | 70.0 | 92.0 | 1354.3 |
| `baseline_s_rr_grounded` | completed | 10 | 80.0 | 90.0 | 1322.3 |
| `optimized_k` | completed | 10 | 40.0 | 60.0 | 33053.7 |
| `optimized_k_grounded` | completed | 10 | 50.0 | 100.0 | 32958.8 |
| `optimized_k_rr` | completed | 10 | 50.0 | 70.0 | 39630.6 |
| `optimized_k_rr_grounded` | completed | 10 | 100.0 | 100.0 | 39441.5 |
| `optimized_s` | completed | 10 | 70.0 | 70.0 | 2014.2 |
| `optimized_s_grounded` | completed | 10 | 80.0 | 80.0 | 2037.6 |
| `optimized_s_rr` | completed | 10 | 80.0 | 90.0 | 2045.8 |
| `optimized_s_rr_grounded` | completed | 10 | 80.0 | 90.0 | 1994.1 |
