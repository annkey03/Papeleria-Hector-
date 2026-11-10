"""
Configuración central del proyecto.

Aquí viven las rutas, los parámetros del modelo, el catálogo de productos
estratégicos y los escenarios de prueba. Cambiar un valor en este archivo
es suficiente para ajustar el dashboard sin tocar la lógica.
"""

import os
from pathlib import Path

# ------------------------------------------------------------------
# Rutas (relativas al proyecto; se puede sobreescribir con una variable
# de entorno para no depender de una ruta fija del equipo)
# ------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
RUTA_DATASET = Path(os.environ.get("DATASET_PATH", BASE_DIR / "dataset.xlsx"))
HOJA_DATASET = "Dataset"

# ------------------------------------------------------------------
# Ventana de análisis definida en el informe del proyecto
# ------------------------------------------------------------------
FECHA_INICIO = "2025-01-01"
FECHA_FIN = "2026-08-31"
PERIODOS_PRONOSTICO = ["2026-10", "2026-11", "2026-12"]  # Q4 2026
HORIZONTE_MESES = len(PERIODOS_PRONOSTICO)

# ------------------------------------------------------------------
# Parámetros del modelo
# ------------------------------------------------------------------
BOOTSTRAP_ITERACIONES = 1000
# Semilla fija: el remuestreo es aleatorio, pero con semilla el resultado
# es reproducible (esta semilla reproduce los valores del informe).
SEMILLA = 8

# ------------------------------------------------------------------
# Catálogo de productos estratégicos
# (los precios y las ventas se leen del dataset; el proveedor y la
#  existencia inicial no están en el dataset y se registran aquí)
# ------------------------------------------------------------------
PROVEEDOR_SIN_REGISTRO = "Sin registro"
PROVEEDOR_SUGERIDO = "Importadora Escolar Colombia"

PRODUCTOS = [
    {"id": 75, "nombre": "Calculadora básica", "categoria": "Oficina / Cálculo",
     "existencia_inicial": 2, "proveedor": "Distribuidora El Lápiz Dorado"},
    {"id": 54, "nombre": "Papel bond oficio resma x500", "categoria": "Papelería",
     "existencia_inicial": 8, "proveedor": "Mayorista Papelera Bogotá"},
    {"id": 107, "nombre": "Recarga de tinta negra", "categoria": "Insumos",
     "existencia_inicial": 4, "proveedor": "Importadora Escolar Colombia"},
    {"id": 80, "nombre": "Mapa de Colombia político", "categoria": "Geografía",
     "existencia_inicial": 1, "proveedor": PROVEEDOR_SIN_REGISTRO},
    {"id": 81, "nombre": "Mapa mundi político", "categoria": "Geografía",
     "existencia_inicial": 6, "proveedor": PROVEEDOR_SIN_REGISTRO},
    {"id": 77, "nombre": "USB 16GB", "categoria": "Tecnología",
     "existencia_inicial": 3, "proveedor": PROVEEDOR_SIN_REGISTRO},
    {"id": 78, "nombre": "USB 32GB", "categoria": "Tecnología",
     "existencia_inicial": 5, "proveedor": PROVEEDOR_SIN_REGISTRO},
]

# ------------------------------------------------------------------
# Escenarios de prueba (variables predictoras que el usuario puede variar)
#   factor     : multiplicador de la demanda histórica
#   nivel      : nivel de servicio objetivo (percentil del bootstrap)
#   ventana    : meses de la media móvil
#   presupuesto: tope de compra en COP (None = sin límite)
# ------------------------------------------------------------------
ESCENARIOS = {
    "Conservador": {"factor": 0.80, "nivel": 0.80, "ventana": 6, "presupuesto": 350_000},
    "Base": {"factor": 1.00, "nivel": 0.90, "ventana": 6, "presupuesto": None},
    "Optimista": {"factor": 1.25, "nivel": 0.95, "ventana": 6, "presupuesto": 600_000},
}

# ------------------------------------------------------------------
# Paleta visual
# ------------------------------------------------------------------
COLOR_PRIMARIO = "#2563EB"
COLOR_SECUNDARIO = "#94A3B8"
COLOR_OK = "#10B981"
COLOR_ALERTA = "#EF4444"
COLOR_AVISO = "#F59E0B"
