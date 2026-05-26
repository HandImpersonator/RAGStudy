# Resumen de evaluación `run_20260517_211323_multi_qa_mini_bge_reranker_34bee2e9`

- Inicio: `2026-05-17T21:13:23`
- Fin: `2026-05-22T04:15:21`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `llama3_8b__multi-qa-mini__bge-reranker`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 70.0 | 0.0 | 366.0 |
| `baseline_k` | completed | 10 | 40.0 | 50.0 | 18832.1 |
| `baseline_k_grounded` | completed | 10 | 70.0 | 80.0 | 18819.6 |
| `baseline_k_rr` | completed | 10 | 60.0 | 60.0 | 15647.1 |
| `baseline_k_rr_grounded` | completed | 10 | 90.0 | 90.0 | 15635.7 |
| `baseline_s` | completed | 10 | 70.0 | 70.0 | 1082.6 |
| `baseline_s_grounded` | completed | 10 | 70.0 | 90.0 | 1089.1 |
| `baseline_s_rr` | completed | 10 | 70.0 | 90.0 | 1332.3 |
| `baseline_s_rr_grounded` | completed | 10 | 90.0 | 80.0 | 1421.5 |
| `optimized_k` | completed | 10 | 50.0 | 50.0 | 33347.9 |
| `optimized_k_grounded` | completed | 10 | 50.0 | 100.0 | 32992.1 |
| `optimized_k_rr` | completed | 10 | 60.0 | 70.0 | 39963.6 |
| `optimized_k_rr_grounded` | completed | 10 | 50.0 | 100.0 | 39717.1 |
| `optimized_s` | completed | 10 | 70.0 | 86.0 | 1406.6 |
| `optimized_s_grounded` | completed | 10 | 70.0 | 82.0 | 1350.3 |
| `optimized_s_rr` | completed | 10 | 70.0 | 70.0 | 1543.9 |
| `optimized_s_rr_grounded` | completed | 10 | 70.0 | 72.0 | 1586.9 |
