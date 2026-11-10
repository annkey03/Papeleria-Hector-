"""
Capa de datos: lectura del dataset y construcción del catálogo.

No contiene lógica predictiva ni de interfaz; solo carga, valida y
organiza la información histórica de ventas.
"""

from pathlib import Path

import pandas as pd

from config import (
    FECHA_FIN,
    FECHA_INICIO,
    HOJA_DATASET,
    PRODUCTOS,
    RUTA_DATASET,
)

COLUMNAS_REQUERIDAS = {
    "fecha_venta",
    "id_producto",
    "cantidad_vendida",
    "precio_compra_producto",
    "precio_venta_producto",
}


def cargar_ventas(ruta: Path = RUTA_DATASET) -> pd.DataFrame:
    """Lee el dataset de ventas y lo filtra a la ventana y productos del informe.

    Args:
        ruta: ubicación de ``dataset.xlsx`` (por defecto, la del proyecto o la
            definida en la variable de entorno ``DATASET_PATH``).

    Returns:
        DataFrame con las ventas de los productos estratégicos entre
        ``FECHA_INICIO`` y ``FECHA_FIN``.

    Raises:
        FileNotFoundError: si el archivo no existe.
        ValueError: si faltan columnas necesarias.
    """
    if not Path(ruta).exists():
        raise FileNotFoundError(
            f"No se encontró el dataset en '{ruta}'. Colócalo junto a app.py "
            "o define la variable de entorno DATASET_PATH."
        )

    df = pd.read_excel(ruta, sheet_name=HOJA_DATASET)
    faltantes = COLUMNAS_REQUERIDAS - set(df.columns)
    if faltantes:
        raise ValueError(f"Al dataset le faltan columnas: {sorted(faltantes)}")

    df["fecha_venta"] = pd.to_datetime(df["fecha_venta"])
    ids = [p["id"] for p in PRODUCTOS]
    filtro = (
        df["id_producto"].isin(ids)
        & (df["fecha_venta"] >= FECHA_INICIO)
        & (df["fecha_venta"] <= FECHA_FIN)
    )
    return df.loc[filtro].copy()


def construir_catalogo(ventas: pd.DataFrame) -> pd.DataFrame:
    """Combina el catálogo configurado con los precios reales del dataset.

    El precio de compra y de venta se toma de la moda observada en las ventas
    de cada producto, de modo que el catálogo siempre refleja los datos.
    """
    precios = (
        ventas.groupby("id_producto")[["precio_compra_producto", "precio_venta_producto"]]
        .agg(lambda s: s.mode().iloc[0])
        .rename(columns={
            "precio_compra_producto": "precio_compra",
            "precio_venta_producto": "precio_venta",
        })
    )
    catalogo = pd.DataFrame(PRODUCTOS).rename(columns={
        "id": "id_producto",
        "nombre": "producto",
    })
    catalogo = catalogo.merge(precios, on="id_producto", how="left")
    catalogo["utilidad_unit"] = catalogo["precio_venta"] - catalogo["precio_compra"]
    return catalogo


def ventas_mensuales(ventas: pd.DataFrame, fecha_ini, fecha_fin) -> pd.DataFrame:
    """Unidades vendidas por mes y producto (formato ancho).

    Los meses sin ventas se rellenan con 0 para que la serie sea continua,
    algo necesario para que la media móvil y el bootstrap sean correctos.

    Returns:
        DataFrame con índice de periodos mensuales y una columna por
        ``id_producto``.
    """
    rango = ventas[
        (ventas["fecha_venta"].dt.date >= fecha_ini)
        & (ventas["fecha_venta"].dt.date <= fecha_fin)
    ]
    periodos = pd.period_range(fecha_ini, fecha_fin, freq="M")
    tabla = (
        rango.assign(periodo=rango["fecha_venta"].dt.to_period("M"))
        .pivot_table(index="periodo", columns="id_producto",
                     values="cantidad_vendida", aggfunc="sum")
        .reindex(periodos)
        .fillna(0)
    )
    for p in PRODUCTOS:  # garantiza una columna por producto, aunque no venda
        if p["id"] not in tabla.columns:
            tabla[p["id"]] = 0.0
    return tabla[[p["id"] for p in PRODUCTOS]]
