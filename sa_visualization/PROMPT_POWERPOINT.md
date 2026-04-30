# Prompt para Claude for PowerPoint

Copia y pega el siguiente prompt en Claude for PowerPoint. Después adjunta los archivos de la carpeta `outputs/` cuando te los pida (o arrástralos al inicio).

---

## PROMPT

Crea una presentación profesional en español sobre **"Simulated Annealing vs Hill Climbing"** para una exposición universitaria de máximo 5 minutos. El tema es una tarea del curso de Inteligencia Artificial / Algoritmos de Búsqueda. El público son compañeros de clase y un docente.

**Estilo visual:** Limpio, moderno, paleta azul/rojo (azul = Simulated Annealing, rojo = Hill Climbing). Tipografía sans-serif. Cada diapositiva con un título claro, poco texto y mucho apoyo visual.

**Estructura sugerida (10–11 diapositivas):**

### 1. Portada
- Título: **Simulated Annealing vs Hill Climbing**
- Subtítulo: Implementación, comparativa y análisis de hiperparámetros
- Curso, integrantes (5 nombres — dejar placeholders)
- Fecha

### 2. Introducción al problema
- ¿Qué es la optimización? Espacio de búsqueda, mínimos locales vs globales
- Una imagen / esquema simple de un paisaje con varios valles
- Mensaje clave: *"Los algoritmos avaros se atascan; necesitamos exploración"*

### 3. Hill Climbing (HC)
- Pseudocódigo corto (5–6 líneas)
- Idea: solo aceptar vecinos que mejoran
- Ventaja: simple y rápido
- Desventaja: se atasca en óptimos locales

### 4. Simulated Annealing (SA)
- Inspiración: enfriamiento de metales
- Pseudocódigo (recuadro pequeño)
- Fórmula clave: **P(aceptar peor) = exp(−Δ/T)**
- Idea visual: temperatura alta → exploración; temperatura baja → explotación
- Hiperparámetros: T₀, α, iter_por_T, T_final

### 5. Problemas usados
Dos columnas:
- **Función Rastrigin (continua):** muchos mínimos locales en una rejilla, mínimo global en (0,0). Dominio [-5.12, 5.12]ⁿ.
- **TSP (combinatorio):** encontrar la ruta más corta que visita todas las ciudades. Operador 2-opt para vecinos.

### 6. Visualización: Rastrigin
- **Insertar GIF**: `rastrigin_hc_vs_sa.gif` (lado izquierdo HC, derecho SA)
- Texto corto: "HC se queda en el primer valle; SA salta entre valles y converge mejor"

### 7. Visualización: TSP
- **Insertar GIF**: `tsp_hc_vs_sa.gif`
- Texto corto: "Ambos mejoran la ruta, pero SA encuentra rutas más cortas, especialmente con n grande"

### 8. Comparativa cuantitativa
Dos columnas con las gráficas:
- **Insertar imagen** `comparativa_rastrigin.png`
- **Insertar imagen** `comparativa_tsp.png`

Conclusiones (bullets cortos):
- En TSP, SA gana claramente cuando n crece (con n=80, SA ≈ 794 vs HC ≈ 1056, **~25% mejor**)
- HC es entre 5–10× más rápido pero la calidad cae drásticamente con n grande
- **SA paga tiempo extra a cambio de calidad**

### 9. Análisis de hiperparámetros
Tres columnas / tres mini-gráficas:
- **Insertar** `hiper_temperatura_inicial.png` — *"T₀ muy baja = no explora. Encima de cierto umbral (~20) la calidad es estable"*
- **Insertar** `hiper_alpha.png` — *"α más cercano a 1 = enfriamiento más lento = mejor calidad pero mucho más tiempo. Sweet spot: α ∈ [0.99, 0.995]"*
- **Insertar** `hiper_iter_por_T.png` — *"Subir iter_por_T mejora calidad, pero el costo es lineal"*

### 10. Valores recomendados (tabla)
| Hiperparámetro | Rango bajo | Recomendado | Rango alto |
|---|---|---|---|
| T₀ (temperatura inicial) | 1–5 | **50–100** | 500+ |
| α (factor de enfriamiento) | 0.80–0.90 | **0.99–0.995** | 0.999 |
| iter_por_T | 1–5 | **15–25** | 50+ |
| T_final | — | **0.01–0.1** | — |

### 11. Conclusiones
- HC = rápido y simple, **bueno para problemas pequeños o convexos**
- SA = más lento pero **logra mejor calidad** y escala mejor con n
- Los hiperparámetros de SA importan: el factor α es el más sensible
- En problemas combinatorios grandes (TSP n≥30), SA es la mejor opción
- Trade-off claro: **calidad vs tiempo**

### 12. Gracias / Preguntas
- Slide final con "¿Preguntas?" y nombres del equipo

---

**Notas adicionales para Claude for PowerPoint:**
- Usa los colores: rojo `#d62728` para HC, azul `#1f77b4` para SA, verde `#2ca02c` para tiempo
- El texto debe estar en español
- Mantén bullets cortos (máximo una línea)
- Las imágenes deben ocupar ≥ 60% del espacio en las diapositivas que las contienen
- Total de palabras de texto bajo: la presentación es de 5 minutos, ~30 segundos por slide
- Si insertas pseudocódigo, usa fuente monoespaciada y fondo gris claro

**Archivos a adjuntar:**
- `outputs/rastrigin_hc_vs_sa.gif` (slide 6)
- `outputs/tsp_hc_vs_sa.gif` (slide 7)
- `outputs/comparativa_rastrigin.png` (slide 8)
- `outputs/comparativa_tsp.png` (slide 8)
- `outputs/hiper_temperatura_inicial.png` (slide 9)
- `outputs/hiper_alpha.png` (slide 9)
- `outputs/hiper_iter_por_T.png` (slide 9)
