# Efecto aislado: re-ranking (agregado)

Cada fila promedia los runs de una misma pareja (media aritmética). `n_paired` es la suma de muestras emparejadas en todos los runs del grupo.

Threshold mínimo: **600** muestras emparejadas.

| Pareja | n_runs | n_paired | ΔCorrect. | ΔFaith. | ΔAnsRel. | ΔCtxSup. | ΔGlobal | Soporta % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `baseline_s -> baseline_s_rr` | 10 | 6250 | +6,36 | +4,09 | +1,56 | +5,83 | +5,81 | 100% |
| `optimized_s -> optimized_s_rr` | 10 | 6250 | +5,75 | +3,61 | +1,74 | +4,96 | +5,39 | 100% |
