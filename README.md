# 📦 Dashboard Predictivo de Demanda e Inventarios · Papelería Héctor

Solución analítica interactiva para la **Papelería y Miscelánea Héctor** (Mosquera, Cundinamarca).
Proyecto de aula de **Business Analytics 802**, Universidad de Cundinamarca — Facultad de Ingeniería.

* **Docente:** Ivon Forero
* **Grupo 01:** Snattan Espitia · Angela Palacios · Juan Rueda · Oscar Becerra · Anna Arenales

---

## 🎯 Pregunta de predicción

> ¿Cuántas unidades de cada uno de los siete productos estratégicos venderá la papelería entre
> **octubre y diciembre de 2026**, y cuántas debe tener disponibles para atender esa demanda con un
> **nivel de servicio del 90 %**?

## 🧠 Cómo funciona el modelo

1. **Demanda esperada Q4:** media móvil de los últimos *N* meses (por defecto 6) × 3 meses × factor de demanda.
2. **Stock objetivo:** remuestreo *bootstrap* (1.000 iteraciones) de los meses históricos; se suman 3 meses simulados
   y se toma el percentil del nivel de servicio (P90 por defecto).
3. **Punto de reorden:** percentil del consumo de un mes (cubre el plazo de reposición).
4. **Plan de compras:** stock objetivo − existencia real. Con presupuesto limitado, se prioriza lo que está en
   estado PEDIR y luego lo que más utilidad deja por peso invertido.
5. **Validación (backtesting):** para cada trimestre histórico se calcula el stock con la información disponible
   hasta ese momento y se verifica si cubrió la demanda real. Con P90 la cobertura histórica es **90,5 %**.

### Variables predictoras (se pueden variar en la barra lateral)

| Variable | Efecto en el modelo |
|---|---|
| Factor de demanda | Escala la demanda histórica (0,8 = baja · 1,0 = normal · 1,25 = pico) |
| Nivel de servicio | Percentil del bootstrap (80 %, 85 %, 90 %, 95 %, 99 %) |
| Ventana de media móvil | 3, 6, 9 o 12 meses |
| Presupuesto de compra | Tope en COP para el pedido (opcional) |
| Rango de fechas | Datos históricos con los que se calcula el modelo |

### Escenarios de prueba

Generados con `python tabla_escenarios.py` (los mismos que carga el selector del dashboard):

| | Conservador | Base | Optimista |
|---|---|---|---|
| Factor de demanda | 0,80x | 1,00x | 1,25x |
| Nivel de servicio | 80 % | 90 % | 95 % |
| Presupuesto de compra | $350.000 | Sin límite | $600.000 |
| Demanda esperada Q4 | 27,6 un. | 34,5 un. | 43,1 un. |
| Stock objetivo total | 48 un. | 74 un. | 115 un. |
| Punto de reorden total | 26 un. | 41 un. | 55 un. |
| Inversión en inventario objetivo | $593.500 | $889.000 | $1.399.500 |
| Utilidad bruta proyectada | $169.280 | $211.600 | $264.500 |
| Pedido (unidades / COP) | 20 / $227.500 | 45 / $507.500 | 64 / $587.000 |
| Cobertura histórica | 87,3 % | 90,5 % | 96,8 % |

> El pedido se calcula con las existencias iniciales (2, 8, 4, 1, 6, 3 y 5 unidades).

---

## 🖥️ Estructura del dashboard

1. **📊 Resumen del trimestre** — KPIs, ventas esperadas vs. stock recomendado, dinero invertido por producto y tabla de pronóstico.
2. **🔎 Detalle de ventas** — tres niveles: categorías → productos → producto individual (histórico + pronóstico).
3. **📋 Qué comprar** — simulador de existencias, semáforo (🔴 PEDIR · 🟡 VIGILAR · 🟢 SUFICIENTE),
   compra con presupuesto y alerta de productos sin proveedor.

4. **📤 Cargar ventas** — el vendedor descarga una plantilla de Excel (fecha, producto, cantidad), la sube, revisa una
   vista previa con validaciones y confirma; el pronóstico se recalcula con las ventas nuevas. Las cargas se guardan en
   `data/ventas_cargadas.csv` (se suman a `dataset.xlsx`, que no se modifica), no se puede subir dos veces el mismo
   archivo y cada carga se puede deshacer.

> **Nota de despliegue:** en Streamlit Community Cloud el disco es temporal; si la app se reinicia, las cargas se
> pierden. Para uso real conviene guardarlas en una base de datos o en Google Sheets.

### Interacciones disponibles

* Selector de escenario (Conservador / Base / Optimista) que carga los valores de las variables predictoras.
* Controles de factor de demanda, nivel de servicio, ventana de media móvil y presupuesto.
* Filtro de rango de fechas (recalcula el modelo).
* Filtro por categoría y selección múltiple de productos.
* Drill-down de tres niveles con selectores de categoría y producto.
* Simulador de existencias por producto con semáforo y compra recomendada.

### Capturas

Guardar las capturas en `docs/capturas/` y enlazarlas aquí:

```
docs/capturas/01_resumen_base.png
docs/capturas/02_resumen_conservador.png
docs/capturas/03_resumen_optimista.png
docs/capturas/04_drilldown.png
docs/capturas/05_plan_compras.png
```

---

## 📂 Estructura del repositorio

```text
├── app.py                  # Interfaz Streamlit (solo presentación)
├── config.py               # Rutas, parámetros, catálogo y escenarios
├── data_loader.py          # Carga y ETL del dataset
├── forecast.py             # Media móvil, bootstrap, plan de compras y backtesting
├── charts.py               # Figuras Plotly
├── tabla_escenarios.py     # Genera la tabla de escenarios para el informe
├── tests/test_forecast.py  # Pruebas del modelo
├── dataset.xlsx            # Ventas históricas (2025-2026)
├── requirements.txt
├── .streamlit/config.toml  # Tema visual
└── docs/capturas/          # Pantallazos del dashboard
```

## 🚀 Ejecución local

```bash
git clone https://github.com/annkey03/Papeleria-Hector-.git
cd Papeleria-Hector-

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
streamlit run app.py
```

Se abre en `http://localhost:8501`. Si el dataset está en otra ubicación, define la variable de entorno
`DATASET_PATH` con su ruta.

### Pruebas (opcional)

```bash
pip install pytest
pytest
```

## ⚠️ Notas metodológicas

* El bootstrap es aleatorio; se fija la semilla (`SEMILLA` en `config.py`) para que los resultados sean reproducibles.
  La semilla elegida reproduce los valores del informe.
* Para la recarga de tinta, el P90 exacto cae justo en el límite entre 11 y 12 unidades, por lo que, según la
  semilla, el resultado puede variar en 1 unidad.
* Los productos de geografía y las USB no tienen proveedor registrado en el sistema; el dashboard lo señala como alerta.

## 🛠️ Tecnologías

Python 3.10+ · Streamlit · Pandas · NumPy · Plotly · OpenPyXL

---
*Universidad de Cundinamarca — Facultad de Ingeniería — 2026*
