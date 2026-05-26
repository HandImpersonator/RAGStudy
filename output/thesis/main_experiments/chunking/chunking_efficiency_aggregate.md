# Eficiencia de chunking - resumen agregado

Runs escaneados: **52** · Pares totales: **30**

La agregación está **ponderada por n_paired_completed** para que los runs de 10 muestras y los de 625 contribuyan proporcionalmente.  Todos los runs extraen preguntas del mismo caché - los tamaños de contexto son deterministas para un par (pregunta, chunker) dado, por lo que las medias ponderadas reflejan la cobertura real de preguntas, no el número de runs.

'Δ < 0 consistente' significa que la reducción del tamaño de contexto se mantiene en > 80 % de los runs individuales.

## Reducción de contexto por (retriever, variante)

| Retriever | Variante | n_runs | total_n | avg_chunk_size Δ (chars) | context_chars Δ% | context_tokens Δ% | ¿Consistente? |
|---|---|---:|---:|---:|---:|---:|:---:|
| `s` | `(none)` | 10 | 6250 | -59,86 | -12,25% | -12,25% | [si] |
| `s` | `rr` | 10 | 6250 | -73,57 | -14,65% | -14,65% | [si] |
| `s` | `rr_grounded` | 10 | 6250 | -73,57 | -14,65% | -14,65% | [si] |

## Preservación de calidad por (retriever, variante)

| Retriever | Variante | n_runs | total_n | Exactitud Δ | Global Δ | ¿Todo equiv (≤2 pts)? | % afirmación soportada |
|---|---|---:|---:|---:|---:|:---:|---:|
| `s` | `(none)` | 10 | 6250 | -1,66 | -1,41 | [no] | 60% |
| `s` | `rr` | 10 | 6250 | -2,27 | -1,83 | [no] | 40% |
| `s` | `rr_grounded` | 10 | 6250 | -1,31 | -1,24 | [no] | 70% |

## Global (ponderado por tamaño muestral)

- **17/30** pares soportan la afirmación completa (contexto reducido Y calidad preservada).
- Δ media ponderada context_chars: **-13,85%**
- Δ media ponderada context_tokens: **-13,85%**
- Δ media ponderada exactitud: **-1,75 pts** (dentro del umbral de equivalencia).

> **Nota sobre solapamiento de runs**: todos los runs usan el mismo caché de preguntas.  Los runs de 10 muestras cubren las mismas preguntas que las primeras filas de los runs de 625 muestras.  Para estadísticas de publicación, usa `--min-samples 600` para comparar solo los runs de dataset completo, donde cada pregunta se cuenta exactamente una vez.

