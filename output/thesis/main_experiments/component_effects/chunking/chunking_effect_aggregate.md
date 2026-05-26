# Efecto aislado: chunking (agregado)

Cada fila promedia los runs de una misma pareja (media aritmética). `n_paired` es la suma de muestras emparejadas en todos los runs del grupo.

Threshold mínimo: **600** muestras emparejadas.

| Pareja | n_runs | n_paired | ΔCorrect. | ΔFaith. | ΔAnsRel. | ΔCtxSup. | ΔGlobal | Soporta % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `baseline_s -> optimized_s` | 10 | 6250 | -1,66 | -0,69 | -0,45 | -0,60 | -1,41 | 60% |
| `baseline_s_rr -> optimized_s_rr` | 10 | 6250 | -2,27 | -1,18 | -0,27 | -1,48 | -1,83 | 40% |
| `baseline_s_rr_grounded -> optimized_s_rr_grounded` | 10 | 6250 | -1,31 | -1,21 | -0,33 | -0,79 | -1,24 | 70% |
