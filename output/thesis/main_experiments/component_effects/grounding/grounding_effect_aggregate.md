# Efecto aislado: prompt grounded (agregado)

Cada fila promedia los runs de una misma pareja (media aritmética). `n_paired` es la suma de muestras emparejadas en todos los runs del grupo.

Threshold mínimo: **600** muestras emparejadas.

| Pareja | n_runs | n_paired | ΔCorrect. | ΔFaith. | ΔAnsRel. | ΔCtxSup. | ΔGlobal | Soporta % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `baseline_s_rr -> baseline_s_rr_grounded` | 10 | 6250 | -1,22 | +3,56 | +2,27 | +0,78 | -1,11 | 10% |
| `optimized_s_rr -> optimized_s_rr_grounded` | 10 | 6250 | -0,25 | +3,53 | +2,21 | +1,46 | -0,52 | 0% |
