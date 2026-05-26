# Resumen de evaluación `run_20260517_125619_bge_base_ms_marco_l12_c77af6d5`

- Inicio: `2026-05-17T12:56:19`
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
| `no_rag` | completed | 10 | 60.0 | 0.0 | 587.2 |
| `baseline_k` | completed | 10 | 100.0 | 88.5 | 18755.7 |
| `baseline_k_grounded` | completed | 10 | 20.0 | 80.0 | 18611.4 |
| `baseline_k_rr` | completed | 10 | 50.0 | 40.0 | 15286.8 |
| `baseline_k_rr_grounded` | completed | 10 | 90.0 | 90.0 | 15153.4 |
| `baseline_s` | completed | 10 | 60.0 | 80.0 | 1329.3 |
| `baseline_s_grounded` | completed | 10 | 70.0 | 90.0 | 1319.4 |
| `baseline_s_rr` | completed | 10 | 60.0 | 70.0 | 1311.8 |
| `baseline_s_rr_grounded` | completed | 10 | 70.0 | 90.0 | 1273.2 |
| `optimized_k` | completed | 10 | 30.0 | 80.0 | 33029.3 |
| `optimized_k_grounded` | completed | 10 | 50.0 | 90.0 | 32923.3 |
| `optimized_k_rr` | completed | 10 | 30.0 | 60.0 | 39585.7 |
| `optimized_k_rr_grounded` | completed | 10 | 100.0 | 100.0 | 39880.0 |
| `optimized_s` | completed | 10 | 60.0 | 71.5 | 1942.2 |
| `optimized_s_grounded` | completed | 10 | 71.0 | 80.0 | 1928.1 |
| `optimized_s_rr` | completed | 10 | 60.0 | 60.0 | 2010.5 |
| `optimized_s_rr_grounded` | completed | 10 | 60.0 | 80.0 | 2138.1 |
