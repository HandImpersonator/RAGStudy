# Resumen de evaluación `run_20260517_210619_multi_qa_mini_ms_marco_l12_64032a5f`

- Inicio: `2026-05-17T21:06:19`
- Fin: `2026-05-22T04:15:20`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `llama3_8b__multi-qa-mini__ms-marco-L12`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 70.0 | 0.0 | 365.9 |
| `baseline_k` | completed | 10 | 30.0 | 40.0 | 18827.5 |
| `baseline_k_grounded` | completed | 10 | 60.0 | 80.0 | 18815.5 |
| `baseline_k_rr` | completed | 10 | 61.0 | 61.0 | 15534.0 |
| `baseline_k_rr_grounded` | completed | 10 | 50.0 | 90.0 | 15435.4 |
| `baseline_s` | completed | 10 | 70.0 | 70.0 | 1080.7 |
| `baseline_s_grounded` | completed | 10 | 70.0 | 90.0 | 1082.7 |
| `baseline_s_rr` | completed | 10 | 70.0 | 80.0 | 1166.6 |
| `baseline_s_rr_grounded` | completed | 10 | 100.0 | 100.0 | 1132.6 |
| `optimized_k` | completed | 10 | 60.0 | 40.0 | 33337.5 |
| `optimized_k_grounded` | completed | 10 | 100.0 | 100.0 | 32988.0 |
| `optimized_k_rr` | completed | 10 | 50.0 | 70.0 | 39817.7 |
| `optimized_k_rr_grounded` | completed | 10 | 50.0 | 92.0 | 39684.4 |
| `optimized_s` | completed | 10 | 70.0 | 76.0 | 1402.9 |
| `optimized_s_grounded` | completed | 10 | 90.0 | 70.0 | 1347.9 |
| `optimized_s_rr` | completed | 10 | 90.5 | 90.5 | 1405.2 |
| `optimized_s_rr_grounded` | completed | 10 | 80.0 | 80.0 | 1408.4 |
