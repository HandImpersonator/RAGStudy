# Resumen de evaluación `run_20260517_130618_multi_qa_mini_ms_marco_l12_a39fd543`

- Inicio: `2026-05-17T13:06:18`
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
| `no_rag` | completed | 10 | 70.0 | 0.0 | 299.4 |
| `baseline_k` | completed | 10 | 92.0 | 74.0 | 18748.5 |
| `baseline_k_grounded` | completed | 10 | 20.0 | 80.0 | 18611.7 |
| `baseline_k_rr` | completed | 10 | 50.0 | 40.0 | 15284.5 |
| `baseline_k_rr_grounded` | completed | 10 | 50.0 | 90.0 | 15154.0 |
| `baseline_s` | completed | 10 | 80.0 | 90.0 | 961.5 |
| `baseline_s_grounded` | completed | 10 | 70.0 | 90.0 | 828.8 |
| `baseline_s_rr` | completed | 10 | 80.0 | 90.0 | 925.3 |
| `baseline_s_rr_grounded` | completed | 10 | 80.0 | 90.0 | 926.0 |
| `optimized_k` | completed | 10 | 30.0 | 80.0 | 33025.7 |
| `optimized_k_grounded` | completed | 10 | 50.0 | 90.0 | 32919.2 |
| `optimized_k_rr` | completed | 10 | 40.0 | 79.0 | 39585.1 |
| `optimized_k_rr_grounded` | completed | 10 | 100.0 | 80.0 | 39878.9 |
| `optimized_s` | completed | 10 | 70.0 | 74.5 | 1234.3 |
| `optimized_s_grounded` | completed | 10 | 70.0 | 80.0 | 1131.3 |
| `optimized_s_rr` | completed | 10 | 80.0 | 70.0 | 1268.0 |
| `optimized_s_rr_grounded` | completed | 10 | 80.0 | 80.0 | 1265.4 |
