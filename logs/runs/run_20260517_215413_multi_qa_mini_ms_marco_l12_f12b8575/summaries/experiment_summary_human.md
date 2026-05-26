# Resumen de evaluación `run_20260517_215413_multi_qa_mini_ms_marco_l12_f12b8575`

- Inicio: `2026-05-17T21:54:13`
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
| `no_rag` | completed | 10 | 80.0 | 0.0 | 425.9 |
| `baseline_k` | completed | 10 | 40.0 | 60.0 | 18643.6 |
| `baseline_k_grounded` | completed | 10 | 80.0 | 80.0 | 18623.1 |
| `baseline_k_rr` | completed | 10 | 50.0 | 90.0 | 15292.6 |
| `baseline_k_rr_grounded` | completed | 10 | 50.0 | 90.0 | 15205.2 |
| `baseline_s` | completed | 10 | 80.0 | 100.0 | 972.6 |
| `baseline_s_grounded` | completed | 10 | 70.0 | 88.0 | 897.6 |
| `baseline_s_rr` | completed | 10 | 80.0 | 90.0 | 1062.3 |
| `baseline_s_rr_grounded` | completed | 10 | 80.0 | 80.0 | 1113.3 |
| `optimized_k` | completed | 10 | 40.0 | 50.0 | 33053.4 |
| `optimized_k_grounded` | completed | 10 | 100.0 | 100.0 | 32957.1 |
| `optimized_k_rr` | completed | 10 | 40.0 | 90.0 | 39677.9 |
| `optimized_k_rr_grounded` | completed | 10 | 50.0 | 80.0 | 39546.3 |
| `optimized_s` | completed | 10 | 90.0 | 98.0 | 1308.7 |
| `optimized_s_grounded` | completed | 10 | 90.0 | 89.0 | 1187.6 |
| `optimized_s_rr` | completed | 10 | 90.0 | 88.0 | 1330.7 |
| `optimized_s_rr_grounded` | completed | 10 | 80.0 | 90.0 | 1309.9 |
