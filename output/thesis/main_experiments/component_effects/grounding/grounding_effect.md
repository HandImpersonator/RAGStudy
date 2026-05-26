# Efecto aislado: prompt grounded

Pares analizados: **20**.  Threshold mínimo de muestras emparejadas: **600**.

Cada fila es un (run, pareja) que cumple el threshold.  Los deltas son **right - left** según la convención definida para este efecto.

| Run | Pareja | n | ΔCorrect. | ΔFaith. | ΔAnsRel. | ΔCtxSup. | ΔGlobal | Soporta |
|---|---|---:|---:|---:|---:|---:|---:|:---:|
| `75120177` | `baseline_s_rr -> baseline_s_rr_grounded` | 625 | -1,11 | +2,58 | +2,40 | +1,82 | -1,05 | [no] |
| `75120177` | `optimized_s_rr -> optimized_s_rr_grounded` | 625 | +0,25 | +3,94 | +1,54 | +0,54 | -0,86 | [no] |
| `0ae208b6` | `baseline_s_rr -> baseline_s_rr_grounded` | 625 | -1,63 | +2,58 | +1,80 | +1,41 | -1,51 | [no] |
| `0ae208b6` | `optimized_s_rr -> optimized_s_rr_grounded` | 625 | -0,03 | +3,86 | +1,51 | +0,52 | -1,13 | [no] |
| `1e8f339e` | `baseline_s_rr -> baseline_s_rr_grounded` | 625 | -1,05 | +2,79 | +3,68 | +2,17 | -0,86 | [no] |
| `1e8f339e` | `optimized_s_rr -> optimized_s_rr_grounded` | 625 | +0,09 | +2,84 | +0,85 | +0,69 | -0,60 | [no] |
| `4818b378` | `baseline_s_rr -> baseline_s_rr_grounded` | 625 | -1,18 | +2,16 | +1,77 | +1,50 | -1,39 | [no] |
| `4818b378` | `optimized_s_rr -> optimized_s_rr_grounded` | 625 | -0,08 | +2,84 | +1,77 | +0,42 | -0,26 | [no] |
| `ecfe2405` | `baseline_s_rr -> baseline_s_rr_grounded` | 625 | -1,82 | +2,32 | +1,03 | +0,23 | -1,98 | [no] |
| `ecfe2405` | `optimized_s_rr -> optimized_s_rr_grounded` | 625 | +1,02 | +3,00 | +2,24 | +1,80 | +0,43 | [no] |
| `74a6f570` | `baseline_s_rr -> baseline_s_rr_grounded` | 625 | -1,91 | +2,18 | +2,83 | +2,11 | -1,79 | [no] |
| `74a6f570` | `optimized_s_rr -> optimized_s_rr_grounded` | 625 | +0,54 | +3,00 | +0,77 | +1,45 | +0,60 | [no] |
| `fedf0681` | `baseline_s_rr -> baseline_s_rr_grounded` | 625 | -1,27 | +5,88 | +2,60 | -0,65 | -0,80 | [no] |
| `fedf0681` | `optimized_s_rr -> optimized_s_rr_grounded` | 625 | -1,61 | +5,01 | +3,07 | +3,24 | -1,29 | [no] |
| `39fff400` | `baseline_s_rr -> baseline_s_rr_grounded` | 625 | +0,16 | +5,15 | +2,85 | -1,86 | +0,20 | [si] |
| `39fff400` | `optimized_s_rr -> optimized_s_rr_grounded` | 625 | -2,05 | +5,16 | +4,07 | +1,91 | -1,71 | [no] |
| `170932dd` | `baseline_s_rr -> baseline_s_rr_grounded` | 625 | -1,10 | +5,09 | +1,52 | +0,04 | -0,90 | [no] |
| `170932dd` | `optimized_s_rr -> optimized_s_rr_grounded` | 625 | -1,03 | +3,05 | +3,49 | +2,06 | -0,56 | [no] |
| `d95c0ab0` | `baseline_s_rr -> baseline_s_rr_grounded` | 625 | -1,27 | +4,88 | +2,18 | +1,02 | -1,06 | [no] |
| `d95c0ab0` | `optimized_s_rr -> optimized_s_rr_grounded` | 625 | +0,37 | +2,58 | +2,82 | +2,03 | +0,15 | [no] |
