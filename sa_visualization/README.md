# Simulated Annealing vs Hill Climbing — Visualización

Tarea de comparación de **Hill Climbing (HC)** y **Simulated Annealing (SA)**
sobre dos problemas: optimización de la función Rastrigin y TSP.

## Estructura

```
sa_visualization/
├── src/
│   ├── algorithms.py             # HC y SA genéricos
│   ├── problema_funcion.py       # Función Rastrigin
│   ├── problema_tsp.py           # Traveling Salesman Problem
│   ├── viz_funcion.py            # Animación GIF — Rastrigin 2D
│   ├── viz_tsp.py                # Animación GIF — TSP
│   ├── comparativa.py            # Comparativa con varios n
│   ├── analisis_hiperparametros.py  # Hiperparámetros de SA
│   └── run_all.py                # Ejecuta todo
└── outputs/
    ├── rastrigin_hc_vs_sa.gif
    ├── tsp_hc_vs_sa.gif
    ├── comparativa_rastrigin.png
    ├── comparativa_tsp.png
    ├── hiper_temperatura_inicial.png
    ├── hiper_alpha.png
    ├── hiper_iter_por_T.png
    └── resultados.csv
```

## Ejecución

```bash
cd sa_visualization/src
python run_all.py
```

Requiere: `numpy`, `matplotlib`, `pillow`.

## Algoritmos implementados

**Hill Climbing**: parte de un estado inicial y solo se mueve a vecinos que
mejoran el costo. Se queda atrapado en mínimos locales.

**Simulated Annealing**: igual que HC pero acepta peores soluciones con
probabilidad `exp(-Δ/T)`. La temperatura `T` decrece con el tiempo según
`T = T * alpha`. Esto permite escapar de mínimos locales al inicio y
converger al final.
