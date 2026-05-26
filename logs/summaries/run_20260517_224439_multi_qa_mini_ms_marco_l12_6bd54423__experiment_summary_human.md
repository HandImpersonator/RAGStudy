# Resumen de evaluación `run_20260517_224439_multi_qa_mini_ms_marco_l12_6bd54423`

- Inicio: `2026-05-17T22:44:39`
- Fin: `2026-05-22T04:15:21`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `mistral_7b__multi-qa-mini__ms-marco-L12`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 80.0 | 0.0 | 420.5 |
| `baseline_k` | completed | 10 | 40.0 | 60.0 | 18634.8 |
| `baseline_k_grounded` | completed | 10 | 70.0 | 70.0 | 18617.5 |
| `baseline_k_rr` | completed | 10 | 50.0 | 90.0 | 15286.1 |
| `baseline_k_rr_grounded` | completed | 10 | 50.0 | 90.0 | 15201.7 |
| `baseline_s` | completed | 10 | 70.0 | 100.0 | 967.5 |
| `baseline_s_grounded` | completed | 10 | 60.0 | 90.0 | 895.6 |
| `baseline_s_rr` | completed | 10 | 70.0 | 90.0 | 1059.1 |
| `baseline_s_rr_grounded` | completed | 10 | 80.0 | 90.0 | 1110.2 |
| `optimized_k` | completed | 10 | 40.0 | 50.0 | 33049.5 |
| `optimized_k_grounded` | completed | 10 | 90.0 | 90.0 | 32957.7 |
| `optimized_k_rr` | completed | 10 | 70.0 | 96.0 | 39674.1 |
| `optimized_k_rr_grounded` | completed | 10 | 80.0 | 80.0 | 39546.7 |
| `optimized_s` | completed | 10 | 80.0 | 100.0 | 1304.8 |
| `optimized_s_grounded` | completed | 10 | 80.0 | 99.0 | 1187.9 |
| `optimized_s_rr` | completed | 10 | 90.0 | 86.0 | 1328.3 |
| `optimized_s_rr_grounded` | completed | 10 | 80.0 | 80.0 | 1306.2 |
