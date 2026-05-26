# Resumen de evaluación `run_20260517_183433_multi_qa_mini_ms_marco_l12_b58d259e`

- Inicio: `2026-05-17T18:34:33`
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
| `no_rag` | completed | 10 | 70.0 | 0.0 | 335.2 |
| `baseline_k` | completed | 10 | 50.0 | 70.0 | 18991.1 |
| `baseline_k_grounded` | completed | 10 | 50.0 | 70.0 | 18904.9 |
| `baseline_k_rr` | completed | 10 | 60.0 | 70.0 | 15556.5 |
| `baseline_k_rr_grounded` | completed | 10 | 50.0 | 80.0 | 15637.1 |
| `baseline_s` | completed | 10 | 70.0 | 70.0 | 1155.7 |
| `baseline_s_grounded` | completed | 10 | 70.0 | 100.0 | 1059.6 |
| `baseline_s_rr` | completed | 10 | 80.0 | 80.0 | 1188.3 |
| `baseline_s_rr_grounded` | completed | 10 | 100.0 | 100.0 | 1130.3 |
| `optimized_k` | completed | 10 | 60.0 | 90.0 | 33398.2 |
| `optimized_k_grounded` | completed | 10 | 100.0 | 100.0 | 33047.6 |
| `optimized_k_rr` | completed | 10 | 40.0 | 80.0 | 39923.1 |
| `optimized_k_rr_grounded` | completed | 10 | 60.0 | 90.0 | 39737.9 |
| `optimized_s` | completed | 10 | 80.0 | 80.0 | 1443.9 |
| `optimized_s_grounded` | completed | 10 | 70.0 | 90.0 | 1378.5 |
| `optimized_s_rr` | completed | 10 | 90.0 | 90.0 | 1422.9 |
| `optimized_s_rr_grounded` | completed | 10 | 90.0 | 90.0 | 1402.5 |
