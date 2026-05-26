# Resumen de evaluación `run_20260517_215723_multi_qa_mini_ms_marco_l6_234a219d`

- Inicio: `2026-05-17T21:57:23`
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
| `no_rag` | completed | 10 | 70.0 | 0.0 | 425.5 |
| `baseline_k` | completed | 10 | 40.0 | 60.0 | 18639.7 |
| `baseline_k_grounded` | completed | 10 | 30.0 | 80.0 | 18617.8 |
| `baseline_k_rr` | completed | 10 | 60.0 | 60.0 | 15313.2 |
| `baseline_k_rr_grounded` | completed | 10 | 60.0 | 90.0 | 15141.8 |
| `baseline_s` | completed | 10 | 70.0 | 100.0 | 972.5 |
| `baseline_s_grounded` | completed | 10 | 60.0 | 89.0 | 897.3 |
| `baseline_s_rr` | completed | 10 | 90.0 | 90.0 | 1025.5 |
| `baseline_s_rr_grounded` | completed | 10 | 80.0 | 90.0 | 1062.7 |
| `optimized_k` | completed | 10 | 40.0 | 50.0 | 33052.5 |
| `optimized_k_grounded` | completed | 10 | 100.0 | 100.0 | 32959.4 |
| `optimized_k_rr` | completed | 10 | 60.0 | 90.0 | 39631.3 |
| `optimized_k_rr_grounded` | completed | 10 | 100.0 | 100.0 | 39445.1 |
| `optimized_s` | completed | 10 | 80.0 | 90.0 | 1310.8 |
| `optimized_s_grounded` | completed | 10 | 70.0 | 100.0 | 1190.9 |
| `optimized_s_rr` | completed | 10 | 90.0 | 82.0 | 1223.7 |
| `optimized_s_rr_grounded` | completed | 10 | 90.0 | 90.0 | 1265.1 |
