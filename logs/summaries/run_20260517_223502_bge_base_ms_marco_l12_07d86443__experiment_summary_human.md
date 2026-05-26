# Resumen de evaluación `run_20260517_223502_bge_base_ms_marco_l12_07d86443`

- Inicio: `2026-05-17T22:35:02`
- Fin: `2026-05-22T04:15:21`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `mistral_7b__bge-base__ms-marco-L12`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 80.0 | 0.0 | 712.1 |
| `baseline_k` | completed | 10 | 30.0 | 30.0 | 18638.8 |
| `baseline_k_grounded` | completed | 10 | 80.0 | 80.0 | 18617.2 |
| `baseline_k_rr` | completed | 10 | 50.0 | 90.0 | 15284.9 |
| `baseline_k_rr_grounded` | completed | 10 | 50.0 | 90.0 | 15201.2 |
| `baseline_s` | completed | 10 | 60.0 | 60.0 | 1399.3 |
| `baseline_s_grounded` | completed | 10 | 70.0 | 100.0 | 1312.3 |
| `baseline_s_rr` | completed | 10 | 70.0 | 90.0 | 1427.6 |
| `baseline_s_rr_grounded` | completed | 10 | 70.0 | 90.0 | 1424.8 |
| `optimized_k` | completed | 10 | 50.0 | 50.0 | 33049.7 |
| `optimized_k_grounded` | completed | 10 | 90.0 | 100.0 | 32957.1 |
| `optimized_k_rr` | completed | 10 | 50.0 | 88.0 | 39675.2 |
| `optimized_k_rr_grounded` | completed | 10 | 50.0 | 90.0 | 39544.8 |
| `optimized_s` | completed | 10 | 70.0 | 70.0 | 2009.2 |
| `optimized_s_grounded` | completed | 10 | 80.0 | 80.0 | 2032.1 |
| `optimized_s_rr` | completed | 10 | 80.0 | 90.0 | 2173.1 |
| `optimized_s_rr_grounded` | completed | 10 | 62.0 | 72.0 | 2099.3 |
