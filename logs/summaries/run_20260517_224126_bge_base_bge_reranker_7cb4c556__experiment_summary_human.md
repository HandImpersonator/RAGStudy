# Resumen de evaluación `run_20260517_224126_bge_base_bge_reranker_7cb4c556`

- Inicio: `2026-05-17T22:41:26`
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
| `no_rag` | completed | 10 | 80.0 | 0.0 | 422.9 |
| `baseline_k` | completed | 10 | 40.0 | 40.0 | 18636.7 |
| `baseline_k_grounded` | completed | 10 | 70.0 | 70.0 | 18618.7 |
| `baseline_k_rr` | completed | 10 | 60.0 | 80.0 | 15515.6 |
| `baseline_k_rr_grounded` | completed | 10 | 70.0 | 92.0 | 15370.7 |
| `baseline_s` | completed | 10 | 70.0 | 62.0 | 1398.7 |
| `baseline_s_grounded` | completed | 10 | 80.0 | 90.0 | 1311.8 |
| `baseline_s_rr` | completed | 10 | 80.0 | 90.0 | 1437.4 |
| `baseline_s_rr_grounded` | completed | 10 | 80.0 | 90.0 | 1430.3 |
| `optimized_k` | completed | 10 | 40.0 | 50.0 | 33050.1 |
| `optimized_k_grounded` | completed | 10 | 40.0 | 100.0 | 32956.3 |
| `optimized_k_rr` | completed | 10 | 50.0 | 70.0 | 39797.3 |
| `optimized_k_rr_grounded` | completed | 10 | 40.0 | 80.0 | 39646.7 |
| `optimized_s` | completed | 10 | 70.0 | 70.0 | 2009.0 |
| `optimized_s_grounded` | completed | 10 | 70.0 | 90.0 | 2035.2 |
| `optimized_s_rr` | completed | 10 | 78.5 | 86.5 | 2251.6 |
| `optimized_s_rr_grounded` | completed | 10 | 80.0 | 90.0 | 2194.4 |
