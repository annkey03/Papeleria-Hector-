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
    COLOR_AVISO, COLOR_OK, COLOR_PRIMARIO, ESCENARIOS, FECHA_INICIO,
    PROVEEDOR_SIN_REGISTRO, PROVEEDOR_SUGERIDO,
)

st.set_page_config(page_title="Pronóstico de ventas | Papelería Héctor",
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
    st.caption("Control de inventario y pronóstico de ventas")
    st.markdown("---")

    st.subheader("🎯 Tipo de temporada")
    st.selectbox("Escenario", list(ESCENARIOS), key="escenario",
                 on_change=aplicar_escenario,
                 help="Carga valores sugeridos para cada tipo de temporada. Puedes ajustarlos después.")

    st.subheader("🔧 Ajustes del pronóstico")
    st.slider("Ritmo de ventas esperado", 0.5, 1.5, step=0.05, key="factor",
              help="0.8 = ventas bajas · 1.0 = igual que lo habitual · 1.25 = temporada alta")
    st.select_slider("Probabilidad de tener producto disponible", options=[0.80, 0.85, 0.90, 0.95, 0.99],
                     key="nivel", format_func=lambda x: f"{x:.0%}",
                     help="Qué tan seguro quieres estar de no quedarte sin producto. "
                          "A mayor porcentaje, más stock en bodega y más inversión.")
    st.selectbox("Meses de historia a considerar", [3, 6, 9, 12], key="ventana",
                 help="Cuántos de los últimos meses se usan para estimar las ventas futuras.")
    st.checkbox("Limitar presupuesto de compra", key="limitar")
    if st.session_state["limitar"]:
        st.slider("Presupuesto de compra (COP)", 100_000, 2_000_000, step=50_000, key="presupuesto")

    st.markdown("---")
    st.subheader("📅 Periodo de ventas a considerar")
    f_min = dt.date.fromisoformat(FECHA_INICIO)
    f_sugerida = dl.ultimo_mes_completo(ventas)
    f_max = max(ventas["fecha_venta"].max().date(), f_sugerida)
    rango = st.date_input("Rango de fechas", value=(f_min, f_sugerida), min_value=f_min, max_value=f_max,
                          help="Por defecto se usan meses completos. Si incluyes un mes a medias, "
                               "el promedio de ventas puede quedar más bajo de lo real.")

    st.subheader("🏷️ Categorías y productos")
    categoria = st.selectbox("Categoría", ["Todas"] + list(catalogo["categoria"].unique()))
    opciones = catalogo if categoria == "Todas" else catalogo[catalogo["categoria"] == categoria]
    seleccion = st.multiselect("Productos", opciones["producto"].tolist(),
                               default=opciones["producto"].tolist())
    st.markdown("---")
    with st.expander("ℹ️ Acerca de este tablero"):
        st.markdown(
            "**¿Cómo se calcula?** Se promedian las ventas de los últimos meses para estimar el trimestre "
            "y se simulan miles de trimestres posibles con tu historial para saber cuánto stock te "
            "cubre con la probabilidad elegida.\n\n"
            "Proyecto de aula · Business Analytics 802 · Universidad de Cundinamarca · Grupo 01 · "
            "Docente: Ivon Forero.")

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

st.title("📦 Pronóstico de ventas e inventario · Octubre–Diciembre 2026")
st.caption(f"Cuántas unidades se espera vender de cada producto y cuántas conviene tener en bodega "
           f"para cubrir la demanda con una probabilidad del {nivel:.0%}. "
           f"Basado en las ventas de los últimos {ventana} meses.")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Resumen del trimestre", "🔎 Detalle de ventas",
                                    "📋 Qué comprar", "📤 Cargar ventas"])


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
    k1.markdown(tarjeta("Ventas esperadas (oct–dic)", f"{plan['demanda_q4'].sum():.1f} un.",
                        f"Últimos {ventana} meses · ajuste ×{factor:.2f}", COLOR_PRIMARIO), unsafe_allow_html=True)
    k2.markdown(tarjeta("Inversión en inventario recomendado", f"${plan['inversion_inventario'].sum():,.0f}",
                        f"{plan['stock_objetivo'].sum()} unidades en bodega", "#4F46E5"), unsafe_allow_html=True)
    k3.markdown(tarjeta("Ganancia bruta estimada", f"${plan['utilidad_proyectada'].sum():,.0f}",
                        "Ventas esperadas × ganancia por unidad", COLOR_OK), unsafe_allow_html=True)
    k4.markdown(tarjeta("Aciertos en trimestres anteriores", f"{cob:.1%}",
                        f"Meta: {nivel:.0%} de los trimestres cubiertos", COLOR_AVISO), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Ventas esperadas vs. stock recomendado")
        st.plotly_chart(charts.demanda_vs_stock(plan), width='stretch')
    with c2:
        st.subheader("Dinero invertido en inventario, por producto")
        st.plotly_chart(charts.distribucion_inversion(plan), width='stretch')

    st.subheader("Pronóstico por producto")
    st.caption("**Stock recomendado**: unidades que conviene tener en bodega para el trimestre. "
               "**Pedir cuando queden**: si la existencia baja de esa cantidad, es momento de reponer.")
    st.dataframe(
        plan[["producto", "categoria", "demanda_q4", "stock_objetivo", "punto_reorden"]].rename(columns={
            "producto": "Producto", "categoria": "Categoría", "demanda_q4": "Ventas esperadas (un.)",
            "stock_objetivo": "Stock recomendado", "punto_reorden": "Pedir cuando queden (un.)"}
        ).style.format({"Ventas esperadas (un.)": "{:.1f}"}),
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
    st.subheader("Qué comprar y alertas de inventario")
    st.caption("Ingresa la existencia real en bodega de cada producto para calcular las compras.")
    with st.expander("📦 Inventario actual en bodega", expanded=True):
        cols = st.columns(len(plan))
        existencias = {}
        for col, (_, fila) in zip(cols, plan.iterrows()):
            existencias[fila["id_producto"]] = col.number_input(
                fila["producto"], min_value=0, max_value=60,
                value=int(fila["existencia_inicial"]), key=f"exist_{fila['id_producto']}")

    compras = fc.plan_de_compras(plan, existencias, presupuesto)
    icono = {"PEDIR": "🔴 PEDIR", "VIGILAR": "🟡 VIGILAR", "SUFICIENTE": "🟢 SUFICIENTE"}
    tabla = pd.DataFrame({
        "Producto": compras["producto"], "Stock recomendado": compras["stock_objetivo"],
        "Pedir cuando queden": compras["punto_reorden"], "Existencia": compras["existencia"],
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

# ------------------------------------------------------------------
# Pestaña 4: carga de ventas por el vendedor
# ------------------------------------------------------------------
with tab4:
    st.subheader("Cargar ventas nuevas")
    st.caption("Sube tus ventas recientes y el pronóstico se actualiza solo con la información más reciente.")
    if st.session_state.get("msg_carga"):
        st.success(st.session_state.pop("msg_carga"))

    st.markdown("**1. Descarga la plantilla** y escribe una fila por cada venta (fecha, producto y cantidad).")
    st.download_button("⬇️ Descargar plantilla de Excel", data=dl.plantilla_xlsx(catalogo),
                       file_name="plantilla_ventas.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.markdown("**2. Sube el archivo** con tus ventas (Excel o CSV).")
    subido = st.file_uploader("Archivo de ventas", type=["xlsx", "csv"], label_visibility="collapsed",
                              key=f"archivo_ventas_{st.session_state.get('n_cargas', 0)}")
    if subido is not None:
        contenido = subido.getvalue()
        lote = dl.huella(contenido)
        nuevas, errores, avisos = dl.validar_carga(contenido, subido.name, catalogo)
        for e in errores:
            st.error(e)
        for a in avisos:
            st.warning(a)
        if lote in set(dl.lotes_cargados()["lote"]):
            st.info("Este archivo ya se cargó antes; no se puede subir dos veces.")
        elif nuevas is not None and not errores:
            st.markdown(f"**3. Revisa y confirma:** {len(nuevas)} ventas · "
                        f"{int(nuevas['cantidad_vendida'].sum())} unidades · "
                        f"del {nuevas['fecha_venta'].min():%d/%m/%Y} al {nuevas['fecha_venta'].max():%d/%m/%Y}")
            st.dataframe(nuevas.rename(columns={"fecha_venta": "Fecha", "producto": "Producto",
                                                "cantidad_vendida": "Cantidad"})[["Fecha", "Producto", "Cantidad"]]
                         .style.format({"Fecha": "{:%d/%m/%Y}"}), width='stretch', hide_index=True)
            if st.button("✅ Confirmar y actualizar pronóstico", type="primary"):
                dl.guardar_carga(nuevas, catalogo, lote, subido.name)
                st.cache_data.clear()
                st.session_state["n_cargas"] = st.session_state.get("n_cargas", 0) + 1
                st.session_state["msg_carga"] = f"Se cargaron {len(nuevas)} ventas. El pronóstico ya está actualizado."
                st.rerun()

    historial = dl.lotes_cargados()
    if len(historial):
        st.markdown("---")
        st.markdown("**Cargas realizadas**")
        for _, fila in historial.iterrows():
            c_a, c_b = st.columns([4, 1])
            c_a.write(f"📄 {fila['archivo']} · {fila['filas']} ventas "
                      f"({fila['desde']:%d/%m/%Y} – {fila['hasta']:%d/%m/%Y}) · subido el {fila['cargado_en']}")
            if c_b.button("Deshacer", key=f"del_{fila['lote']}"):
                dl.eliminar_lote(fila["lote"])
                st.cache_data.clear()
                st.session_state["msg_carga"] = f"Se deshizo la carga de {fila['archivo']}."
                st.rerun()

st.markdown("---")
st.caption(f"Papelería y Miscelánea Héctor · Mosquera, Cundinamarca · "
           f"Ventas registradas hasta el {ventas['fecha_venta'].max():%d/%m/%Y}")
