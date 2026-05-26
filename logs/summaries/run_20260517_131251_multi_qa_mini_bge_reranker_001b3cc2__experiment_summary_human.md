# Resumen de evaluación `run_20260517_131251_multi_qa_mini_bge_reranker_001b3cc2`

- Inicio: `2026-05-17T13:12:51`
- Fin: `2026-05-22T04:15:19`
- Dataset: `triviaqa`
- Modo: `real`
- Modelo pipeline: `llama3.2_latest__multi-qa-mini__bge-reranker`
- Estado de evaluación: **completed**
- Juez LLM: `gpt-5.4-mini`
- Muestras evaluadas: 170/170 (100.0%)

## Configuraciones

| Config | Estado Eval | Muestras | Correctness | Faithfulness | Latencia (ms) |
|---|---|---|---|---|---|
| `no_rag` | completed | 10 | 70.0 | 0.0 | 297.7 |
| `baseline_k` | completed | 10 | 90.0 | 66.0 | 18749.5 |
| `baseline_k_grounded` | completed | 10 | 20.0 | 80.0 | 18613.2 |
| `baseline_k_rr` | completed | 10 | 50.0 | 50.0 | 15445.5 |
| `baseline_k_rr_grounded` | completed | 10 | 60.0 | 100.0 | 15273.9 |
| `baseline_s` | completed | 10 | 80.0 | 90.0 | 956.5 |
| `baseline_s_grounded` | completed | 10 | 70.0 | 90.0 | 842.3 |
| `baseline_s_rr` | completed | 10 | 90.0 | 97.0 | 1070.5 |
| `baseline_s_rr_grounded` | completed | 10 | 100.0 | 100.0 | 1057.5 |
| `optimized_k` | completed | 10 | 40.0 | 80.0 | 33037.2 |
| `optimized_k_grounded` | completed | 10 | 50.0 | 98.0 | 32935.4 |
| `optimized_k_rr` | completed | 10 | 50.0 | 50.0 | 39710.6 |
| `optimized_k_rr_grounded` | completed | 10 | 40.0 | 90.0 | 39664.6 |
| `optimized_s` | completed | 10 | 60.0 | 70.0 | 1243.3 |
| `optimized_s_grounded` | completed | 10 | 80.0 | 80.0 | 1136.5 |
| `optimized_s_rr` | completed | 10 | 70.0 | 60.0 | 1505.2 |
| `optimized_s_rr_grounded` | completed | 10 | 70.0 | 80.0 | 1334.8 |
