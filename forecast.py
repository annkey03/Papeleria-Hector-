"""
Motor predictivo: media móvil, remuestreo bootstrap y plan de compras.

Todas las funciones son puras (no dependen de Streamlit), por lo que se
pueden probar y reutilizar fuera del dashboard.
"""

import numpy as np
import pandas as pd

from config import BOOTSTRAP_ITERACIONES, HORIZONTE_MESES, SEMILLA

ORDEN_ESTADO = {"PEDIR": 0, "VIGILAR": 1, "SUFICIENTE": 2}


def media_movil_trimestral(serie: np.ndarray, ventana: int, horizonte: int = HORIZONTE_MESES) -> float:
    """Demanda esperada del trimestre = media de los últimos ``ventana`` meses × horizonte."""
    return float(np.mean(serie[-ventana:]) * horizonte)


def bootstrap_percentil(
    serie: np.ndarray,
    nivel: float,
    horizonte: int = HORIZONTE_MESES,
    iteraciones: int = BOOTSTRAP_ITERACIONES,
    semilla: int = SEMILLA,
) -> float:
    """Percentil de la demanda del trimestre mediante remuestreo bootstrap.

    Se muestrean meses históricos con reemplazo, se suman ``horizonte`` meses
    y se toma el percentil ``nivel`` (p. ej. 0.90) de las 1.000 simulaciones.
    """
    rng = np.random.default_rng(semilla)
    muestras = rng.choice(serie, size=(iteraciones, horizonte), replace=True).sum(axis=1)
    return float(np.percentile(muestras, nivel * 100))


def _entero(x: float) -> int:
    """Redondea hacia arriba tolerando ruido numérico de punto flotante."""
    return int(np.ceil(round(x, 6)))


def calcular_plan(
    ventas_m: pd.DataFrame,
    catalogo: pd.DataFrame,
    factor: float = 1.0,
    nivel: float = 0.90,
    ventana: int = 6,
) -> pd.DataFrame:
    """Calcula demanda, stock objetivo y punto de reorden por producto.

    Args:
        ventas_m: ventas mensuales (salida de ``ventas_mensuales``).
        catalogo: catálogo con precios (salida de ``construir_catalogo``).
        factor: multiplicador de la demanda (0.8 = demanda baja, 1.25 = pico).
        nivel: nivel de servicio objetivo (0.80, 0.90, 0.95...).
        ventana: meses de la media móvil.
    """
    filas = []
    for _, prod in catalogo.iterrows():
        serie = ventas_m[prod["id_producto"]].to_numpy(dtype=float)
        demanda = media_movil_trimestral(serie, ventana) * factor
        stock = _entero(bootstrap_percentil(serie, nivel, semilla=SEMILLA + int(prod["id_producto"])) * factor)
        # Punto de reorden: percentil del consumo de UN mes (cubre el plazo de reposición)
        reorden = _entero(np.percentile(serie, nivel * 100) * factor)
        filas.append({
            "id_producto": prod["id_producto"],
            "demanda_q4": demanda,
            "stock_objetivo": stock,
            "punto_reorden": reorden,
        })
    plan = catalogo.merge(pd.DataFrame(filas), on="id_producto")
    plan["inversion_inventario"] = plan["stock_objetivo"] * plan["precio_compra"]
    plan["utilidad_proyectada"] = plan["demanda_q4"] * plan["utilidad_unit"]
    return plan


def clasificar_estado(existencia: int, reorden: int, stock: int) -> str:
    """Semáforo de inventario: PEDIR / VIGILAR / SUFICIENTE."""
    if existencia <= reorden:
        return "PEDIR"
    if existencia < stock:
        return "VIGILAR"
    return "SUFICIENTE"


def plan_de_compras(plan: pd.DataFrame, existencias: dict, presupuesto=None) -> pd.DataFrame:
    """Calcula qué comprar según las existencias y el presupuesto disponible.

    Sin presupuesto se compra todo lo necesario para llegar al stock objetivo.
    Con presupuesto, se prioriza primero lo que está en estado PEDIR y luego lo
    que más utilidad deja por peso invertido; se compran unidades enteras
    hasta agotar el presupuesto.
    """
    df = plan.copy()
    df["existencia"] = df["id_producto"].map(existencias).astype(int)
    df["estado"] = [
        clasificar_estado(e, r, s)
        for e, r, s in zip(df["existencia"], df["punto_reorden"], df["stock_objetivo"])
    ]
    df["necesaria"] = (df["stock_objetivo"] - df["existencia"]).clip(lower=0)
    df["a_comprar"] = df["necesaria"]

    if presupuesto is not None:
        df["rendimiento"] = df["utilidad_unit"] / df["precio_compra"]
        df["_orden"] = df["estado"].map(ORDEN_ESTADO)
        restante = float(presupuesto)
        df["a_comprar"] = 0
        for idx in df.sort_values(["_orden", "rendimiento"], ascending=[True, False]).index:
            unidades = int(min(df.at[idx, "necesaria"], restante // df.at[idx, "precio_compra"]))
            df.at[idx, "a_comprar"] = unidades
            restante -= unidades * df.at[idx, "precio_compra"]
        df = df.drop(columns=["rendimiento", "_orden"])

    df["inversion_compra"] = df["a_comprar"] * df["precio_compra"]
    df["sin_cubrir"] = df["necesaria"] - df["a_comprar"]
    return df


def backtest_cobertura(
    ventas_m: pd.DataFrame,
    nivel: float,
    horizonte: int = HORIZONTE_MESES,
    historia_minima: int = 9,
    iteraciones: int = 500,
) -> float:
    """Cobertura histórica real del stock P-nivel (validación del modelo).

    Para cada trimestre histórico se calcula el stock con la información
    disponible hasta ese momento y se verifica si cubrió la demanda real.
    Devuelve la fracción de trimestres cubiertos (0 a 1).
    """
    aciertos, total = 0, 0
    for col in ventas_m.columns:
        serie = ventas_m[col].to_numpy(dtype=float)
        for t in range(historia_minima, len(serie) - horizonte + 1):
            stock = _entero(bootstrap_percentil(serie[:t], nivel, horizonte, iteraciones, SEMILLA + int(col)))
            real = serie[t:t + horizonte].sum()
            aciertos += int(real <= stock)
            total += 1
    return aciertos / total if total else float("nan")
