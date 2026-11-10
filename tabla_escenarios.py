"""
Genera la tabla de escenarios de prueba directamente desde el modelo,
para que los números del informe coincidan con los del dashboard.

Uso:  python tabla_escenarios.py
"""

import datetime as dt

import pandas as pd

import data_loader as dl
import forecast as fc
from config import ESCENARIOS, FECHA_FIN, FECHA_INICIO


def generar() -> pd.DataFrame:
    """Evalúa cada escenario de ``config.ESCENARIOS`` con las existencias iniciales."""
    ventas = dl.cargar_ventas()
    catalogo = dl.construir_catalogo(ventas)
    mensual = dl.ventas_mensuales(ventas, dt.date.fromisoformat(FECHA_INICIO), dt.date.fromisoformat(FECHA_FIN))
    existencias = dict(zip(catalogo["id_producto"], catalogo["existencia_inicial"]))

    columnas = {}
    for nombre, esc in ESCENARIOS.items():
        plan = fc.calcular_plan(mensual, catalogo, esc["factor"], esc["nivel"], esc["ventana"])
        compras = fc.plan_de_compras(plan, existencias, esc["presupuesto"])
        cob = fc.backtest_cobertura(mensual, esc["nivel"])
        columnas[nombre] = {
            "Factor de demanda": f"{esc['factor']:.2f}x",
            "Nivel de servicio objetivo": f"{esc['nivel']:.0%}",
            "Ventana media móvil (meses)": esc["ventana"],
            "Presupuesto de compra (COP)": "Sin límite" if esc["presupuesto"] is None else f"${esc['presupuesto']:,.0f}",
            "Demanda esperada Q4 (un.)": f"{plan['demanda_q4'].sum():.1f}",
            "Stock objetivo total (un.)": int(plan["stock_objetivo"].sum()),
            "Punto de reorden total (un.)": int(plan["punto_reorden"].sum()),
            "Inversión en inventario objetivo (COP)": f"${plan['inversion_inventario'].sum():,.0f}",
            "Utilidad bruta proyectada (COP)": f"${plan['utilidad_proyectada'].sum():,.0f}",
            "Unidades a comprar": int(compras["a_comprar"].sum()),
            "Inversión del pedido (COP)": f"${compras['inversion_compra'].sum():,.0f}",
            "Unidades sin cubrir por presupuesto": int(compras["sin_cubrir"].sum()),
            "Cobertura histórica (backtesting)": f"{cob:.1%}",
        }
    return pd.DataFrame(columnas)


if __name__ == "__main__":
    tabla = generar()
    print(tabla.to_string())
    tabla.to_csv("escenarios_resultado.csv", encoding="utf-8-sig")
