# Efecto aislado: re-ranking

Pares analizados: **20**.  Threshold mínimo de muestras emparejadas: **600**.

Cada fila es un (run, pareja) que cumple el threshold.  Los deltas son **right - left** según la convención definida para este efecto.

| Run | Pareja | n | ΔCorrect. | ΔFaith. | ΔAnsRel. | ΔCtxSup. | ΔGlobal | Soporta |
|---|---|---:|---:|---:|---:|---:|---:|:---:|
| `75120177` | `baseline_s -> baseline_s_rr` | 625 | +6,86 | +3,80 | +1,44 | +6,63 | +6,60 | [si] |
| `75120177` | `optimized_s -> optimized_s_rr` | 625 | +5,14 | +2,05 | +0,87 | +3,93 | +4,95 | [si] |
| `0ae208b6` | `baseline_s -> baseline_s_rr` | 625 | +6,97 | +5,31 | +2,68 | +6,51 | +5,97 | [si] |
| `0ae208b6` | `optimized_s -> optimized_s_rr` | 625 | +6,23 | +2,69 | +2,91 | +5,78 | +5,96 | [si] |
| `1e8f339e` | `baseline_s -> baseline_s_rr` | 625 | +5,90 | +5,12 | +2,51 | +4,57 | +5,55 | [si] |
| `1e8f339e` | `optimized_s -> optimized_s_rr` | 625 | +6,76 | +3,79 | +1,39 | +6,76 | +6,02 | [si] |
| `4818b378` | `baseline_s -> baseline_s_rr` | 625 | +6,23 | +5,40 | +3,18 | +6,57 | +6,06 | [si] |
| `4818b378` | `optimized_s -> optimized_s_rr` | 625 | +6,82 | +3,79 | +3,03 | +5,51 | +5,77 | [si] |
| `ecfe2405` | `baseline_s -> baseline_s_rr` | 625 | +6,37 | +4,36 | +2,69 | +7,00 | +6,16 | [si] |
| `ecfe2405` | `optimized_s -> optimized_s_rr` | 625 | +6,31 | +2,45 | +1,68 | +4,40 | +5,68 | [si] |
| `74a6f570` | `baseline_s -> baseline_s_rr` | 625 | +7,54 | +4,70 | +2,58 | +5,71 | +6,40 | [si] |
| `74a6f570` | `optimized_s -> optimized_s_rr` | 625 | +6,62 | +1,16 | +1,93 | +3,93 | +5,57 | [si] |
| `fedf0681` | `baseline_s -> baseline_s_rr` | 625 | +6,52 | +0,20 | -0,26 | +4,88 | +5,81 | [si] |
| `fedf0681` | `optimized_s -> optimized_s_rr` | 625 | +5,04 | +6,14 | +1,34 | +5,21 | +5,27 | [si] |
| `39fff400` | `baseline_s -> baseline_s_rr` | 625 | +5,31 | +5,72 | +0,18 | +6,61 | +5,13 | [si] |
| `39fff400` | `optimized_s -> optimized_s_rr` | 625 | +5,66 | +4,72 | +1,59 | +6,11 | +5,65 | [si] |
| `170932dd` | `baseline_s -> baseline_s_rr` | 625 | +7,03 | +4,08 | -0,03 | +4,72 | +6,18 | [si] |
| `170932dd` | `optimized_s -> optimized_s_rr` | 625 | +4,12 | +4,08 | +1,05 | +5,10 | +4,03 | [si] |
| `d95c0ab0` | `baseline_s -> baseline_s_rr` | 625 | +4,87 | +2,23 | +0,61 | +5,08 | +4,24 | [si] |
| `d95c0ab0` | `optimized_s -> optimized_s_rr` | 625 | +4,83 | +5,23 | +1,57 | +2,81 | +5,00 | [si] |
