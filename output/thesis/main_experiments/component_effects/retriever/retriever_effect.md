# Efecto aislado: retriever (BM25 vs FAISS)

Pares analizados: **48**.  Threshold mínimo de muestras emparejadas: **45**.

Cada fila es un (run, pareja) que cumple el threshold.  Los deltas son **right - left** según la convención definida para este efecto.

| Run | Pareja | n | ΔCorrect. | ΔFaith. | ΔAnsRel. | ΔCtxSup. | ΔGlobal | Soporta |
|---|---|---:|---:|---:|---:|---:|---:|:---:|
| `e7e4e2d8` | `baseline_k -> baseline_s` | 50 | +3,40 | +1,40 | -0,20 | +3,60 | +4,90 | [si] |
| `e7e4e2d8` | `baseline_k_rr -> baseline_s_rr` | 50 | +3,90 | -1,20 | +5,00 | +2,80 | +1,86 | [si] |
| `e7e4e2d8` | `baseline_k_grounded -> baseline_s_grounded` | 50 | +0,00 | +1,00 | +12,80 | +9,60 | +1,60 | [si] |
| `e7e4e2d8` | `baseline_k_rr_grounded -> baseline_s_rr_grounded` | 50 | +7,60 | -5,60 | +1,60 | +3,60 | +2,10 | [si] |
| `e7e4e2d8` | `optimized_k -> optimized_s` | 50 | +20,00 | +8,40 | +18,60 | +26,00 | +16,12 | [si] |
| `e7e4e2d8` | `optimized_k_rr -> optimized_s_rr` | 50 | +12,00 | +6,00 | +4,00 | +20,00 | +12,00 | [si] |
| `e7e4e2d8` | `optimized_k_grounded -> optimized_s_grounded` | 50 | +14,40 | -3,20 | +1,60 | +14,40 | +10,30 | [si] |
| `e7e4e2d8` | `optimized_k_rr_grounded -> optimized_s_rr_grounded` | 50 | +4,00 | -10,00 | -8,80 | +12,00 | +1,92 | [si] |
| `4fa43fdd` | `baseline_k -> baseline_s` | 50 | +0,40 | -2,00 | +8,80 | +5,60 | +0,82 | [si] |
| `4fa43fdd` | `baseline_k_rr -> baseline_s_rr` | 50 | +1,70 | +3,40 | -2,00 | +2,00 | +1,40 | [si] |
| `4fa43fdd` | `baseline_k_grounded -> baseline_s_grounded` | 50 | -6,00 | +10,20 | +2,60 | +9,60 | -6,20 | [no] |
| `4fa43fdd` | `baseline_k_rr_grounded -> baseline_s_rr_grounded` | 50 | +8,80 | +8,40 | +7,60 | +13,60 | +6,80 | [si] |
| `4fa43fdd` | `optimized_k -> optimized_s` | 50 | +27,60 | +20,00 | +19,70 | +32,00 | +26,68 | [si] |
| `4fa43fdd` | `optimized_k_rr -> optimized_s_rr` | 50 | +16,80 | +11,60 | +8,80 | +20,00 | +18,20 | [si] |
| `4fa43fdd` | `optimized_k_grounded -> optimized_s_grounded` | 50 | +22,00 | -4,00 | -1,60 | +38,00 | +18,80 | [si] |
| `4fa43fdd` | `optimized_k_rr_grounded -> optimized_s_rr_grounded` | 50 | +6,00 | +0,00 | -7,20 | +12,00 | +7,28 | [si] |
| `ac2bbe71` | `baseline_k -> baseline_s` | 50 | +5,00 | +3,00 | +4,40 | +9,80 | +3,70 | [si] |
| `ac2bbe71` | `baseline_k_rr -> baseline_s_rr` | 50 | +16,00 | +20,60 | +7,60 | +4,80 | +13,34 | [si] |
| `ac2bbe71` | `baseline_k_grounded -> baseline_s_grounded` | 50 | +6,40 | -14,20 | -1,80 | -1,80 | -5,82 | [no] |
| `ac2bbe71` | `baseline_k_rr_grounded -> baseline_s_rr_grounded` | 50 | +16,20 | +1,20 | +0,00 | +11,00 | +12,32 | [si] |
| `ac2bbe71` | `optimized_k -> optimized_s` | 50 | +14,00 | -1,30 | +2,80 | +24,00 | +13,10 | [si] |
| `ac2bbe71` | `optimized_k_rr -> optimized_s_rr` | 50 | +18,50 | +14,04 | +6,86 | +13,90 | +18,78 | [si] |
| `ac2bbe71` | `optimized_k_grounded -> optimized_s_grounded` | 50 | +6,00 | -9,20 | -1,70 | +24,00 | +2,74 | [si] |
| `ac2bbe71` | `optimized_k_rr_grounded -> optimized_s_rr_grounded` | 50 | +15,80 | -6,60 | -3,60 | +11,20 | +11,54 | [si] |
| `1bdbb314` | `baseline_k -> baseline_s` | 50 | +9,00 | +9,80 | +5,20 | +1,20 | +5,74 | [si] |
| `1bdbb314` | `baseline_k_rr -> baseline_s_rr` | 50 | +12,20 | +13,80 | +2,40 | +3,80 | +10,64 | [si] |
| `1bdbb314` | `baseline_k_grounded -> baseline_s_grounded` | 50 | +7,40 | +2,50 | +0,80 | +3,60 | +7,56 | [si] |
| `1bdbb314` | `baseline_k_rr_grounded -> baseline_s_rr_grounded` | 50 | +15,80 | -0,90 | +0,80 | +9,60 | +12,88 | [si] |
| `1bdbb314` | `optimized_k -> optimized_s` | 50 | +20,20 | +2,00 | +14,40 | +28,40 | +17,72 | [si] |
| `1bdbb314` | `optimized_k_rr -> optimized_s_rr` | 50 | +16,80 | +21,50 | +5,70 | +16,20 | +17,02 | [si] |
| `1bdbb314` | `optimized_k_grounded -> optimized_s_grounded` | 50 | +22,00 | -7,60 | -2,00 | +30,00 | +18,12 | [si] |
| `1bdbb314` | `optimized_k_rr_grounded -> optimized_s_rr_grounded` | 50 | +16,00 | -8,00 | -1,60 | +22,00 | +13,30 | [si] |
| `c2696cd2` | `baseline_k -> baseline_s` | 50 | +2,20 | +2,00 | +4,80 | -4,60 | +0,60 | [si] |
| `c2696cd2` | `baseline_k_rr -> baseline_s_rr` | 50 | +5,20 | -0,70 | +7,20 | +2,60 | +5,34 | [si] |
| `c2696cd2` | `baseline_k_grounded -> baseline_s_grounded` | 50 | +1,80 | -0,20 | +2,00 | +12,20 | +4,36 | [si] |
| `c2696cd2` | `baseline_k_rr_grounded -> baseline_s_rr_grounded` | 50 | +7,60 | +5,60 | +4,00 | +5,60 | +6,20 | [si] |
| `c2696cd2` | `optimized_k -> optimized_s` | 50 | +24,00 | +23,60 | +15,20 | +30,00 | +21,44 | [si] |
| `c2696cd2` | `optimized_k_rr -> optimized_s_rr` | 50 | +13,90 | +13,60 | +6,00 | +23,60 | +14,30 | [si] |
| `c2696cd2` | `optimized_k_grounded -> optimized_s_grounded` | 50 | +18,40 | +12,00 | +0,80 | +28,00 | +17,40 | [si] |
| `c2696cd2` | `optimized_k_rr_grounded -> optimized_s_rr_grounded` | 50 | +2,00 | -2,00 | -1,20 | +14,00 | +3,40 | [si] |
| `5e34e77c` | `baseline_k -> baseline_s` | 50 | +1,60 | +4,60 | +5,60 | +12,80 | +0,88 | [si] |
| `5e34e77c` | `baseline_k_rr -> baseline_s_rr` | 50 | +9,60 | +0,26 | +2,84 | +2,30 | +8,08 | [si] |
| `5e34e77c` | `baseline_k_grounded -> baseline_s_grounded` | 50 | +2,40 | +2,40 | +3,20 | -1,60 | +4,08 | [si] |
| `5e34e77c` | `baseline_k_rr_grounded -> baseline_s_rr_grounded` | 50 | +7,60 | +1,60 | -0,80 | +10,00 | +6,90 | [si] |
| `5e34e77c` | `optimized_k -> optimized_s` | 50 | +14,00 | +12,60 | +13,20 | +26,00 | +13,84 | [si] |
| `5e34e77c` | `optimized_k_rr -> optimized_s_rr` | 50 | +17,80 | +13,60 | +3,72 | +25,60 | +15,70 | [si] |
| `5e34e77c` | `optimized_k_grounded -> optimized_s_grounded` | 50 | +10,00 | +2,00 | +0,00 | +20,00 | +8,70 | [si] |
| `5e34e77c` | `optimized_k_rr_grounded -> optimized_s_rr_grounded` | 50 | +6,00 | -2,40 | +2,00 | +18,00 | +7,42 | [si] |
