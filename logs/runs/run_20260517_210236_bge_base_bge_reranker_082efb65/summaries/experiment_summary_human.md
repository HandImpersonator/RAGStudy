# Resumen de evaluación `run_20260517_210236_bge_base_bge_reranker_082efb65`

- Inicio: `2026-05-17T21:02:36`
- Fin: `2026-05-22T04:15:20`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `llama3_8b__bge-base__bge-reranker`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 70.0 | 0.0 | 368.0 |
| `baseline_k` | completed | 10 | 30.0 | 50.0 | 18831.0 |
| `baseline_k_grounded` | completed | 10 | 30.0 | 80.0 | 18817.6 |
| `baseline_k_rr` | completed | 10 | 60.0 | 60.0 | 15645.7 |
| `baseline_k_rr_grounded` | completed | 10 | 90.0 | 90.0 | 15637.8 |
| `baseline_s` | completed | 10 | 50.0 | 50.0 | 1604.5 |
| `baseline_s_grounded` | completed | 10 | 60.0 | 96.0 | 1619.1 |
| `baseline_s_rr` | completed | 10 | 80.0 | 79.0 | 1677.0 |
| `baseline_s_rr_grounded` | completed | 10 | 60.0 | 70.0 | 1725.8 |
| `optimized_k` | completed | 10 | 30.0 | 40.0 | 33339.8 |
| `optimized_k_grounded` | completed | 10 | 40.0 | 100.0 | 32987.1 |
| `optimized_k_rr` | completed | 10 | 50.0 | 50.0 | 39963.7 |
| `optimized_k_rr_grounded` | completed | 10 | 100.0 | 100.0 | 39715.7 |
| `optimized_s` | completed | 10 | 70.0 | 70.0 | 2104.0 |
| `optimized_s_grounded` | completed | 10 | 90.0 | 80.0 | 2361.7 |
| `optimized_s_rr` | completed | 10 | 80.0 | 80.0 | 2303.1 |
| `optimized_s_rr_grounded` | completed | 10 | 80.0 | 80.0 | 2372.3 |
