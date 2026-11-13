"""
Capa de datos: lectura del dataset y construcción del catálogo.

No contiene lógica predictiva ni de interfaz; solo carga, valida y
organiza la información histórica de ventas.
"""

import datetime as dt
import hashlib
import io
from pathlib import Path

import pandas as pd

from config import (
    FECHA_INICIO,
    HOJA_DATASET,
    PRODUCTOS,
    RUTA_CARGAS,
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
        DataFrame con las ventas de los productos estratégicos desde
        ``FECHA_INICIO`` (dataset base + ventas cargadas por el vendedor).

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

    # Ventas nuevas subidas por el vendedor (si existen)
    if Path(RUTA_CARGAS).exists():
        nuevas = pd.read_csv(RUTA_CARGAS)
        if len(nuevas):
            nuevas["fecha_venta"] = pd.to_datetime(nuevas["fecha_venta"])
            df = pd.concat([df, nuevas.drop(columns=["lote", "archivo", "cargado_en"], errors="ignore")],
                           ignore_index=True)

    ids = [p["id"] for p in PRODUCTOS]
    filtro = df["id_producto"].isin(ids) & (df["fecha_venta"] >= FECHA_INICIO)
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


def ultimo_mes_completo(ventas: pd.DataFrame, hoy: dt.date = None) -> dt.date:
    """Fecha final sugerida para el modelo: fin del último mes ya terminado con ventas.

    Es el menor entre (a) el último día del mes anterior al actual y (b) el
    último día del mes de la venta más reciente. Así nunca se incluye un mes
    a medias, que bajaría el promedio de ventas.
    """
    hoy = hoy or dt.date.today()
    mes_anterior = (pd.Timestamp(hoy).to_period("M").start_time - pd.Timedelta(days=1)).date()
    mes_ultima_venta = (ventas["fecha_venta"].max() + pd.offsets.MonthEnd(0)).date()
    return min(mes_anterior, mes_ultima_venta)


# ------------------------------------------------------------------
# Carga de ventas por el vendedor
# ------------------------------------------------------------------
COLUMNAS_CARGA = ["fecha_venta", "nombre_producto", "cantidad_vendida"]
COLUMNAS_GUARDADAS = ["fecha_venta", "id_producto", "cantidad_vendida",
                      "precio_compra_producto", "precio_venta_producto",
                      "lote", "archivo", "cargado_en"]


def _normalizar(texto) -> str:
    return " ".join(str(texto).strip().lower().split())


def plantilla_xlsx(catalogo: pd.DataFrame) -> bytes:
    """Plantilla de Excel para que el vendedor registre ventas (con lista desplegable de productos)."""
    from openpyxl import Workbook
    from openpyxl.worksheet.datavalidation import DataValidation

    wb = Workbook()
    ws = wb.active
    ws.title = "Ventas"
    ws.append(COLUMNAS_CARGA)
    for col, ancho in zip("ABC", (16, 38, 18)):
        ws.column_dimensions[col].width = ancho

    hoja_prod = wb.create_sheet("Productos")
    hoja_prod.append(["Productos disponibles"])
    for nombre in catalogo["producto"]:
        hoja_prod.append([nombre])
    hoja_prod.column_dimensions["A"].width = 38

    lista = DataValidation(type="list", formula1=f"=Productos!$A$2:$A${len(catalogo) + 1}",
                           allow_blank=True, showErrorMessage=True,
                           error="Elige un producto de la lista.")
    ws.add_data_validation(lista)
    lista.add("B2:B1000")
    for fila in range(2, 1001):
        ws[f"A{fila}"].number_format = "yyyy-mm-dd"

    salida = io.BytesIO()
    wb.save(salida)
    return salida.getvalue()


def validar_carga(contenido: bytes, nombre_archivo: str, catalogo: pd.DataFrame):
    """Lee y valida un archivo de ventas (.xlsx o .csv) subido por el vendedor.

    Returns:
        (ventas_ok, errores, avisos): ``ventas_ok`` es un DataFrame con
        ``fecha_venta``, ``id_producto``, ``producto`` y ``cantidad_vendida``;
        ``errores`` impiden guardar; ``avisos`` son solo informativos.
    """
    errores, avisos = [], []
    try:
        if nombre_archivo.lower().endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contenido), sep=None, engine="python", encoding="utf-8-sig")
        else:
            df = pd.read_excel(io.BytesIO(contenido), sheet_name=0)
    except Exception:  # archivo dañado o formato no soportado
        return None, ["No se pudo leer el archivo. Usa la plantilla de Excel o un CSV."], []

    df.columns = [_normalizar(c).replace(" ", "_") for c in df.columns]
    df = df.dropna(how="all")
    if df.empty:
        return None, ["El archivo no tiene ventas."], []

    tiene_producto = "nombre_producto" in df.columns or "id_producto" in df.columns
    faltan = [c for c in ("fecha_venta", "cantidad_vendida") if c not in df.columns]
    if faltan or not tiene_producto:
        pedidas = "fecha_venta, nombre_producto, cantidad_vendida"
        return None, [f"Faltan columnas. El archivo debe tener: {pedidas}."], []

    df["fila"] = df.index + 2  # número de fila como lo ve el usuario en Excel

    # --- producto ---
    por_nombre = {_normalizar(n): i for n, i in zip(catalogo["producto"], catalogo["id_producto"])}
    if "id_producto" in df.columns:
        df["id_producto"] = pd.to_numeric(df["id_producto"], errors="coerce")
    else:
        df["id_producto"] = df["nombre_producto"].map(lambda n: por_nombre.get(_normalizar(n)))
    nombres = dict(zip(catalogo["id_producto"], catalogo["producto"]))

    # --- fecha y cantidad ---
    df["fecha_venta"] = _parsear_fechas(df["fecha_venta"])
    df["cantidad_vendida"] = pd.to_numeric(df["cantidad_vendida"], errors="coerce")

    malas_fecha = df.loc[df["fecha_venta"].isna(), "fila"].tolist()
    if malas_fecha:
        errores.append(f"Fecha inválida o vacía en las filas: {_listar(malas_fecha)}.")
    futuras = df.loc[df["fecha_venta"] > pd.Timestamp(dt.date.today()), "fila"].tolist()
    if futuras:
        errores.append(f"Hay fechas futuras en las filas: {_listar(futuras)}.")
    malas_cant = df.loc[~(df["cantidad_vendida"] > 0)
                        | (df["cantidad_vendida"] % 1 != 0), "fila"].tolist()
    if malas_cant:
        errores.append(f"La cantidad debe ser un número entero mayor que 0 (filas: {_listar(malas_cant)}).")

    # --- productos fuera del plan: se ignoran, pero se avisa ---
    fuera = df[~df["id_producto"].isin(nombres)]
    if len(fuera):
        avisos.append(f"{len(fuera)} fila(s) con productos que no están en el pronóstico se ignorarán "
                      f"(filas: {_listar(fuera['fila'].tolist())}).")
    ok = df[df["id_producto"].isin(nombres)].dropna(subset=["fecha_venta", "cantidad_vendida"]).copy()
    ok = ok[(ok["cantidad_vendida"] > 0) & (ok["cantidad_vendida"] % 1 == 0)]
    if ok.empty and not errores:
        errores.append("Ninguna fila corresponde a los productos del pronóstico.")

    ok["id_producto"] = ok["id_producto"].astype(int)
    ok["cantidad_vendida"] = ok["cantidad_vendida"].astype(int)
    ok["producto"] = ok["id_producto"].map(nombres)
    return ok[["fecha_venta", "id_producto", "producto", "cantidad_vendida"]].reset_index(drop=True), errores, avisos


def _parsear_fechas(serie: pd.Series) -> pd.Series:
    """Convierte a fecha respetando el formato ISO (2026-09-01) y, si no, día/mes/año (03/09/2026)."""
    if pd.api.types.is_datetime64_any_dtype(serie):
        return serie
    texto = serie.astype(str).str.strip()
    fechas = pd.to_datetime(texto, format="ISO8601", errors="coerce")
    resto = fechas.isna()
    if resto.any():
        fechas[resto] = pd.to_datetime(texto[resto], dayfirst=True, errors="coerce", format="mixed")
    return fechas


def _listar(filas, maximo: int = 8) -> str:
    texto = ", ".join(str(int(f)) for f in filas[:maximo])
    return texto + (" …" if len(filas) > maximo else "")


def huella(contenido: bytes) -> str:
    """Identificador del archivo (evita cargar dos veces el mismo)."""
    return hashlib.sha1(contenido).hexdigest()[:12]


def lotes_cargados() -> pd.DataFrame:
    """Resumen de los archivos ya cargados (uno por fila)."""
    if not Path(RUTA_CARGAS).exists():
        return pd.DataFrame(columns=["lote", "archivo", "cargado_en", "filas", "desde", "hasta"])
    df = pd.read_csv(RUTA_CARGAS, parse_dates=["fecha_venta"])
    if df.empty:
        return pd.DataFrame(columns=["lote", "archivo", "cargado_en", "filas", "desde", "hasta"])
    return (df.groupby("lote", sort=False)
            .agg(archivo=("archivo", "first"), cargado_en=("cargado_en", "first"),
                 filas=("fecha_venta", "size"), desde=("fecha_venta", "min"), hasta=("fecha_venta", "max"))
            .reset_index().sort_values("cargado_en", ascending=False))


def guardar_carga(ventas_ok: pd.DataFrame, catalogo: pd.DataFrame, lote: str, archivo: str) -> None:
    """Agrega las ventas validadas al histórico (precios tomados del catálogo)."""
    if lote in set(lotes_cargados()["lote"]):
        raise ValueError("Este archivo ya fue cargado antes.")
    precios = catalogo.set_index("id_producto")[["precio_compra", "precio_venta"]]
    nuevas = ventas_ok[["fecha_venta", "id_producto", "cantidad_vendida"]].copy()
    nuevas["precio_compra_producto"] = nuevas["id_producto"].map(precios["precio_compra"])
    nuevas["precio_venta_producto"] = nuevas["id_producto"].map(precios["precio_venta"])
    nuevas["lote"], nuevas["archivo"] = lote, archivo
    nuevas["cargado_en"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    ruta = Path(RUTA_CARGAS)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    nuevas[COLUMNAS_GUARDADAS].to_csv(ruta, mode="a", header=not ruta.exists(), index=False)


def eliminar_lote(lote: str) -> None:
    """Deshace una carga (por si el vendedor subió un archivo equivocado)."""
    ruta = Path(RUTA_CARGAS)
    if not ruta.exists():
        return
    df = pd.read_csv(ruta)
    restante = df[df["lote"] != lote]
    if restante.empty:
        ruta.unlink()  # sin cargas: se vuelve al dataset base
    else:
        restante.to_csv(ruta, index=False)
