# Resumen de evaluación `run_20260517_183039_bge_base_bge_reranker_8bfa0122`

- Inicio: `2026-05-17T18:30:39`
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
| `no_rag` | completed | 10 | 70.0 | 0.0 | 372.4 |
| `baseline_k` | completed | 10 | 30.0 | 40.0 | 18833.9 |
| `baseline_k_grounded` | completed | 10 | 30.0 | 70.0 | 18903.2 |
| `baseline_k_rr` | completed | 10 | 60.0 | 50.0 | 16452.1 |
| `baseline_k_rr_grounded` | completed | 10 | 90.0 | 90.0 | 15727.4 |
| `baseline_s` | completed | 10 | 60.0 | 70.0 | 1604.0 |
| `baseline_s_grounded` | completed | 10 | 100.0 | 100.0 | 1595.4 |
| `baseline_s_rr` | completed | 10 | 80.0 | 80.0 | 1703.3 |
| `baseline_s_rr_grounded` | completed | 10 | 70.0 | 90.0 | 1758.8 |
| `optimized_k` | completed | 10 | 40.0 | 50.0 | 33392.3 |
| `optimized_k_grounded` | completed | 10 | 100.0 | 100.0 | 33048.2 |
| `optimized_k_rr` | completed | 10 | 60.0 | 90.0 | 39934.1 |
| `optimized_k_rr_grounded` | completed | 10 | 50.0 | 100.0 | 39677.3 |
| `optimized_s` | completed | 10 | 60.0 | 78.0 | 2113.2 |
| `optimized_s_grounded` | completed | 10 | 90.0 | 82.0 | 2337.0 |
| `optimized_s_rr` | completed | 10 | 80.0 | 80.0 | 2308.8 |
| `optimized_s_rr_grounded` | completed | 10 | 80.0 | 90.0 | 2335.3 |
