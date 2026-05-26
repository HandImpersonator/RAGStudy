# Resumen de evaluación `run_20260517_225055_multi_qa_mini_bge_reranker_0badde3a`

- Inicio: `2026-05-17T22:50:55`
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
| `no_rag` | completed | 10 | 80.0 | 0.0 | 421.2 |
| `baseline_k` | completed | 10 | 30.0 | 60.0 | 18637.0 |
| `baseline_k_grounded` | completed | 10 | 80.0 | 80.0 | 18616.9 |
| `baseline_k_rr` | completed | 10 | 50.0 | 96.0 | 15514.3 |
| `baseline_k_rr_grounded` | completed | 10 | 50.0 | 90.0 | 15369.1 |
| `baseline_s` | completed | 10 | 70.0 | 100.0 | 969.3 |
| `baseline_s_grounded` | completed | 10 | 60.0 | 90.0 | 895.7 |
| `baseline_s_rr` | completed | 10 | 100.0 | 100.0 | 1153.4 |
| `baseline_s_rr_grounded` | completed | 10 | 100.0 | 100.0 | 1243.3 |
| `optimized_k` | completed | 10 | 40.0 | 60.0 | 33054.5 |
| `optimized_k_grounded` | completed | 10 | 60.0 | 100.0 | 32958.0 |
| `optimized_k_rr` | completed | 10 | 40.0 | 40.0 | 39799.0 |
| `optimized_k_rr_grounded` | completed | 10 | 40.0 | 100.0 | 39646.5 |
| `optimized_s` | completed | 10 | 80.0 | 100.0 | 1306.9 |
| `optimized_s_grounded` | completed | 10 | 100.0 | 100.0 | 1188.7 |
| `optimized_s_rr` | completed | 10 | 70.0 | 80.0 | 1456.8 |
| `optimized_s_rr_grounded` | completed | 10 | 70.0 | 80.0 | 1364.0 |
