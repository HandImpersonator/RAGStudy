# Resumen de evaluación `run_20260517_215058_bge_base_bge_reranker_6d67b373`

- Inicio: `2026-05-17T21:50:58`
- Fin: `2026-05-22T04:15:21`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `mistral_7b__bge-base__bge-reranker`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 80.0 | 0.0 | 423.4 |
| `baseline_k` | completed | 10 | 40.0 | 60.0 | 18638.2 |
| `baseline_k_grounded` | completed | 10 | 80.0 | 80.0 | 18621.2 |
| `baseline_k_rr` | completed | 10 | 60.0 | 80.0 | 15515.8 |
| `baseline_k_rr_grounded` | completed | 10 | 50.0 | 92.0 | 15372.3 |
| `baseline_s` | completed | 10 | 60.0 | 60.0 | 1400.9 |
| `baseline_s_grounded` | completed | 10 | 60.0 | 100.0 | 1316.8 |
| `baseline_s_rr` | completed | 10 | 80.0 | 90.0 | 1438.7 |
| `baseline_s_rr_grounded` | completed | 10 | 80.0 | 90.0 | 1434.1 |
| `optimized_k` | completed | 10 | 50.0 | 50.0 | 33052.9 |
| `optimized_k_grounded` | completed | 10 | 40.0 | 100.0 | 32962.3 |
| `optimized_k_rr` | completed | 10 | 50.0 | 50.0 | 39803.7 |
| `optimized_k_rr_grounded` | completed | 10 | 40.0 | 80.0 | 39651.5 |
| `optimized_s` | completed | 10 | 70.0 | 70.0 | 2013.9 |
| `optimized_s_grounded` | completed | 10 | 70.0 | 90.0 | 2038.1 |
| `optimized_s_rr` | completed | 10 | 75.5 | 91.0 | 2255.9 |
| `optimized_s_rr_grounded` | completed | 10 | 90.0 | 98.0 | 2199.3 |
