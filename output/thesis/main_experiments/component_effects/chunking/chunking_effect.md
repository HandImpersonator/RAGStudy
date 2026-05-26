# Efecto aislado: chunking

Pares analizados: **30**.  Threshold mínimo de muestras emparejadas: **600**.

Cada fila es un (run, pareja) que cumple el threshold.  Los deltas son **right - left** según la convención definida para este efecto.

| Run | Pareja | n | ΔCorrect. | ΔFaith. | ΔAnsRel. | ΔCtxSup. | ΔGlobal | Soporta |
|---|---|---:|---:|---:|---:|---:|---:|:---:|
| `75120177` | `baseline_s -> optimized_s` | 625 | -1,09 | +0,06 | +0,28 | +1,75 | -0,37 | [si] |
| `75120177` | `baseline_s_rr -> optimized_s_rr` | 625 | -2,81 | -1,69 | -0,29 | -0,95 | -2,03 | [no] |
| `75120177` | `baseline_s_rr_grounded -> optimized_s_rr_grounded` | 625 | -1,46 | -0,33 | -1,15 | -2,22 | -1,83 | [si] |
| `0ae208b6` | `baseline_s -> optimized_s` | 625 | -2,14 | +0,48 | -0,28 | -0,05 | -1,87 | [no] |
| `0ae208b6` | `baseline_s_rr -> optimized_s_rr` | 625 | -2,88 | -2,14 | -0,05 | -0,78 | -1,88 | [no] |
| `0ae208b6` | `baseline_s_rr_grounded -> optimized_s_rr_grounded` | 625 | -1,28 | -0,86 | -0,35 | -1,67 | -1,51 | [si] |
| `1e8f339e` | `baseline_s -> optimized_s` | 625 | -2,63 | -0,17 | +2,12 | -1,26 | -1,76 | [no] |
| `1e8f339e` | `baseline_s_rr -> optimized_s_rr` | 625 | -1,76 | -1,50 | +0,99 | +0,92 | -1,28 | [si] |
| `1e8f339e` | `baseline_s_rr_grounded -> optimized_s_rr_grounded` | 625 | -0,63 | -1,44 | -1,84 | -0,56 | -1,02 | [si] |
| `4818b378` | `baseline_s -> optimized_s` | 625 | -2,58 | +0,64 | -0,06 | -0,37 | -1,46 | [no] |
| `4818b378` | `baseline_s_rr -> optimized_s_rr` | 625 | -1,99 | -0,97 | -0,21 | -1,43 | -1,75 | [si] |
| `4818b378` | `baseline_s_rr_grounded -> optimized_s_rr_grounded` | 625 | -0,89 | -0,29 | -0,21 | -2,51 | -0,62 | [si] |
| `ecfe2405` | `baseline_s -> optimized_s` | 625 | -1,87 | +0,74 | +0,03 | +0,47 | -1,44 | [si] |
| `ecfe2405` | `baseline_s_rr -> optimized_s_rr` | 625 | -1,93 | -1,17 | -0,99 | -2,12 | -1,92 | [si] |
| `ecfe2405` | `baseline_s_rr_grounded -> optimized_s_rr_grounded` | 625 | +0,92 | -0,49 | +0,22 | -0,56 | +0,49 | [si] |
| `74a6f570` | `baseline_s -> optimized_s` | 625 | -1,79 | +1,64 | +0,55 | +1,41 | -1,89 | [si] |
| `74a6f570` | `baseline_s_rr -> optimized_s_rr` | 625 | -2,72 | -1,91 | -0,10 | -0,36 | -2,72 | [no] |
| `74a6f570` | `baseline_s_rr_grounded -> optimized_s_rr_grounded` | 625 | -0,27 | -1,09 | -2,16 | -1,03 | -0,33 | [si] |
| `fedf0681` | `baseline_s -> optimized_s` | 625 | -1,24 | -5,89 | -1,78 | -3,01 | -1,46 | [si] |
| `fedf0681` | `baseline_s_rr -> optimized_s_rr` | 625 | -2,71 | +0,04 | -0,18 | -2,67 | -2,00 | [no] |
| `fedf0681` | `baseline_s_rr_grounded -> optimized_s_rr_grounded` | 625 | -3,06 | -0,83 | +0,28 | +1,21 | -2,49 | [no] |
| `39fff400` | `baseline_s -> optimized_s` | 625 | -1,72 | -0,96 | -2,08 | -1,97 | -1,55 | [si] |
| `39fff400` | `baseline_s_rr -> optimized_s_rr` | 625 | -1,37 | -1,97 | -0,67 | -2,46 | -1,03 | [si] |
| `39fff400` | `baseline_s_rr_grounded -> optimized_s_rr_grounded` | 625 | -3,58 | -1,96 | +0,55 | +1,31 | -2,93 | [no] |
| `170932dd` | `baseline_s -> optimized_s` | 625 | +0,61 | -1,09 | -1,86 | -2,74 | +0,11 | [si] |
| `170932dd` | `baseline_s_rr -> optimized_s_rr` | 625 | -2,30 | -1,09 | -0,78 | -2,36 | -2,04 | [no] |
| `170932dd` | `baseline_s_rr_grounded -> optimized_s_rr_grounded` | 625 | -2,23 | -3,14 | +1,19 | -0,34 | -1,70 | [no] |
| `d95c0ab0` | `baseline_s -> optimized_s` | 625 | -2,19 | -2,35 | -1,40 | -0,26 | -2,45 | [no] |
| `d95c0ab0` | `baseline_s_rr -> optimized_s_rr` | 625 | -2,23 | +0,65 | -0,44 | -2,53 | -1,70 | [no] |
| `d95c0ab0` | `baseline_s_rr_grounded -> optimized_s_rr_grounded` | 625 | -0,59 | -1,64 | +0,19 | -1,52 | -0,49 | [si] |
