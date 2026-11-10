# 📦 Dashboard Predictivo de Demanda e Inventarios | Papelería Héctor

Este repositorio contiene la solución analítica interactiva y predictiva desarrollada para la **Papelería y Miscelánea Héctor** (Mosquera, Cundinamarca), desarrollada como parte del **Proyecto de Aula** de la asignatura **Business Analytics 802** en la **Universidad de Cundinamarca**.

---

## 👨‍💻 Información del Proyecto y Grupo

* **Asignatura:** Business Analytics 802
* **Docente:** Ivon Forero
* **Institución:** Universidad de Cundinamarca — Facultad de Ingeniería
* **Grupo 01:** 
  * Snattan Espitia
  * Angela Palacios
  * Juan Rueda
  * Oscar Becerra
  * Anna Arenales

---

## 🎯 Objetivo del Sistema

Desarrollar una herramienta analítica predictiva en **Streamlit** que automatice la gestión de inventarios para 7 productos estratégicos mediante:
1. **Pronóstico de Demanda:** Cálculo de la demanda esperada para el trimestre Q4 mediante el modelo de **Media Móvil de 6 Meses**.
2. **Dimensionamiento de Inventario de Seguridad:** Determinación de stock de cobertura al **90% de nivel de servicio (P90)** aplicando **Remuestreo Bootstrap (1,000 iteraciones)** sobre las ventas históricas.
3. **Plan Operativo y Simulación:** Generación automática de recomendaciones de compra en unidades y en pesos colombianos ($COP$) basadas en las existencias reales en bodega ingresadas por el usuario.

---

## 📊 Estructura del Dashboard

La aplicación web está dividida en 3 pestañas principales de análisis:

1. **📊 Resumen Predictivo Q4:**
   * KPIs globales: Demanda esperada, inversión requerida ($COP$), utilidad proyectada y nivel de servicio ajustado.
   * Gráficos comparativos de Demanda vs. Stock P90 y distribución de capital de inversión por producto.

2. **🔎 Análisis Drill-Down por Producto:**
   * **Comparativo Global:** Grafica la serie temporal histórica de todos los productos estratégicos juntos para comparar tendencias.
   * **Análisis Individual:** Gráfico detallado mes a mes de cada referencia frente a su meta de stock mensual equivalente.

3. **📋 Plan Operativo de Compras y Alertas:**
   * **Simulador Individual por Producto:** Permite ingresar la existencia real en bodega para cada ítem de forma independiente.
   * Matriz interactiva de compras con semáforo de estado (`🔴 PEDIR`, `🟡 VIGILAR`, `🟢 SUFICIENTE`).
   * Diagnóstico gerencial automático sobre la cadena de suministro y proveedores.

---

## 📂 Estructura del Repositorio

```text
├── app.py              # Código principal del Dashboard en Streamlit
├── dataset.xlsx        # Base de datos histórica de ventas (2025-2026)
├── requirements.txt    # Lista de dependencias de Python requeridas
└── README.md           # Guía de instalación y documentación del proyecto
```

---

## 🚀 Instrucciones de Instalación y Ejecución Local

Sigue estos pasos para ejecutar la aplicación en tu equipo local:

### 1. Clonar el Repositorio
```bash
git clone https://github.com/TU_USUARIO/proyecto-papeleria-hector.git
cd proyecto-papeleria-hector
```

### 2. Crear y Activar Entorno Virtual (Opcional pero recomendado)
* En Windows (PowerShell):
  ```bash
  python -m venv venv
  .\venv\Scripts\activate
  ```
* En macOS/Linux:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar el Dashboard
```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador predeterminado en `http://localhost:8501`.

---

## 🛠️ Tecnologías Utilizadas

* **Lenguaje:** Python 3.10+
* **Interfaz de Usuario:** Streamlit
* **Procesamiento de Datos:** Pandas, NumPy
* **Visualización de Datos:** Plotly Express & Plotly Graph Objects
* **Lectura de Archivos:** OpenPyXL

---
*Universidad de Cundinamarca — Facultad de Ingeniería — 2026*
