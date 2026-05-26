# Resumen de evaluación `run_20260517_134318_multi_qa_mini_ms_marco_l12_1c694c38`

- Inicio: `2026-05-17T13:43:18`
- Fin: `2026-05-22T04:15:19`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `llama3.2_latest__multi-qa-mini__ms-marco-L12`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 80.0 | 0.0 | 294.4 |
| `baseline_k` | completed | 10 | 58.0 | 78.0 | 18752.5 |
| `baseline_k_grounded` | completed | 10 | 20.0 | 80.0 | 18608.7 |
| `baseline_k_rr` | completed | 10 | 50.0 | 40.0 | 15293.1 |
| `baseline_k_rr_grounded` | completed | 10 | 50.0 | 100.0 | 15160.8 |
| `baseline_s` | completed | 10 | 80.0 | 90.0 | 959.1 |
| `baseline_s_grounded` | completed | 10 | 70.0 | 94.0 | 837.4 |
| `baseline_s_rr` | completed | 10 | 80.0 | 90.0 | 934.2 |
| `baseline_s_rr_grounded` | completed | 10 | 90.0 | 90.0 | 931.1 |
| `optimized_k` | completed | 10 | 60.0 | 30.0 | 33030.8 |
| `optimized_k_grounded` | completed | 10 | 50.0 | 90.0 | 32926.0 |
| `optimized_k_rr` | completed | 10 | 40.0 | 60.0 | 39585.8 |
| `optimized_k_rr_grounded` | completed | 10 | 100.0 | 90.0 | 39882.1 |
| `optimized_s` | completed | 10 | 80.0 | 79.0 | 1237.0 |
| `optimized_s_grounded` | completed | 10 | 80.0 | 80.0 | 1136.3 |
| `optimized_s_rr` | completed | 10 | 80.0 | 70.0 | 1272.4 |
| `optimized_s_rr_grounded` | completed | 10 | 70.0 | 80.0 | 1264.7 |
