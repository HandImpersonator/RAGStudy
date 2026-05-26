# Resumen de evaluación `run_20260517_133355_bge_base_ms_marco_l12_a3265af0`

- Inicio: `2026-05-17T13:33:55`
- Fin: `2026-05-22T04:15:19`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `llama3.2_latest__bge-base__ms-marco-L12`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 50.0 | 0.0 | 830.8 |
| `baseline_k` | completed | 10 | 50.0 | 92.0 | 18753.2 |
| `baseline_k_grounded` | completed | 10 | 80.0 | 80.0 | 18611.0 |
| `baseline_k_rr` | completed | 10 | 50.0 | 42.0 | 15293.5 |
| `baseline_k_rr_grounded` | completed | 10 | 50.0 | 90.0 | 15161.5 |
| `baseline_s` | completed | 10 | 50.0 | 58.0 | 1334.3 |
| `baseline_s_grounded` | completed | 10 | 70.0 | 90.0 | 1310.3 |
| `baseline_s_rr` | completed | 10 | 60.0 | 60.0 | 1319.7 |
| `baseline_s_rr_grounded` | completed | 10 | 70.0 | 90.0 | 1277.0 |
| `optimized_k` | completed | 10 | 40.0 | 40.0 | 33029.7 |
| `optimized_k_grounded` | completed | 10 | 40.0 | 90.0 | 32928.4 |
| `optimized_k_rr` | completed | 10 | 30.0 | 80.0 | 39592.4 |
| `optimized_k_rr_grounded` | completed | 10 | 100.0 | 100.0 | 39877.8 |
| `optimized_s` | completed | 10 | 60.0 | 69.5 | 1946.8 |
| `optimized_s_grounded` | completed | 10 | 70.0 | 82.0 | 1927.1 |
| `optimized_s_rr` | completed | 10 | 59.0 | 59.5 | 2011.4 |
| `optimized_s_rr_grounded` | completed | 10 | 70.0 | 80.0 | 2138.3 |
