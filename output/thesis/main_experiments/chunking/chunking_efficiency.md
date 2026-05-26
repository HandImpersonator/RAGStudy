# Chunking efficiency: fixed (~512 chars) vs semantic (250-512 chars)

Runs escaneados: **52** · Pares analizados: **30**

Cada par mantiene constante el retriever y la variante.  Δ = **semántico − fijo** (negativo = semántico usa menos).  Calidad equivalente cuando |Δmedia| ≤ 2,00 pts en la escala 0-100 del juez LLM.

**Afirmación soportada cuando:** calidad preservada Y contexto reducido.

## Resumen

| Run | Retriever | Variante | n | avg_chunk Δ | context_chars Δ% | context_tokens_est Δ% | Exactitud Δ | Global Δ | Afirmación |
|---|---|---|---:|---:|---:|---:|---:|---:|:---:|
| `75120177` | `s` | `(none)` | 625 | -59,86 | -12,25% | -12,25% | -1,09 | -0,37 | [si] |
| `75120177` | `s` | `rr` | 625 | -73,57 | -14,65% | -14,65% | -2,81 | -2,03 | [no] |
| `75120177` | `s` | `rr_grounded` | 625 | -73,57 | -14,65% | -14,65% | -1,46 | -1,83 | [si] |
| `0ae208b6` | `s` | `(none)` | 625 | -59,86 | -12,25% | -12,25% | -2,14 | -1,87 | [no] |
| `0ae208b6` | `s` | `rr` | 625 | -73,57 | -14,65% | -14,65% | -2,88 | -1,88 | [no] |
| `0ae208b6` | `s` | `rr_grounded` | 625 | -73,57 | -14,65% | -14,65% | -1,28 | -1,51 | [si] |
| `1e8f339e` | `s` | `(none)` | 625 | -59,86 | -12,25% | -12,25% | -2,63 | -1,76 | [no] |
| `1e8f339e` | `s` | `rr` | 625 | -73,57 | -14,65% | -14,65% | -1,76 | -1,28 | [si] |
| `1e8f339e` | `s` | `rr_grounded` | 625 | -73,57 | -14,65% | -14,65% | -0,63 | -1,02 | [si] |
| `4818b378` | `s` | `(none)` | 625 | -59,86 | -12,25% | -12,25% | -2,58 | -1,46 | [no] |
| `4818b378` | `s` | `rr` | 625 | -73,57 | -14,65% | -14,65% | -1,99 | -1,75 | [si] |
| `4818b378` | `s` | `rr_grounded` | 625 | -73,57 | -14,65% | -14,65% | -0,89 | -0,62 | [si] |
| `ecfe2405` | `s` | `(none)` | 625 | -59,86 | -12,25% | -12,25% | -1,87 | -1,44 | [si] |
| `ecfe2405` | `s` | `rr` | 625 | -73,57 | -14,65% | -14,65% | -1,93 | -1,92 | [si] |
| `ecfe2405` | `s` | `rr_grounded` | 625 | -73,57 | -14,65% | -14,65% | +0,92 | +0,49 | [si] |
| `74a6f570` | `s` | `(none)` | 625 | -59,86 | -12,25% | -12,25% | -1,79 | -1,89 | [si] |
| `74a6f570` | `s` | `rr` | 625 | -73,57 | -14,65% | -14,65% | -2,72 | -2,72 | [no] |
| `74a6f570` | `s` | `rr_grounded` | 625 | -73,57 | -14,65% | -14,65% | -0,27 | -0,33 | [si] |
| `fedf0681` | `s` | `(none)` | 625 | -59,86 | -12,25% | -12,25% | -1,24 | -1,46 | [si] |
| `fedf0681` | `s` | `rr` | 625 | -73,57 | -14,65% | -14,65% | -2,71 | -2,00 | [no] |
| `fedf0681` | `s` | `rr_grounded` | 625 | -73,57 | -14,65% | -14,65% | -3,06 | -2,49 | [no] |
| `39fff400` | `s` | `(none)` | 625 | -59,86 | -12,25% | -12,25% | -1,72 | -1,55 | [si] |
| `39fff400` | `s` | `rr` | 625 | -73,57 | -14,65% | -14,65% | -1,37 | -1,03 | [si] |
| `39fff400` | `s` | `rr_grounded` | 625 | -73,57 | -14,65% | -14,65% | -3,58 | -2,93 | [no] |
| `170932dd` | `s` | `(none)` | 625 | -59,86 | -12,25% | -12,25% | +0,61 | +0,11 | [si] |
| `170932dd` | `s` | `rr` | 625 | -73,57 | -14,65% | -14,65% | -2,30 | -2,04 | [no] |
| `170932dd` | `s` | `rr_grounded` | 625 | -73,57 | -14,65% | -14,65% | -2,23 | -1,70 | [no] |
| `d95c0ab0` | `s` | `(none)` | 625 | -59,86 | -12,25% | -12,25% | -2,19 | -2,45 | [no] |
| `d95c0ab0` | `s` | `rr` | 625 | -73,57 | -14,65% | -14,65% | -2,23 | -1,70 | [no] |
| `d95c0ab0` | `s` | `rr_grounded` | 625 | -73,57 | -14,65% | -14,65% | -0,59 | -0,49 | [si] |

## Detalle por par

### `run_20260520_181009_unknown_75120177` - `s`  (`baseline_s` vs `optimized_s`)

- Retriever: `s` · Variante: `(none)`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 488,71 | 428,85 | -59,86 | -12,25% | 0,0000 | [si] |
| context_chars_total | 2443,55 | 2144,26 | -299,29 | -12,25% | 0,0000 | [si] |
| context_tokens_est | 610,47 | 535,69 | -74,78 | -12,25% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 72,49 | 71,40 | -1,09 | 0,6232 | [si] | - |
| faithfulness | 80,83 | 80,89 | +0,06 | 0,8346 | [si] | - |
| answer_relevance | 92,96 | 93,24 | +0,28 | 0,8708 | [si] | - |
| context_support | 88,14 | 89,89 | +1,75 | 0,0643 | [si] | - |
| overall | 76,11 | 75,74 | -0,37 | 0,9699 | [si] | - |

**Veredicto:** soporta la afirmación

### `run_20260520_181009_unknown_75120177` - `s_rr`  (`baseline_s_rr` vs `optimized_s_rr`)

- Retriever: `s` · Variante: `rr`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 502,35 | 428,78 | -73,57 | -14,65% | 0,0000 | [si] |
| context_chars_total | 2511,75 | 2143,88 | -367,87 | -14,65% | 0,0000 | [si] |
| context_tokens_est | 627,52 | 535,61 | -91,91 | -14,65% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 79,35 | 76,54 | -2,81 | 0,0812 | [no] | - |
| faithfulness | 84,63 | 82,94 | -1,69 | 0,1580 | [si] | - |
| answer_relevance | 94,40 | 94,11 | -0,29 | 0,6873 | [si] | - |
| context_support | 94,77 | 93,82 | -0,95 | 0,1683 | [si] | - |
| overall | 82,71 | 80,68 | -2,03 | 0,1972 | [no] | - |

**Veredicto:** **no** soporta la afirmación (contexto reducido pero calidad perdida)

### `run_20260520_181009_unknown_75120177` - `s_rr_grounded`  (`baseline_s_rr_grounded` vs `optimized_s_rr_grounded`)

- Retriever: `s` · Variante: `rr_grounded`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 502,35 | 428,78 | -73,57 | -14,65% | 0,0000 | [si] |
| context_chars_total | 2511,75 | 2143,88 | -367,87 | -14,65% | 0,0000 | [si] |
| context_tokens_est | 627,52 | 535,61 | -91,91 | -14,65% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 78,25 | 76,79 | -1,46 | 0,4951 | [si] | - |
| faithfulness | 87,21 | 86,88 | -0,33 | 0,7264 | [si] | - |
| answer_relevance | 96,80 | 95,65 | -1,15 | 0,2198 | [si] | - |
| context_support | 96,59 | 94,37 | -2,22 | 0,0082 | [no] | [si] |
| overall | 81,66 | 79,83 | -1,83 | 0,1244 | [si] | - |

**Veredicto:** soporta la afirmación

### `run_20260520_204251_unknown_0ae208b6` - `s`  (`baseline_s` vs `optimized_s`)

- Retriever: `s` · Variante: `(none)`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 488,71 | 428,85 | -59,86 | -12,25% | 0,0000 | [si] |
| context_chars_total | 2443,55 | 2144,26 | -299,29 | -12,25% | 0,0000 | [si] |
| context_tokens_est | 610,47 | 535,69 | -74,78 | -12,25% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 73,05 | 70,91 | -2,14 | 0,2827 | [no] | - |
| faithfulness | 79,97 | 80,45 | +0,48 | 0,7905 | [si] | - |
| answer_relevance | 92,36 | 92,08 | -0,28 | 0,6609 | [si] | - |
| context_support | 87,84 | 87,79 | -0,05 | 0,8094 | [si] | - |
| overall | 77,28 | 75,41 | -1,87 | 0,0604 | [si] | - |

**Veredicto:** **no** soporta la afirmación (contexto reducido pero calidad perdida)

### `run_20260520_204251_unknown_0ae208b6` - `s_rr`  (`baseline_s_rr` vs `optimized_s_rr`)

- Retriever: `s` · Variante: `rr`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 502,35 | 428,78 | -73,57 | -14,65% | 0,0000 | [si] |
| context_chars_total | 2511,75 | 2143,88 | -367,87 | -14,65% | 0,0000 | [si] |
| context_tokens_est | 627,52 | 535,61 | -91,91 | -14,65% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 80,02 | 77,14 | -2,88 | 0,0598 | [no] | - |
| faithfulness | 85,28 | 83,14 | -2,14 | 0,1322 | [no] | - |
| answer_relevance | 95,04 | 94,99 | -0,05 | 0,8328 | [si] | - |
| context_support | 94,35 | 93,57 | -0,78 | 0,5217 | [si] | - |
| overall | 83,25 | 81,37 | -1,88 | 0,1076 | [si] | - |

**Veredicto:** **no** soporta la afirmación (contexto reducido pero calidad perdida)

### `run_20260520_204251_unknown_0ae208b6` - `s_rr_grounded`  (`baseline_s_rr_grounded` vs `optimized_s_rr_grounded`)

- Retriever: `s` · Variante: `rr_grounded`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 502,35 | 428,78 | -73,57 | -14,65% | 0,0000 | [si] |
| context_chars_total | 2511,75 | 2143,88 | -367,87 | -14,65% | 0,0000 | [si] |
| context_tokens_est | 627,52 | 535,61 | -91,91 | -14,65% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 78,39 | 77,11 | -1,28 | 0,4139 | [si] | - |
| faithfulness | 87,86 | 86,99 | -0,86 | 0,7103 | [si] | - |
| answer_relevance | 96,85 | 96,50 | -0,35 | 0,9817 | [si] | - |
| context_support | 95,76 | 94,09 | -1,67 | 0,1332 | [si] | - |
| overall | 81,74 | 80,24 | -1,51 | 0,1680 | [si] | - |

**Veredicto:** soporta la afirmación

### `run_20260520_225042_unknown_1e8f339e` - `s`  (`baseline_s` vs `optimized_s`)

- Retriever: `s` · Variante: `(none)`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 488,71 | 428,85 | -59,86 | -12,25% | 0,0000 | [si] |
| context_chars_total | 2443,55 | 2144,26 | -299,29 | -12,25% | 0,0000 | [si] |
| context_tokens_est | 610,47 | 535,69 | -74,78 | -12,25% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 73,01 | 70,38 | -2,63 | 0,1254 | [no] | - |
| faithfulness | 79,87 | 79,70 | -0,17 | 0,8880 | [si] | - |
| answer_relevance | 91,33 | 93,46 | +2,12 | 0,0496 | [no] | [si] |
| context_support | 89,46 | 88,20 | -1,26 | 0,2622 | [si] | - |
| overall | 76,80 | 75,04 | -1,76 | 0,4121 | [si] | - |

**Veredicto:** **no** soporta la afirmación (contexto reducido pero calidad perdida)

### `run_20260520_225042_unknown_1e8f339e` - `s_rr`  (`baseline_s_rr` vs `optimized_s_rr`)

- Retriever: `s` · Variante: `rr`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 502,35 | 428,78 | -73,57 | -14,65% | 0,0000 | [si] |
| context_chars_total | 2511,75 | 2143,88 | -367,87 | -14,65% | 0,0000 | [si] |
| context_tokens_est | 627,52 | 535,61 | -91,91 | -14,65% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 78,91 | 77,15 | -1,76 | 0,1942 | [si] | - |
| faithfulness | 84,98 | 83,49 | -1,50 | 0,3609 | [si] | - |
| answer_relevance | 93,85 | 94,84 | +0,99 | 0,3562 | [si] | - |
| context_support | 94,03 | 94,96 | +0,92 | 0,2039 | [si] | - |
| overall | 82,34 | 81,06 | -1,28 | 0,2215 | [si] | - |

**Veredicto:** soporta la afirmación

### `run_20260520_225042_unknown_1e8f339e` - `s_rr_grounded`  (`baseline_s_rr_grounded` vs `optimized_s_rr_grounded`)

- Retriever: `s` · Variante: `rr_grounded`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 502,35 | 428,78 | -73,57 | -14,65% | 0,0000 | [si] |
| context_chars_total | 2511,75 | 2143,88 | -367,87 | -14,65% | 0,0000 | [si] |
| context_tokens_est | 627,52 | 535,61 | -91,91 | -14,65% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 77,86 | 77,23 | -0,63 | 0,7387 | [si] | - |
| faithfulness | 87,77 | 86,33 | -1,44 | 0,4328 | [si] | - |
| answer_relevance | 97,53 | 95,69 | -1,84 | 0,0210 | [si] | [si] |
| context_support | 96,20 | 95,65 | -0,56 | 0,2950 | [si] | - |
| overall | 81,48 | 80,46 | -1,02 | 0,2952 | [si] | - |

**Veredicto:** soporta la afirmación

### `run_20260521_005823_unknown_4818b378` - `s`  (`baseline_s` vs `optimized_s`)

- Retriever: `s` · Variante: `(none)`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 488,71 | 428,85 | -59,86 | -12,25% | 0,0000 | [si] |
| context_chars_total | 2443,55 | 2144,26 | -299,29 | -12,25% | 0,0000 | [si] |
| context_tokens_est | 610,47 | 535,69 | -74,78 | -12,25% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 72,71 | 70,13 | -2,58 | 0,3206 | [no] | - |
| faithfulness | 78,61 | 79,26 | +0,64 | 0,4675 | [si] | - |
| answer_relevance | 91,73 | 91,67 | -0,06 | 0,6312 | [si] | - |
| context_support | 88,14 | 87,77 | -0,37 | 0,9039 | [si] | - |
| overall | 76,37 | 74,91 | -1,46 | 0,4560 | [si] | - |

**Veredicto:** **no** soporta la afirmación (contexto reducido pero calidad perdida)

### `run_20260521_005823_unknown_4818b378` - `s_rr`  (`baseline_s_rr` vs `optimized_s_rr`)

- Retriever: `s` · Variante: `rr`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 502,35 | 428,78 | -73,57 | -14,65% | 0,0000 | [si] |
| context_chars_total | 2511,75 | 2143,88 | -367,87 | -14,65% | 0,0000 | [si] |
| context_tokens_est | 627,52 | 535,61 | -91,91 | -14,65% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 78,94 | 76,95 | -1,99 | 0,4061 | [si] | - |
| faithfulness | 84,01 | 83,04 | -0,97 | 0,5054 | [si] | - |
| answer_relevance | 94,91 | 94,70 | -0,21 | 0,7296 | [si] | - |
| context_support | 94,71 | 93,28 | -1,43 | 0,2330 | [si] | - |
| overall | 82,43 | 80,68 | -1,75 | 0,2839 | [si] | - |

**Veredicto:** soporta la afirmación

### `run_20260521_005823_unknown_4818b378` - `s_rr_grounded`  (`baseline_s_rr_grounded` vs `optimized_s_rr_grounded`)

- Retriever: `s` · Variante: `rr_grounded`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 502,35 | 428,78 | -73,57 | -14,65% | 0,0000 | [si] |
| context_chars_total | 2511,75 | 2143,88 | -367,87 | -14,65% | 0,0000 | [si] |
| context_tokens_est | 627,52 | 535,61 | -91,91 | -14,65% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 77,76 | 76,87 | -0,89 | 0,4114 | [si] | - |
| faithfulness | 86,17 | 85,88 | -0,29 | 0,6007 | [si] | - |
| answer_relevance | 96,68 | 96,47 | -0,21 | 0,9963 | [si] | - |
| context_support | 96,21 | 93,70 | -2,51 | 0,0244 | [no] | [si] |
| overall | 81,04 | 80,42 | -0,62 | 0,9027 | [si] | - |

**Veredicto:** soporta la afirmación

### `run_20260521_031645_unknown_ecfe2405` - `s`  (`baseline_s` vs `optimized_s`)

- Retriever: `s` · Variante: `(none)`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 488,71 | 428,85 | -59,86 | -12,25% | 0,0000 | [si] |
| context_chars_total | 2443,55 | 2144,26 | -299,29 | -12,25% | 0,0000 | [si] |
| context_tokens_est | 610,47 | 535,69 | -74,78 | -12,25% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 71,92 | 70,05 | -1,87 | 0,4132 | [si] | - |
| faithfulness | 79,47 | 80,21 | +0,74 | 0,6374 | [si] | - |
| answer_relevance | 92,44 | 92,47 | +0,03 | 0,9440 | [si] | - |
| context_support | 88,03 | 88,50 | +0,47 | 0,3993 | [si] | - |
| overall | 75,95 | 74,51 | -1,44 | 0,3240 | [si] | - |

**Veredicto:** soporta la afirmación

### `run_20260521_031645_unknown_ecfe2405` - `s_rr`  (`baseline_s_rr` vs `optimized_s_rr`)

- Retriever: `s` · Variante: `rr`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 502,35 | 428,78 | -73,57 | -14,65% | 0,0000 | [si] |
| context_chars_total | 2511,75 | 2143,88 | -367,87 | -14,65% | 0,0000 | [si] |
| context_tokens_est | 627,52 | 535,61 | -91,91 | -14,65% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 78,29 | 76,36 | -1,93 | 0,4020 | [si] | - |
| faithfulness | 83,82 | 82,65 | -1,17 | 0,5725 | [si] | - |
| answer_relevance | 95,14 | 94,15 | -0,99 | 0,2604 | [si] | - |
| context_support | 95,03 | 92,90 | -2,12 | 0,1127 | [no] | - |
| overall | 82,11 | 80,19 | -1,92 | 0,0982 | [si] | - |

**Veredicto:** soporta la afirmación

### `run_20260521_031645_unknown_ecfe2405` - `s_rr_grounded`  (`baseline_s_rr_grounded` vs `optimized_s_rr_grounded`)

- Retriever: `s` · Variante: `rr_grounded`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 502,35 | 428,78 | -73,57 | -14,65% | 0,0000 | [si] |
| context_chars_total | 2511,75 | 2143,88 | -367,87 | -14,65% | 0,0000 | [si] |
| context_tokens_est | 627,52 | 535,61 | -91,91 | -14,65% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 76,47 | 77,39 | +0,92 | 0,6194 | [si] | - |
| faithfulness | 86,15 | 85,66 | -0,49 | 0,6523 | [si] | - |
| answer_relevance | 96,17 | 96,38 | +0,22 | 0,5850 | [si] | - |
| context_support | 95,25 | 94,70 | -0,56 | 0,7672 | [si] | - |
| overall | 80,13 | 80,62 | +0,49 | 0,8219 | [si] | - |

**Veredicto:** soporta la afirmación

### `run_20260521_053016_unknown_74a6f570` - `s`  (`baseline_s` vs `optimized_s`)

- Retriever: `s` · Variante: `(none)`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 488,71 | 428,85 | -59,86 | -12,25% | 0,0000 | [si] |
| context_chars_total | 2443,55 | 2144,26 | -299,29 | -12,25% | 0,0000 | [si] |
| context_tokens_est | 610,47 | 535,69 | -74,78 | -12,25% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 72,06 | 70,27 | -1,79 | 0,6349 | [si] | - |
| faithfulness | 79,38 | 81,02 | +1,64 | 0,2808 | [si] | - |
| answer_relevance | 92,07 | 92,62 | +0,55 | 0,5660 | [si] | - |
| context_support | 87,68 | 89,09 | +1,41 | 0,5422 | [si] | - |
| overall | 76,50 | 74,61 | -1,89 | 0,2077 | [si] | - |

**Veredicto:** soporta la afirmación

### `run_20260521_053016_unknown_74a6f570` - `s_rr`  (`baseline_s_rr` vs `optimized_s_rr`)

- Retriever: `s` · Variante: `rr`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 502,35 | 428,78 | -73,57 | -14,65% | 0,0000 | [si] |
| context_chars_total | 2511,75 | 2143,88 | -367,87 | -14,65% | 0,0000 | [si] |
| context_tokens_est | 627,52 | 535,61 | -91,91 | -14,65% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 79,61 | 76,89 | -2,72 | 0,1287 | [no] | - |
| faithfulness | 84,09 | 82,17 | -1,91 | 0,2748 | [si] | - |
| answer_relevance | 94,65 | 94,56 | -0,10 | 0,9466 | [si] | - |
| context_support | 93,39 | 93,03 | -0,36 | 0,6229 | [si] | - |
| overall | 82,90 | 80,18 | -2,72 | 0,0305 | [no] | [si] |

**Veredicto:** **no** soporta la afirmación (contexto reducido pero calidad perdida)

### `run_20260521_053016_unknown_74a6f570` - `s_rr_grounded`  (`baseline_s_rr_grounded` vs `optimized_s_rr_grounded`)

- Retriever: `s` · Variante: `rr_grounded`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 502,35 | 428,78 | -73,57 | -14,65% | 0,0000 | [si] |
| context_chars_total | 2511,75 | 2143,88 | -367,87 | -14,65% | 0,0000 | [si] |
| context_tokens_est | 627,52 | 535,61 | -91,91 | -14,65% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 77,70 | 77,43 | -0,27 | 0,7556 | [si] | - |
| faithfulness | 86,26 | 85,18 | -1,09 | 0,6348 | [si] | - |
| answer_relevance | 97,48 | 95,32 | -2,16 | 0,0237 | [no] | [si] |
| context_support | 95,50 | 94,47 | -1,03 | 0,3877 | [si] | - |
| overall | 81,11 | 80,78 | -0,33 | 0,7638 | [si] | - |

**Veredicto:** soporta la afirmación

### `run_20260521_074553_unknown_fedf0681` - `s`  (`baseline_s` vs `optimized_s`)

- Retriever: `s` · Variante: `(none)`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 488,71 | 428,85 | -59,86 | -12,25% | 0,0000 | [si] |
| context_chars_total | 2443,55 | 2144,26 | -299,29 | -12,25% | 0,0000 | [si] |
| context_tokens_est | 610,47 | 535,69 | -74,78 | -12,25% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 72,55 | 71,31 | -1,24 | 0,6052 | [si] | - |
| faithfulness | 83,06 | 77,16 | -5,89 | 0,0004 | [no] | [si] |
| answer_relevance | 95,32 | 93,54 | -1,78 | 0,0092 | [si] | [si] |
| context_support | 89,79 | 86,77 | -3,01 | 0,0123 | [no] | [si] |
| overall | 76,63 | 75,17 | -1,46 | 0,0621 | [si] | - |

**Veredicto:** soporta la afirmación

### `run_20260521_074553_unknown_fedf0681` - `s_rr`  (`baseline_s_rr` vs `optimized_s_rr`)

- Retriever: `s` · Variante: `rr`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 502,35 | 428,78 | -73,57 | -14,65% | 0,0000 | [si] |
| context_chars_total | 2511,75 | 2143,88 | -367,87 | -14,65% | 0,0000 | [si] |
| context_tokens_est | 627,52 | 535,61 | -91,91 | -14,65% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 79,07 | 76,35 | -2,71 | 0,1525 | [no] | - |
| faithfulness | 83,26 | 83,30 | +0,04 | 0,7063 | [si] | - |
| answer_relevance | 95,06 | 94,88 | -0,18 | 0,5381 | [si] | - |
| context_support | 94,66 | 91,99 | -2,67 | 0,0007 | [no] | [si] |
| overall | 82,44 | 80,45 | -2,00 | 0,2489 | [si] | - |

**Veredicto:** **no** soporta la afirmación (contexto reducido pero calidad perdida)

### `run_20260521_074553_unknown_fedf0681` - `s_rr_grounded`  (`baseline_s_rr_grounded` vs `optimized_s_rr_grounded`)

- Retriever: `s` · Variante: `rr_grounded`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 502,35 | 428,78 | -73,57 | -14,65% | 0,0000 | [si] |
| context_chars_total | 2511,75 | 2143,88 | -367,87 | -14,65% | 0,0000 | [si] |
| context_tokens_est | 627,52 | 535,61 | -91,91 | -14,65% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 77,80 | 74,74 | -3,06 | 0,0171 | [no] | [si] |
| faithfulness | 89,14 | 88,31 | -0,83 | 0,4690 | [si] | - |
| answer_relevance | 97,66 | 97,95 | +0,28 | 0,7019 | [si] | - |
| context_support | 94,02 | 95,22 | +1,21 | 0,1255 | [si] | - |
| overall | 81,65 | 79,16 | -2,49 | 0,0414 | [no] | [si] |

**Veredicto:** **no** soporta la afirmación (contexto reducido pero calidad perdida)

### `run_20260521_094824_unknown_39fff400` - `s`  (`baseline_s` vs `optimized_s`)

- Retriever: `s` · Variante: `(none)`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 488,71 | 428,85 | -59,86 | -12,25% | 0,0000 | [si] |
| context_chars_total | 2443,55 | 2144,26 | -299,29 | -12,25% | 0,0000 | [si] |
| context_tokens_est | 610,47 | 535,69 | -74,78 | -12,25% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 73,11 | 71,39 | -1,72 | 0,2451 | [si] | - |
| faithfulness | 79,77 | 78,80 | -0,96 | 0,5975 | [si] | - |
| answer_relevance | 94,38 | 92,30 | -2,08 | 0,0198 | [no] | [si] |
| context_support | 88,85 | 86,88 | -1,97 | 0,0282 | [si] | [si] |
| overall | 76,74 | 75,19 | -1,55 | 0,2017 | [si] | - |

**Veredicto:** soporta la afirmación

### `run_20260521_094824_unknown_39fff400` - `s_rr`  (`baseline_s_rr` vs `optimized_s_rr`)

- Retriever: `s` · Variante: `rr`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 502,35 | 428,78 | -73,57 | -14,65% | 0,0000 | [si] |
| context_chars_total | 2511,75 | 2143,88 | -367,87 | -14,65% | 0,0000 | [si] |
| context_tokens_est | 627,52 | 535,61 | -91,91 | -14,65% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 78,41 | 77,05 | -1,37 | 0,3075 | [si] | - |
| faithfulness | 85,49 | 83,52 | -1,97 | 0,1491 | [si] | - |
| answer_relevance | 94,57 | 93,89 | -0,67 | 0,5319 | [si] | - |
| context_support | 95,46 | 92,99 | -2,46 | 0,0040 | [no] | [si] |
| overall | 81,87 | 80,84 | -1,03 | 0,3395 | [si] | - |

**Veredicto:** soporta la afirmación

### `run_20260521_094824_unknown_39fff400` - `s_rr_grounded`  (`baseline_s_rr_grounded` vs `optimized_s_rr_grounded`)

- Retriever: `s` · Variante: `rr_grounded`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 502,35 | 428,78 | -73,57 | -14,65% | 0,0000 | [si] |
| context_chars_total | 2511,75 | 2143,88 | -367,87 | -14,65% | 0,0000 | [si] |
| context_tokens_est | 627,52 | 535,61 | -91,91 | -14,65% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 78,58 | 75,00 | -3,58 | 0,0276 | [no] | [si] |
| faithfulness | 90,64 | 88,68 | -1,96 | 0,1837 | [si] | - |
| answer_relevance | 97,42 | 97,96 | +0,55 | 0,3795 | [si] | - |
| context_support | 93,59 | 94,90 | +1,31 | 0,3400 | [si] | - |
| overall | 82,07 | 79,13 | -2,93 | 0,0691 | [no] | - |

**Veredicto:** **no** soporta la afirmación (contexto reducido pero calidad perdida)

### `run_20260521_115237_unknown_170932dd` - `s`  (`baseline_s` vs `optimized_s`)

- Retriever: `s` · Variante: `(none)`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 488,71 | 428,85 | -59,86 | -12,25% | 0,0000 | [si] |
| context_chars_total | 2443,55 | 2144,26 | -299,29 | -12,25% | 0,0000 | [si] |
| context_tokens_est | 610,47 | 535,69 | -74,78 | -12,25% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 71,87 | 72,48 | +0,61 | 0,5125 | [si] | - |
| faithfulness | 81,14 | 80,05 | -1,09 | 0,7121 | [si] | - |
| answer_relevance | 94,61 | 92,75 | -1,86 | 0,0325 | [si] | [si] |
| context_support | 90,50 | 87,75 | -2,74 | 0,0131 | [no] | [si] |
| overall | 76,36 | 76,47 | +0,11 | 0,9507 | [si] | - |

**Veredicto:** soporta la afirmación

### `run_20260521_115237_unknown_170932dd` - `s_rr`  (`baseline_s_rr` vs `optimized_s_rr`)

- Retriever: `s` · Variante: `rr`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 502,35 | 428,78 | -73,57 | -14,65% | 0,0000 | [si] |
| context_chars_total | 2511,75 | 2143,88 | -367,87 | -14,65% | 0,0000 | [si] |
| context_tokens_est | 627,52 | 535,61 | -91,91 | -14,65% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 78,89 | 76,59 | -2,30 | 0,2203 | [no] | - |
| faithfulness | 85,22 | 84,13 | -1,09 | 0,4587 | [si] | - |
| answer_relevance | 94,58 | 93,80 | -0,78 | 0,2155 | [si] | - |
| context_support | 95,22 | 92,86 | -2,36 | 0,0084 | [no] | [si] |
| overall | 82,54 | 80,50 | -2,04 | 0,1428 | [no] | - |

**Veredicto:** **no** soporta la afirmación (contexto reducido pero calidad perdida)

### `run_20260521_115237_unknown_170932dd` - `s_rr_grounded`  (`baseline_s_rr_grounded` vs `optimized_s_rr_grounded`)

- Retriever: `s` · Variante: `rr_grounded`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 502,35 | 428,78 | -73,57 | -14,65% | 0,0000 | [si] |
| context_chars_total | 2511,75 | 2143,88 | -367,87 | -14,65% | 0,0000 | [si] |
| context_tokens_est | 627,52 | 535,61 | -91,91 | -14,65% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 77,80 | 75,56 | -2,23 | 0,3066 | [no] | - |
| faithfulness | 90,31 | 87,18 | -3,14 | 0,0633 | [no] | - |
| answer_relevance | 96,10 | 97,29 | +1,19 | 0,2202 | [si] | - |
| context_support | 95,26 | 94,92 | -0,34 | 0,7620 | [si] | - |
| overall | 81,64 | 79,94 | -1,70 | 0,3840 | [si] | - |

**Veredicto:** **no** soporta la afirmación (contexto reducido pero calidad perdida)

### `run_20260521_141011_unknown_d95c0ab0` - `s`  (`baseline_s` vs `optimized_s`)

- Retriever: `s` · Variante: `(none)`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 488,71 | 428,85 | -59,86 | -12,25% | 0,0000 | [si] |
| context_chars_total | 2443,55 | 2144,26 | -299,29 | -12,25% | 0,0000 | [si] |
| context_tokens_est | 610,47 | 535,69 | -74,78 | -12,25% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 73,71 | 71,52 | -2,19 | 0,3683 | [no] | - |
| faithfulness | 82,05 | 79,70 | -2,35 | 0,2065 | [no] | - |
| answer_relevance | 94,42 | 93,01 | -1,40 | 0,2266 | [si] | - |
| context_support | 89,48 | 89,22 | -0,26 | 0,4879 | [si] | - |
| overall | 77,96 | 75,51 | -2,45 | 0,0567 | [no] | - |

**Veredicto:** **no** soporta la afirmación (contexto reducido pero calidad perdida)

### `run_20260521_141011_unknown_d95c0ab0` - `s_rr`  (`baseline_s_rr` vs `optimized_s_rr`)

- Retriever: `s` · Variante: `rr`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 502,35 | 428,78 | -73,57 | -14,65% | 0,0000 | [si] |
| context_chars_total | 2511,75 | 2143,88 | -367,87 | -14,65% | 0,0000 | [si] |
| context_tokens_est | 627,52 | 535,61 | -91,91 | -14,65% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 78,58 | 76,35 | -2,23 | 0,1344 | [no] | - |
| faithfulness | 84,28 | 84,93 | +0,65 | 0,6805 | [si] | - |
| answer_relevance | 95,02 | 94,58 | -0,44 | 0,4423 | [si] | - |
| context_support | 94,56 | 92,03 | -2,53 | 0,0049 | [no] | [si] |
| overall | 82,20 | 80,51 | -1,70 | 0,1670 | [si] | - |

**Veredicto:** **no** soporta la afirmación (contexto reducido pero calidad perdida)

### `run_20260521_141011_unknown_d95c0ab0` - `s_rr_grounded`  (`baseline_s_rr_grounded` vs `optimized_s_rr_grounded`)

- Retriever: `s` · Variante: `rr_grounded`
- Chunker: `fixed` (fijo) vs `semantic` (semántico)
- Muestras emparejadas completadas: **625**

**Tamaño de contexto** (evidencia principal de la afirmación)

| Métrica | fijo | semántico | Δ | Δ% | Wilcoxon p | Sig. dif.? |
|---|---:|---:|---:|---:|---:|:---:|
| avg_chunk_size_chars | 502,35 | 428,78 | -73,57 | -14,65% | 0,0000 | [si] |
| context_chars_total | 2511,75 | 2143,88 | -367,87 | -14,65% | 0,0000 | [si] |
| context_tokens_est | 627,52 | 535,61 | -91,91 | -14,65% | 0,0000 | [si] |
| num_chunks_final | 5,00 | 5,00 | +0,00 | +0,00% | - | - |

**Calidad** (debe preservarse para que la afirmación sea válida)

| Métrica | fijo | semántico | Δ | Wilcoxon p | Equiv.? | Sig.↓? |
|---|---:|---:|---:|---:|:---:|:---:|
| correctness | 77,30 | 76,71 | -0,59 | 0,6869 | [si] | - |
| faithfulness | 89,16 | 87,52 | -1,64 | 0,3054 | [si] | - |
| answer_relevance | 97,21 | 97,40 | +0,19 | 0,9465 | [si] | - |
| context_support | 95,58 | 94,06 | -1,52 | 0,1630 | [si] | - |
| overall | 81,15 | 80,66 | -0,49 | 0,5367 | [si] | - |

**Veredicto:** soporta la afirmación

