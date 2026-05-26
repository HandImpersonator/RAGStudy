# Resumen de evaluación `run_20260517_210950_multi_qa_mini_ms_marco_l6_3be5dd4f`

- Inicio: `2026-05-17T21:09:50`
- Fin: `2026-05-22T04:15:21`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `llama3_8b__multi-qa-mini__ms-marco-L6`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 70.0 | 0.0 | 364.4 |
| `baseline_k` | completed | 10 | 30.0 | 40.0 | 18829.0 |
| `baseline_k_grounded` | completed | 10 | 40.0 | 80.0 | 18818.8 |
| `baseline_k_rr` | completed | 10 | 60.0 | 60.0 | 15581.0 |
| `baseline_k_rr_grounded` | completed | 10 | 60.0 | 100.0 | 15378.6 |
| `baseline_s` | completed | 10 | 70.0 | 70.0 | 1079.6 |
| `baseline_s_grounded` | completed | 10 | 70.0 | 90.0 | 1091.2 |
| `baseline_s_rr` | completed | 10 | 100.0 | 99.0 | 1173.4 |
| `baseline_s_rr_grounded` | completed | 10 | 100.0 | 100.0 | 1064.3 |
| `optimized_k` | completed | 10 | 50.0 | 90.0 | 33336.2 |
| `optimized_k_grounded` | completed | 10 | 50.0 | 100.0 | 32991.2 |
| `optimized_k_rr` | completed | 10 | 50.0 | 73.0 | 39723.8 |
| `optimized_k_rr_grounded` | completed | 10 | 90.0 | 90.0 | 39623.7 |
| `optimized_s` | completed | 10 | 70.0 | 85.0 | 1405.9 |
| `optimized_s_grounded` | completed | 10 | 70.0 | 82.0 | 1351.2 |
| `optimized_s_rr` | completed | 10 | 80.0 | 80.0 | 1412.1 |
| `optimized_s_rr_grounded` | completed | 10 | 90.0 | 90.0 | 1397.0 |
