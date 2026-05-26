# Resumen de evaluación `run_20260517_220034_multi_qa_mini_bge_reranker_4f7f5dcc`

- Inicio: `2026-05-17T22:00:34`
- Fin: `2026-05-22T04:15:21`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `mistral_7b__multi-qa-mini__bge-reranker`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 70.0 | 0.0 | 421.9 |
| `baseline_k` | completed | 10 | 40.0 | 60.0 | 18637.0 |
| `baseline_k_grounded` | completed | 10 | 30.0 | 80.0 | 18618.4 |
| `baseline_k_rr` | completed | 10 | 60.0 | 88.0 | 15516.3 |
| `baseline_k_rr_grounded` | completed | 10 | 60.0 | 90.0 | 15369.2 |
| `baseline_s` | completed | 10 | 70.0 | 100.0 | 969.3 |
| `baseline_s_grounded` | completed | 10 | 80.0 | 100.0 | 896.7 |
| `baseline_s_rr` | completed | 10 | 100.0 | 100.0 | 1153.6 |
| `baseline_s_rr_grounded` | completed | 10 | 80.0 | 90.0 | 1245.7 |
| `optimized_k` | completed | 10 | 50.0 | 50.0 | 33056.8 |
| `optimized_k_grounded` | completed | 10 | 100.0 | 50.0 | 32961.5 |
| `optimized_k_rr` | completed | 10 | 50.0 | 82.0 | 39801.7 |
| `optimized_k_rr_grounded` | completed | 10 | 50.0 | 100.0 | 39649.9 |
| `optimized_s` | completed | 10 | 80.0 | 90.0 | 1309.7 |
| `optimized_s_grounded` | completed | 10 | 80.0 | 89.0 | 1191.0 |
| `optimized_s_rr` | completed | 10 | 70.0 | 80.0 | 1471.8 |
| `optimized_s_rr_grounded` | completed | 10 | 70.0 | 80.0 | 1367.9 |
