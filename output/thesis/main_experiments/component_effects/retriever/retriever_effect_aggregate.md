# Efecto aislado: retriever (BM25 vs FAISS) (agregado)

Cada fila promedia los runs de una misma pareja (media aritmética). `n_paired` es la suma de muestras emparejadas en todos los runs del grupo.

Threshold mínimo: **45** muestras emparejadas.

| Pareja | n_runs | n_paired | ΔCorrect. | ΔFaith. | ΔAnsRel. | ΔCtxSup. | ΔGlobal | Soporta % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `baseline_k -> baseline_s` | 6 | 300 | +3,60 | +3,13 | +4,77 | +4,73 | +2,77 | 100% |
| `baseline_k_rr -> baseline_s_rr` | 6 | 300 | +8,10 | +6,03 | +3,84 | +3,05 | +6,78 | 100% |
| `baseline_k_grounded -> baseline_s_grounded` | 6 | 300 | +2,00 | +0,28 | +3,27 | +5,27 | +0,93 | 67% |
| `baseline_k_rr_grounded -> baseline_s_rr_grounded` | 6 | 300 | +10,60 | +1,72 | +2,20 | +8,90 | +7,87 | 100% |
| `optimized_k -> optimized_s` | 6 | 300 | +19,97 | +10,88 | +13,98 | +27,73 | +18,15 | 100% |
| `optimized_k_rr -> optimized_s_rr` | 6 | 300 | +15,97 | +13,39 | +5,85 | +19,88 | +16,00 | 100% |
| `optimized_k_grounded -> optimized_s_grounded` | 6 | 300 | +15,47 | -1,67 | -0,48 | +25,73 | +12,68 | 100% |
| `optimized_k_rr_grounded -> optimized_s_rr_grounded` | 6 | 300 | +8,30 | -4,83 | -3,40 | +14,87 | +7,48 | 100% |
