# Resumen de evaluación `run_20260517_183813_multi_qa_mini_ms_marco_l6_ea7e1a8d`

- Inicio: `2026-05-17T18:38:13`
- Fin: `2026-05-22T04:15:20`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `llama3_8b__multi-qa-mini__ms-marco-L6`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 70.0 | 0.0 | 334.6 |
| `baseline_k` | completed | 10 | 30.0 | 40.0 | 18988.5 |
| `baseline_k_grounded` | completed | 10 | 40.0 | 70.0 | 18902.9 |
| `baseline_k_rr` | completed | 10 | 60.0 | 70.0 | 15456.0 |
| `baseline_k_rr_grounded` | completed | 10 | 60.0 | 100.0 | 15380.1 |
| `baseline_s` | completed | 10 | 70.0 | 80.0 | 1155.0 |
| `baseline_s_grounded` | completed | 10 | 70.0 | 90.0 | 1059.0 |
| `baseline_s_rr` | completed | 10 | 100.0 | 100.0 | 1182.1 |
| `baseline_s_rr_grounded` | completed | 10 | 80.0 | 90.0 | 1124.7 |
| `optimized_k` | completed | 10 | 40.0 | 40.0 | 33398.0 |
| `optimized_k_grounded` | completed | 10 | 50.0 | 100.0 | 33051.7 |
| `optimized_k_rr` | completed | 10 | 50.0 | 92.0 | 40161.9 |
| `optimized_k_rr_grounded` | completed | 10 | 90.0 | 90.0 | 39640.6 |
| `optimized_s` | completed | 10 | 80.0 | 80.0 | 1449.5 |
| `optimized_s_grounded` | completed | 10 | 90.0 | 90.0 | 1376.3 |
| `optimized_s_rr` | completed | 10 | 80.0 | 80.0 | 1415.3 |
| `optimized_s_rr_grounded` | completed | 10 | 80.0 | 80.0 | 1425.4 |
