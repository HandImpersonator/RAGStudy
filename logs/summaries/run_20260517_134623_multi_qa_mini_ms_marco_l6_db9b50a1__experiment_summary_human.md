# Resumen de evaluación `run_20260517_134623_multi_qa_mini_ms_marco_l6_db9b50a1`

- Inicio: `2026-05-17T13:46:23`
- Fin: `2026-05-22T04:15:20`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `llama3.2_latest__multi-qa-mini__ms-marco-L6`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 80.0 | 0.0 | 288.8 |
| `baseline_k` | completed | 10 | 50.0 | 66.0 | 18743.5 |
| `baseline_k_grounded` | completed | 10 | 20.0 | 80.0 | 18606.5 |
| `baseline_k_rr` | completed | 10 | 70.0 | 60.0 | 15244.6 |
| `baseline_k_rr_grounded` | completed | 10 | 60.0 | 100.0 | 15140.4 |
| `baseline_s` | completed | 10 | 80.0 | 80.0 | 948.9 |
| `baseline_s_grounded` | completed | 10 | 80.0 | 100.0 | 833.1 |
| `baseline_s_rr` | completed | 10 | 80.0 | 73.0 | 982.1 |
| `baseline_s_rr_grounded` | completed | 10 | 80.0 | 90.0 | 900.8 |
| `optimized_k` | completed | 10 | 40.0 | 80.0 | 33026.4 |
| `optimized_k_grounded` | completed | 10 | 100.0 | 99.0 | 32920.1 |
| `optimized_k_rr` | completed | 10 | 60.0 | 50.0 | 39612.9 |
| `optimized_k_rr_grounded` | completed | 10 | 60.0 | 100.0 | 39464.6 |
| `optimized_s` | completed | 10 | 70.0 | 80.0 | 1232.4 |
| `optimized_s_grounded` | completed | 10 | 80.0 | 90.0 | 1133.6 |
| `optimized_s_rr` | completed | 10 | 70.0 | 80.0 | 1185.5 |
| `optimized_s_rr_grounded` | completed | 10 | 90.0 | 90.0 | 1207.3 |
