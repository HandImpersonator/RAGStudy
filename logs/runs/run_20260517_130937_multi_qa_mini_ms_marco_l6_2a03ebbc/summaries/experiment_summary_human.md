# Resumen de evaluación `run_20260517_130937_multi_qa_mini_ms_marco_l6_2a03ebbc`

- Inicio: `2026-05-17T13:09:37`
- Fin: `2026-05-22T04:15:19`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `llama3.2_latest__multi-qa-mini__ms-marco-L6`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 80.0 | 0.0 | 296.1 |
| `baseline_k` | completed | 10 | 60.0 | 38.0 | 18743.7 |
| `baseline_k_grounded` | completed | 10 | 20.0 | 82.0 | 18602.2 |
| `baseline_k_rr` | completed | 10 | 60.0 | 60.0 | 15242.2 |
| `baseline_k_rr_grounded` | completed | 10 | 60.0 | 100.0 | 15140.0 |
| `baseline_s` | completed | 10 | 80.0 | 92.0 | 949.9 |
| `baseline_s_grounded` | completed | 10 | 70.0 | 90.0 | 830.2 |
| `baseline_s_rr` | completed | 10 | 80.0 | 84.0 | 980.7 |
| `baseline_s_rr_grounded` | completed | 10 | 80.0 | 90.0 | 897.3 |
| `optimized_k` | completed | 10 | 60.0 | 62.0 | 33025.5 |
| `optimized_k_grounded` | completed | 10 | 100.0 | 98.5 | 32921.7 |
| `optimized_k_rr` | completed | 10 | 60.0 | 60.0 | 39614.2 |
| `optimized_k_rr_grounded` | completed | 10 | 90.0 | 90.0 | 39465.4 |
| `optimized_s` | completed | 10 | 80.0 | 70.0 | 1234.4 |
| `optimized_s_grounded` | completed | 10 | 80.0 | 80.0 | 1132.6 |
| `optimized_s_rr` | completed | 10 | 88.0 | 78.0 | 1186.8 |
| `optimized_s_rr_grounded` | completed | 10 | 90.0 | 90.0 | 1206.3 |
