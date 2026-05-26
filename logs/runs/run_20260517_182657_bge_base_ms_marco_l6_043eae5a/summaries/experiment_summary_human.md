# Resumen de evaluación `run_20260517_182657_bge_base_ms_marco_l6_043eae5a`

- Inicio: `2026-05-17T18:26:57`
- Fin: `2026-05-22T04:15:20`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `llama3_8b__bge-base__ms-marco-L6`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 70.0 | 0.0 | 368.4 |
| `baseline_k` | completed | 10 | 30.0 | 30.0 | 18838.5 |
| `baseline_k_grounded` | completed | 10 | 70.0 | 80.0 | 18822.9 |
| `baseline_k_rr` | completed | 10 | 60.0 | 70.0 | 15595.4 |
| `baseline_k_rr_grounded` | completed | 10 | 60.0 | 100.0 | 15379.3 |
| `baseline_s` | completed | 10 | 60.0 | 70.0 | 1602.2 |
| `baseline_s_grounded` | completed | 10 | 91.0 | 92.0 | 1620.5 |
| `baseline_s_rr` | completed | 10 | 90.0 | 90.0 | 1613.9 |
| `baseline_s_rr_grounded` | completed | 10 | 90.0 | 99.0 | 1497.2 |
| `optimized_k` | completed | 10 | 40.0 | 40.0 | 33340.2 |
| `optimized_k_grounded` | completed | 10 | 100.0 | 100.0 | 32992.4 |
| `optimized_k_rr` | completed | 10 | 50.0 | 70.0 | 39726.4 |
| `optimized_k_rr_grounded` | completed | 10 | 90.0 | 90.0 | 39625.7 |
| `optimized_s` | completed | 10 | 70.0 | 78.0 | 2108.6 |
| `optimized_s_grounded` | completed | 10 | 90.0 | 82.0 | 2369.1 |
| `optimized_s_rr` | completed | 10 | 60.0 | 72.0 | 2203.7 |
| `optimized_s_rr_grounded` | completed | 10 | 80.0 | 80.0 | 2318.5 |
