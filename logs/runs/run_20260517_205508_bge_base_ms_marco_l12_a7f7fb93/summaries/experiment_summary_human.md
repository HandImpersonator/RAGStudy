# Resumen de evaluación `run_20260517_205508_bge_base_ms_marco_l12_a7f7fb93`

- Inicio: `2026-05-17T20:55:08`
- Fin: `2026-05-22T04:15:20`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `llama3_8b__bge-base__ms-marco-L12`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 70.0 | 0.0 | 832.3 |
| `baseline_k` | completed | 10 | 30.0 | 51.0 | 18829.6 |
| `baseline_k_grounded` | completed | 10 | 70.0 | 80.0 | 18816.3 |
| `baseline_k_rr` | completed | 10 | 60.0 | 70.0 | 15533.5 |
| `baseline_k_rr_grounded` | completed | 10 | 50.0 | 90.0 | 15440.6 |
| `baseline_s` | completed | 10 | 50.0 | 70.0 | 1598.4 |
| `baseline_s_grounded` | completed | 10 | 60.0 | 95.0 | 1616.7 |
| `baseline_s_rr` | completed | 10 | 60.0 | 70.0 | 1641.8 |
| `baseline_s_rr_grounded` | completed | 10 | 90.0 | 92.0 | 1640.6 |
| `optimized_k` | completed | 10 | 40.0 | 40.0 | 33337.0 |
| `optimized_k_grounded` | completed | 10 | 40.0 | 99.0 | 32989.4 |
| `optimized_k_rr` | completed | 10 | 50.0 | 60.0 | 39822.0 |
| `optimized_k_rr_grounded` | completed | 10 | 60.0 | 90.0 | 39686.9 |
| `optimized_s` | completed | 10 | 70.0 | 80.0 | 2103.6 |
| `optimized_s_grounded` | completed | 10 | 90.0 | 70.0 | 2364.6 |
| `optimized_s_rr` | completed | 10 | 70.0 | 70.0 | 2191.6 |
| `optimized_s_rr_grounded` | completed | 10 | 60.0 | 60.0 | 2489.1 |
