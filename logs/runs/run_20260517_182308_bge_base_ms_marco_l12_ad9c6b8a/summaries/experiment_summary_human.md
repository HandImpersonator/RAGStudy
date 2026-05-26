# Resumen de evaluación `run_20260517_182308_bge_base_ms_marco_l12_ad9c6b8a`

- Inicio: `2026-05-17T18:23:08`
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
| `no_rag` | completed | 10 | 70.0 | 0.0 | 820.2 |
| `baseline_k` | completed | 10 | 30.0 | 42.0 | 18837.3 |
| `baseline_k_grounded` | completed | 10 | 70.0 | 80.0 | 18822.2 |
| `baseline_k_rr` | completed | 10 | 60.0 | 99.0 | 15538.2 |
| `baseline_k_rr_grounded` | completed | 10 | 50.0 | 90.0 | 15443.5 |
| `baseline_s` | completed | 10 | 50.0 | 60.0 | 1600.9 |
| `baseline_s_grounded` | completed | 10 | 60.0 | 94.0 | 1622.8 |
| `baseline_s_rr` | completed | 10 | 70.0 | 62.0 | 1643.3 |
| `baseline_s_rr_grounded` | completed | 10 | 81.5 | 91.0 | 1643.6 |
| `optimized_k` | completed | 10 | 50.0 | 80.0 | 33339.8 |
| `optimized_k_grounded` | completed | 10 | 40.0 | 100.0 | 32991.4 |
| `optimized_k_rr` | completed | 10 | 50.0 | 100.0 | 39824.6 |
| `optimized_k_rr_grounded` | completed | 10 | 60.0 | 90.0 | 39685.6 |
| `optimized_s` | completed | 10 | 70.0 | 10.0 | 2107.3 |
| `optimized_s_grounded` | completed | 10 | 90.0 | 90.0 | 2368.0 |
| `optimized_s_rr` | completed | 10 | 70.0 | 66.0 | 2192.5 |
| `optimized_s_rr_grounded` | completed | 10 | 60.0 | 50.0 | 2495.4 |
