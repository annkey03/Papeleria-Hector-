"""
Dashboard predictivo de demanda e inventarios — Papelería y Miscelánea Héctor.

Business Analytics 802 · Universidad de Cundinamarca · Grupo 01.
Ejecución local:  streamlit run app.py

Este archivo contiene SOLO la interfaz. La lógica vive en:
    config.py       parámetros, catálogo y escenarios
    data_loader.py  carga y ETL del dataset
    forecast.py     media móvil, bootstrap y plan de compras
    charts.py       figuras Plotly
"""

import datetime as dt

import pandas as pd
import streamlit as st

import charts
import data_loader as dl
import forecast as fc
from config import (
    COLOR_AVISO, COLOR_OK, COLOR_PRIMARIO, ESCENARIOS, FECHA_FIN, FECHA_INICIO,
    PROVEEDOR_SIN_REGISTRO, PROVEEDOR_SUGERIDO,
)

st.set_page_config(page_title="Dashboard Predictivo | Papelería Héctor",
                   page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
.stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 2px solid #E2E8F0; }
.stTabs [data-baseweb="tab"] { height: 48px; white-space: pre; padding: 0 18px;
    font-weight: 600; font-size: 14px; color: #64748B; border-radius: 8px 8px 0 0; }
.stTabs [aria-selected="true"] { background: #FFFFFF; color: #2563EB !important;
    border-bottom: 3px solid #2563EB !important; }
.metric-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-top: 4px solid #2563EB;
    padding: 18px; border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,.04); }
.metric-title { font-size: 12px; font-weight: 700; color: #64748B;
    text-transform: uppercase; letter-spacing: .05em; }
.metric-value { font-size: 25px; font-weight: 800; color: #0F172A; margin-top: 4px; }
.metric-delta { font-size: 12px; font-weight: 600; margin-top: 4px; }
h1, h2, h3 { color: #0F172A !important; }
section[data-testid="stSidebar"] { background: #FFFFFF !important; border-right: 1px solid #E2E8F0; }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------
# Datos (con caché)
# ------------------------------------------------------------------
@st.cache_data
def cargar():
    """Carga el dataset y construye el catálogo; detiene la app con un mensaje claro si falla."""
    ventas = dl.cargar_ventas()
    return ventas, dl.construir_catalogo(ventas)


@st.cache_data
def modelo(ventas_m, catalogo, factor, nivel, ventana):
    """Plan predictivo (cacheado: se recalcula solo si cambia un parámetro)."""
    return fc.calcular_plan(ventas_m, catalogo, factor, nivel, ventana)


@st.cache_data
def cobertura(ventas_m, nivel):
    """Backtesting del nivel de servicio sobre el histórico seleccionado."""
    return fc.backtest_cobertura(ventas_m, nivel)


try:
    ventas, catalogo = cargar()
except (FileNotFoundError, ValueError) as error:
    st.error(f"No se pudieron cargar los datos: {error}")
    st.stop()


# ------------------------------------------------------------------
# Barra lateral: variables predictoras y filtros
# ------------------------------------------------------------------
def aplicar_escenario():
    """Callback: copia los valores del escenario elegido a los controles."""
    esc = ESCENARIOS[st.session_state["escenario"]]
    st.session_state["factor"] = esc["factor"]
    st.session_state["nivel"] = esc["nivel"]
    st.session_state["ventana"] = esc["ventana"]
    st.session_state["limitar"] = esc["presupuesto"] is not None
    st.session_state["presupuesto"] = esc["presupuesto"] or 600_000


if "escenario" not in st.session_state:
    st.session_state["escenario"] = "Base"
    aplicar_escenario()

with st.sidebar:
    st.markdown("### 🏛️ Papelería Héctor")
    st.caption("Gestión predictiva de inventarios")
    st.markdown("---")

    st.subheader("🎯 Escenario de prueba")
    st.selectbox("Escenario predefinido", list(ESCENARIOS), key="escenario",
                 on_change=aplicar_escenario,
                 help="Carga valores para las variables predictoras. Puedes ajustarlos después.")

    st.subheader("🔧 Variables predictoras")
    st.slider("Factor de demanda", 0.5, 1.5, step=0.05, key="factor",
              help="0.8 = demanda baja · 1.0 = tendencia histórica · 1.25 = pico de temporada")
    st.select_slider("Nivel de servicio objetivo", options=[0.80, 0.85, 0.90, 0.95, 0.99],
                     key="nivel", format_func=lambda x: f"{x:.0%}")
    st.selectbox("Ventana de la media móvil (meses)", [3, 6, 9, 12], key="ventana")
    st.checkbox("Limitar presupuesto de compra", key="limitar")
    if st.session_state["limitar"]:
        st.slider("Presupuesto de compra (COP)", 100_000, 2_000_000, step=50_000, key="presupuesto")

    st.markdown("---")
    st.subheader("📅 Periodo histórico del modelo")
    f_min, f_max = dt.date.fromisoformat(FECHA_INICIO), dt.date.fromisoformat(FECHA_FIN)
    rango = st.date_input("Rango de fechas", value=(f_min, f_max), min_value=f_min, max_value=f_max)

    st.subheader("🏷️ Categorías y productos")
    categoria = st.selectbox("Categoría", ["Todas"] + list(catalogo["categoria"].unique()))
    opciones = catalogo if categoria == "Todas" else catalogo[catalogo["categoria"] == categoria]
    seleccion = st.multiselect("Productos estratégicos", opciones["producto"].tolist(),
                               default=opciones["producto"].tolist())
    st.markdown("---")
    st.caption("Grupo 01 · Business Analytics 802 · Docente: Ivon Forero · Universidad de Cundinamarca")

if not (isinstance(rango, tuple) and len(rango) == 2):
    st.info("Selecciona fecha inicial y final para continuar.")
    st.stop()
if not seleccion:
    st.info("Selecciona al menos un producto para continuar.")
    st.stop()

factor, nivel, ventana = st.session_state["factor"], st.session_state["nivel"], st.session_state["ventana"]
presupuesto = st.session_state["presupuesto"] if st.session_state["limitar"] else None

# ------------------------------------------------------------------
# Cálculos: el rango de fechas define los datos con los que se entrena el modelo
# ------------------------------------------------------------------
ventas_m = dl.ventas_mensuales(ventas, rango[0], rango[1])
if len(ventas_m) < 3:
    st.warning("El periodo elegido tiene menos de 3 meses; amplía el rango para que el modelo sea confiable.")
    st.stop()

plan_total = modelo(ventas_m, catalogo, factor, nivel, ventana)
plan = plan_total[plan_total["producto"].isin(seleccion)].reset_index(drop=True)

st.title("📦 Dashboard Predictivo de Demanda e Inventario Q4 2026")
st.caption(f"¿Cuántas unidades venderá cada producto estratégico entre octubre y diciembre de 2026 y "
           f"cuántas debe haber disponibles con un nivel de servicio del {nivel:.0%}? "
           f"· Media móvil {ventana}M + bootstrap P{nivel:.0%}")

tab1, tab2, tab3 = st.tabs(["📊 Resumen Predictivo Q4", "🔎 Análisis Drill-Down", "📋 Plan Operativo de Compras"])


def tarjeta(titulo, valor, nota, color):
    """Renderiza una tarjeta KPI."""
    return (f'<div class="metric-card" style="border-top-color:{color}">'
            f'<div class="metric-title">{titulo}</div><div class="metric-value">{valor}</div>'
            f'<div class="metric-delta" style="color:{color}">{nota}</div></div>')


# ------------------------------------------------------------------
# Pestaña 1: resumen predictivo
# ------------------------------------------------------------------
with tab1:
    cob = cobertura(ventas_m, nivel)
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(tarjeta("Demanda esperada Q4", f"{plan['demanda_q4'].sum():.1f} un.",
                        f"Media móvil {ventana}M × {factor:.2f}", COLOR_PRIMARIO), unsafe_allow_html=True)
    k2.markdown(tarjeta("Inversión en inventario objetivo", f"${plan['inversion_inventario'].sum():,.0f}",
                        f"{plan['stock_objetivo'].sum()} unidades de stock", "#4F46E5"), unsafe_allow_html=True)
    k3.markdown(tarjeta("Utilidad bruta proyectada", f"${plan['utilidad_proyectada'].sum():,.0f}",
                        "Demanda × margen unitario", COLOR_OK), unsafe_allow_html=True)
    k4.markdown(tarjeta("Cobertura histórica (backtesting)", f"{cob:.1%}",
                        f"Objetivo: {nivel:.0%}", COLOR_AVISO), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Demanda esperada vs. stock objetivo")
        st.plotly_chart(charts.demanda_vs_stock(plan), width='stretch')
    with c2:
        st.subheader("Capital inmovilizado por producto")
        st.plotly_chart(charts.distribucion_inversion(plan), width='stretch')

    st.subheader("Respuesta a la pregunta de predicción")
    st.dataframe(
        plan[["producto", "categoria", "demanda_q4", "stock_objetivo", "punto_reorden"]].rename(columns={
            "producto": "Producto", "categoria": "Categoría", "demanda_q4": "Demanda Q4 (un.)",
            "stock_objetivo": "Stock objetivo", "punto_reorden": "Punto de reorden"}
        ).style.format({"Demanda Q4 (un.)": "{:.1f}"}),
        width='stretch', hide_index=True)

# ------------------------------------------------------------------
# Pestaña 2: drill-down categoría → producto → detalle
# ------------------------------------------------------------------
with tab2:
    nombres = catalogo.set_index("id_producto")[["producto", "categoria"]]
    largo = (ventas_m.rename_axis("periodo").reset_index()
             .melt(id_vars="periodo", var_name="id_producto", value_name="unidades")
             .join(nombres, on="id_producto"))
    largo["periodo"] = largo["periodo"].astype(str)
    largo = largo[largo["producto"].isin(seleccion)]

    nivel_det = st.radio("Nivel de detalle", ["1 · Categorías", "2 · Productos", "3 · Producto individual"],
                         horizontal=True)
    if nivel_det.startswith("1"):
        st.plotly_chart(charts.ventas_por_categoria(largo), width='stretch')
    elif nivel_det.startswith("2"):
        cats = ["Todas"] + sorted(largo["categoria"].unique())
        cat_det = st.selectbox("Categoría a detallar", cats)
        sub = largo if cat_det == "Todas" else largo[largo["categoria"] == cat_det]
        st.plotly_chart(charts.ventas_por_producto(sub, f"Ventas mensuales por producto · {cat_det}"),
                        width='stretch')
    else:
        prod_det = st.selectbox("Producto", plan["producto"].tolist())
        fila = plan[plan["producto"] == prod_det].iloc[0]
        hist = largo[largo["producto"] == prod_det]
        st.plotly_chart(charts.detalle_producto(hist, fila), width='stretch')

# ------------------------------------------------------------------
# Pestaña 3: plan operativo de compras
# ------------------------------------------------------------------
with tab3:
    st.subheader("Plan operativo de compras y alertas de inventario")
    st.caption("Ingresa la existencia real en bodega de cada producto para calcular las compras.")
    with st.expander("📦 Existencias en bodega (simulador por producto)", expanded=True):
        cols = st.columns(len(plan))
        existencias = {}
        for col, (_, fila) in zip(cols, plan.iterrows()):
            existencias[fila["id_producto"]] = col.number_input(
                fila["producto"], min_value=0, max_value=60,
                value=int(fila["existencia_inicial"]), key=f"exist_{fila['id_producto']}")

    compras = fc.plan_de_compras(plan, existencias, presupuesto)
    icono = {"PEDIR": "🔴 PEDIR", "VIGILAR": "🟡 VIGILAR", "SUFICIENTE": "🟢 SUFICIENTE"}
    tabla = pd.DataFrame({
        "Producto": compras["producto"], "Stock objetivo": compras["stock_objetivo"],
        "Punto de reorden": compras["punto_reorden"], "Existencia": compras["existencia"],
        "Estado": compras["estado"].map(icono), "Comprar (un.)": compras["a_comprar"],
        "Sin cubrir (un.)": compras["sin_cubrir"], "Inversión (COP)": compras["inversion_compra"],
        "Proveedor": compras["proveedor"],
    })
    st.dataframe(tabla.style.format({"Inversión (COP)": "${:,.0f}"}),
                 width='stretch', hide_index=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Unidades a pedir", f"{int(compras['a_comprar'].sum())}")
    m2.metric("Inversión del pedido", f"${compras['inversion_compra'].sum():,.0f}")
    m3.metric("Productos en PEDIR", f"{(compras['estado'] == 'PEDIR').sum()} de {len(compras)}")
    m4.metric("Unidades sin cubrir por presupuesto", f"{int(compras['sin_cubrir'].sum())}")

    if presupuesto is not None:
        st.info(f"Presupuesto de ${presupuesto:,.0f}: se prioriza lo que está en PEDIR y, dentro de eso, "
                "lo que más utilidad deja por peso invertido.")
    sin_prov = compras[compras["proveedor"] == PROVEEDOR_SIN_REGISTRO]["producto"].tolist()
    if sin_prov:
        st.warning(f"⚠️ {len(sin_prov)} productos no tienen proveedor registrado: {', '.join(sin_prov)}. "
                   f"Se sugiere formalizar la cadena de suministro (por ejemplo, con {PROVEEDOR_SUGERIDO}).")

st.markdown("---")
st.caption("Universidad de Cundinamarca · Facultad de Ingeniería · Business Analytics 2026")
