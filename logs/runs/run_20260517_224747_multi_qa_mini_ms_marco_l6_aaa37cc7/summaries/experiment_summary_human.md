# Resumen de evaluación `run_20260517_224747_multi_qa_mini_ms_marco_l6_aaa37cc7`

- Inicio: `2026-05-17T22:47:47`
- Fin: `2026-05-22T04:15:21`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `mistral_7b__multi-qa-mini__ms-marco-L6`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 70.0 | 0.0 | 419.7 |
| `baseline_k` | completed | 10 | 30.0 | 60.0 | 18636.3 |
| `baseline_k_grounded` | completed | 10 | 70.0 | 80.0 | 18616.8 |
| `baseline_k_rr` | completed | 10 | 70.0 | 78.0 | 15312.1 |
| `baseline_k_rr_grounded` | completed | 10 | 90.0 | 50.0 | 15141.6 |
| `baseline_s` | completed | 10 | 70.0 | 100.0 | 969.1 |
| `baseline_s_grounded` | completed | 10 | 60.0 | 100.0 | 896.5 |
| `baseline_s_rr` | completed | 10 | 90.0 | 90.0 | 1024.5 |
| `baseline_s_rr_grounded` | completed | 10 | 80.0 | 80.0 | 1060.8 |
| `optimized_k` | completed | 10 | 50.0 | 60.0 | 33050.8 |
| `optimized_k_grounded` | completed | 10 | 100.0 | 100.0 | 32960.1 |
| `optimized_k_rr` | completed | 10 | 60.0 | 90.0 | 39624.7 |
| `optimized_k_rr_grounded` | completed | 10 | 80.0 | 100.0 | 39455.2 |
| `optimized_s` | completed | 10 | 90.0 | 100.0 | 1305.5 |
| `optimized_s_grounded` | completed | 10 | 70.0 | 99.0 | 1190.1 |
| `optimized_s_rr` | completed | 10 | 90.0 | 88.0 | 1219.9 |
| `optimized_s_rr_grounded` | completed | 10 | 90.0 | 90.0 | 1264.5 |
