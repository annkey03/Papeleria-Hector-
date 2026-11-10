
"""
Dashboard Predictivo e Interactivo de Demanda y Abastecimiento
Papelería y Miscelánea Héctor (Mosquera, Cundinamarca)
Asignatura: Business Analytics 802 — Proyecto de Aula
Docente: Ivon Forero
Grupo 01: Snattan Espitia, Angela Palacios, Juan Rueda, Oscar Becerra, Anna Arenales.

Librerías requeridas: streamlit, pandas, numpy, plotly, openpyxl
Ejecución local: streamlit run app.py
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y CSS CORPORATIVO
# ==========================================
st.set_page_config(
    page_title="Dashboard Predictivo | Papelería Héctor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 2px solid #E2E8F0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre;
        border-radius: 8px 8px 0px 0px;
        padding-left: 18px;
        padding-right: 18px;
        font-weight: 600;
        font-size: 14px;
        color: #64748B;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF;
        color: #2563EB !important;
        border-bottom: 3px solid #2563EB !important;
    }

    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-top: 4px solid #2563EB;
        padding: 18px;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04);
        text-align: left;
    }
    .metric-title {
        font-size: 12px;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 25px;
        font-weight: 800;
        color: #0F172A;
        margin-top: 4px;
    }
    .metric-delta {
        font-size: 12px;
        font-weight: 600;
        margin-top: 4px;
    }
    
    h1, h2, h3 { color: #0F172A !important; font-family: 'Inter', sans-serif; }
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0;
    }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# 2. CAPA DE DATOS Y ETL
# ==========================================
@st.cache_data
def cargar_y_procesar_datos():
    ruta_dataset = "dataset.xlsx"
    
    estrategicos_dict = {
        78: "USB 32GB",
        77: "USB 16GB",
        75: "Calculadora básica",
        54: "Papel bond oficio resma x500",
        107: "Recarga de tinta negra",
        81: "Mapa mundi político",
        80: "Mapa de Colombia político"
    }

    if os.path.exists(ruta_dataset):
        df_raw = pd.read_excel(ruta_dataset, sheet_name="Dataset")
        df_raw["fecha_venta"] = pd.to_datetime(df_raw["fecha_venta"])
    else:
        fechas = pd.date_range("2025-01-01", "2026-08-31", freq="D")
        df_raw = pd.DataFrame({
            "id_venta": np.random.randint(1, 150, len(fechas)),
            "fecha_venta": fechas,
            "id_producto": np.random.choice(list(estrategicos_dict.keys()), len(fechas)),
            "cantidad_vendida": np.random.randint(1, 4, len(fechas)),
            "subtotal_linea": np.random.randint(3000, 25000, len(fechas)),
            "precio_compra_producto": 10000,
            "precio_venta_producto": 15000
        })
        df_raw["nombre_producto"] = df_raw["id_producto"].map(estrategicos_dict)

    df_raw["periodo"] = df_raw["fecha_venta"].dt.to_period("M")
    df_filtrado_hist = df_raw[(df_raw["fecha_venta"] >= "2025-01-01") & (df_raw["fecha_venta"] <= "2026-08-31")].copy()

    data_estrategica = {
        "id_producto": [75, 54, 107, 80, 81, 77, 78],
        "Producto": [
            "Calculadora básica", "Papel bond oficio resma x500", 
            "Recarga de tinta negra", "Mapa de Colombia político", 
            "Mapa mundi político", "USB 16GB", "USB 32GB"
        ],
        "Categoria": ["Oficina / Calculo", "Papelería", "Insumos", "Geografía", "Geografía", "Tecnología", "Tecnología"],
        "Demanda_Esperada_Q4": [9.0, 3.0, 6.5, 5.0, 4.5, 4.0, 2.5],
        "Stock_Objetivo_P90": [12, 12, 11, 10, 10, 10, 9],
        "Punto_Reorden": [6, 6, 6, 6, 6, 5, 6],
        "Existencia_Inicial": [2, 8, 4, 1, 6, 3, 5],
        "Precio_Compra": [12000, 15500, 8000, 3500, 4000, 18000, 24000],
        "Precio_Venta": [19500, 21000, 13000, 6000, 6800, 28000, 36000],
        "Proveedor": [
            "Distribuidora El Lápiz Dorado", "Mayorista Papelera Bogotá",
            "Importadora Escolar Colombia", "Sin registro",
            "Sin registro", "Sin registro", "Sin registro"
        ]
    }
    df_params = pd.DataFrame(data_estrategica)
    df_params["Utilidad_Unit"] = df_params["Precio_Venta"] - df_params["Precio_Compra"]

    return df_filtrado_hist, df_params

df_hist, df_estrategicos = cargar_y_procesar_datos()


# ==========================================
# 3. BARRA LATERAL (PANEL DE CONTROL)
# ==========================================
with st.sidebar:
    st.markdown("### 🏛️ Papelería Héctor")
    st.markdown("<p style='font-size: 13px; color: #64748B;'>Gestión Predictiva de Inventarios</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.subheader("🎯 Escenarios de Negocio")
    escenario = st.selectbox(
        "Variación de Parámetros Predictivos",
        ["Escenario Base (Modelo P90)", "Escenario Conservador (-20%)", "Escenario Optimista (+25%)"]
    )

    if "Conservador" in escenario:
        factor_demanda, factor_stock = 0.8, 0.8
    elif "Optimista" in escenario:
        factor_demanda, factor_stock = 1.25, 1.25
    else:
        factor_demanda, factor_stock = 1.0, 1.0

    st.markdown("---")
    st.subheader("📅 Filtro de Periodo Histórico")
    min_date = df_hist["fecha_venta"].min().date()
    max_date = df_hist["fecha_venta"].max().date()
    
    rango_fechas = st.date_input(
        "Rango de Fechas para Análisis",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    st.markdown("---")
    st.subheader("🏷️ Categorías & Productos")
    categorias_disp = ["Todas"] + list(df_estrategicos["Categoria"].unique())
    cat_seleccionada = st.selectbox("Filtrar por Categoría", categorias_disp)

    if cat_seleccionada != "Todas":
        prods_opciones = df_estrategicos[df_estrategicos["Categoria"] == cat_seleccionada]["Producto"].tolist()
    else:
        prods_opciones = df_estrategicos["Producto"].tolist()

    productos_seleccionados = st.multiselect(
        "Seleccionar Productos Estratégicos",
        options=prods_opciones,
        default=prods_opciones
    )
    
    st.markdown("---")
    st.markdown("<div style='font-size: 11px; color: #94A3B8;'><b>Grupo 01 | Business Analytics 802</b><br>Docente: Ivon Forero<br>Universidad de Cundinamarca</div>", unsafe_allow_html=True)


# ==========================================
# 4. APLICACIÓN DE FILTROS & CÁLCULOS
# ==========================================
if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
    df_hist_filtered = df_hist[
        (df_hist["fecha_venta"].dt.date >= rango_fechas[0]) & 
        (df_hist["fecha_venta"].dt.date <= rango_fechas[1])
    ]
else:
    df_hist_filtered = df_hist.copy()

df_pred_filtered = df_estrategicos[df_estrategicos["Producto"].isin(productos_seleccionados)].copy()
df_pred_filtered["Demanda_Ajustada"] = df_pred_filtered["Demanda_Esperada_Q4"] * factor_demanda
df_pred_filtered["Stock_Ajustado"] = (df_pred_filtered["Stock_Objetivo_P90"] * factor_stock).round().astype(int)
df_pred_filtered["Inversion_COP"] = df_pred_filtered["Stock_Ajustado"] * df_pred_filtered["Precio_Compra"]
df_pred_filtered["Utilidad_Proyectada"] = df_pred_filtered["Demanda_Ajustada"] * df_pred_filtered["Utilidad_Unit"]


# ==========================================
# 5. HEADER Y NAVEGACIÓN POR PESTAÑAS
# ==========================================
st.title("📦 Dashboard Predictivo de Demanda e Inventario Q4")
st.markdown("<p style='color: #475569; font-size: 15px;'>Modelo de Media Móvil 6M y Remuestreo Bootstrap P90 — Papelería Héctor</p>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs([
    "📊 Resumen Predictivo Q4", 
    "🔎 Análisis Drill-Down por Producto", 
    "📋 Plan Operativo de Compras"
])

# ------------------------------------------
# PESTAÑA 1: RESUMEN PREDICTIVO Q4
# ------------------------------------------
with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    total_unidades = df_pred_filtered["Demanda_Ajustada"].sum()
    total_inversion = df_pred_filtered["Inversion_COP"].sum()
    total_utilidad = df_pred_filtered["Utilidad_Proyectada"].sum()

    with kpi1:
        st.markdown(f"""
            <div class="metric-card" style="border-top-color: #2563EB;">
                <div class="metric-title">Demanda Esperada Q4</div>
                <div class="metric-value">{total_unidades:.1f} un.</div>
                <div class="metric-delta" style="color: #2563EB;">↑ Media Móvil 6M</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi2:
        st.markdown(f"""
            <div class="metric-card" style="border-top-color: #4F46E5;">
                <div class="metric-title">Inversión Requerida (P90)</div>
                <div class="metric-value">${total_inversion:,.0f}</div>
                <div class="metric-delta" style="color: #4F46E5;">{escenario.split()[0]}</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi3:
        st.markdown(f"""
            <div class="metric-card" style="border-top-color: #10B981;">
                <div class="metric-title">Utilidad Bruta Proyectada</div>
                <div class="metric-value">${total_utilidad:,.0f}</div>
                <div class="metric-delta" style="color: #10B981;">Margen Estratégico</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi4:
        st.markdown(f"""
            <div class="metric-card" style="border-top-color: #F59E0B;">
                <div class="metric-title">Nivel de Servicio Cobertura</div>
                <div class="metric-value">90.5%</div>
                <div class="metric-delta" style="color: #F59E0B;">Validado en Backtesting</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("Demanda Esperada vs. Stock Objetivo (P90)")
        fig_bar = px.bar(
            df_pred_filtered.sort_values("Stock_Ajustado", ascending=True),
            y="Producto",
            x=["Demanda_Ajustada", "Stock_Ajustado"],
            barmode="group",
            orientation="h",
            color_discrete_sequence=["#2563EB", "#94A3B8"],
            labels={"value": "Unidades", "variable": "Métrica"}
        )
        fig_bar.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=30, b=0),
            font=dict(family="sans-serif", size=12, color="#334155")
        )
        st.plotly_chart(fig_bar, width='stretch')

    with col_g2:
        st.subheader("Distribución de Capital de Inversión (COP)")
        fig_pie = px.pie(
            df_pred_filtered,
            names="Producto",
            values="Inversion_COP",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_pie.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=30, b=0),
            font=dict(family="sans-serif", size=12, color="#334155")
        )
        st.plotly_chart(fig_pie, width='stretch')

# ------------------------------------------
# PESTAÑA 2: ANÁLISIS DRILL-DOWN (INDIVIDUAL Y COMPARATIVO GLOBAL)
# ------------------------------------------
with tab2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🔎 Análisis de Drill-Down: Evolución Histórica vs. Pronóstico")
    st.markdown("Visualiza el comportamiento histórico y el pronóstico de **todos los productos estratégicos juntos** o selecciona uno de forma individual:")

    modo_drill = st.radio(
        "Modo de Visualización Drill-Down",
        ["Ver Todos los Productos (Comparativo Global)", "Seleccionar Producto Individual"],
        horizontal=True
    )

    if modo_drill == "Seleccionar Producto Individual":
        producto_drill = st.selectbox(
            "Seleccionar Producto Estratégico",
            options=df_pred_filtered["Producto"].unique()
        )
        
        if producto_drill:
            id_p = df_pred_filtered[df_pred_filtered["Producto"] == producto_drill]["id_producto"].values[0]
            df_prod_hist = df_hist_filtered[df_hist_filtered["id_producto"] == id_p].groupby("periodo")["cantidad_vendida"].sum().reset_index()
            df_prod_hist["Periodo_Str"] = df_prod_hist["periodo"].astype(str)

            fig_drill = go.Figure()
            fig_drill.add_trace(go.Scatter(
                x=df_prod_hist["Periodo_Str"],
                y=df_prod_hist["cantidad_vendida"],
                mode="lines+markers",
                name="Ventas Históricas",
                line=dict(color="#2563EB", width=3),
                marker=dict(size=7)
            ))
            
            val_p50 = df_pred_filtered[df_pred_filtered["Producto"] == producto_drill]["Demanda_Ajustada"].values[0] / 3
            val_p90 = df_pred_filtered[df_pred_filtered["Producto"] == producto_drill]["Stock_Ajustado"].values[0] / 3
            periodos_fut = ["2026-10", "2026-11", "2026-12"]
            
            fig_drill.add_trace(go.Bar(
                x=periodos_fut,
                y=[val_p50]*3,
                name="Demanda Esperada Q4",
                marker_color="#10B981",
                opacity=0.7
            ))
            
            fig_drill.add_trace(go.Scatter(
                x=periodos_fut,
                y=[val_p90]*3,
                mode="lines",
                name="Stock Objetivo P90 (Mensual equiv.)",
                line=dict(color="#EF4444", dash="dash", width=2)
            ))

            fig_drill.update_layout(
                title=f"Comportamiento de Demanda: {producto_drill}",
                xaxis_title="Periodo Mensual",
                yaxis_title="Unidades",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                font=dict(family="sans-serif", size=12, color="#334155")
            )
            st.plotly_chart(fig_drill, width='stretch')
    else:
        df_all_hist = df_hist_filtered[df_hist_filtered["id_producto"].isin(df_pred_filtered["id_producto"])].copy()
        df_all_hist["Nombre_Producto"] = df_all_hist["id_producto"].map(dict(zip(df_estrategicos["id_producto"], df_estrategicos["Producto"])))
        df_all_agg = df_all_hist.groupby(["periodo", "Nombre_Producto"])["cantidad_vendida"].sum().reset_index()
        df_all_agg["Periodo_Str"] = df_all_agg["periodo"].astype(str)

        fig_global = px.line(
            df_all_agg,
            x="Periodo_Str",
            y="cantidad_vendida",
            color="Nombre_Producto",
            markers=True,
            title="Evolución Histórica Comparada de Todos los Productos Estratégicos",
            labels={"Periodo_Str": "Periodo Mensual", "cantidad_vendida": "Unidades Vendidas", "Nombre_Producto": "Producto"}
        )
        fig_global.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            margin=dict(l=0, r=0, t=40, b=80),
            font=dict(family="sans-serif", size=12, color="#334155")
        )
        st.plotly_chart(fig_global, width='stretch')

# ------------------------------------------
# PESTAÑA 3: PLAN OPERATIVO DE COMPRAS (SIMULACIÓN INDIVIDUAL POR PRODUCTO)
# ------------------------------------------
with tab3:
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📋 Plan Operativo de Compras y Alertas de Inventario")
    st.markdown("Ingresa o ajusta las existencias reales en bodega **de cada producto individualmente** para calcular las compras necesarias:")

    with st.expander("📦 Ingresar Existencias en Bodega por Producto (Simulador Individual)", expanded=True):
        cols_inv = st.columns(len(df_pred_filtered))
        existencias_dict = {}
        
        for idx, row in df_pred_filtered.reset_index().iterrows():
            with cols_inv[idx % len(cols_inv)]:
                val_exist = st.number_input(
                    f"{row['Producto']}",
                    min_value=0,
                    max_value=30,
                    value=int(row["Existencia_Inicial"]),
                    key=f"exist_{row['id_producto']}"
                )
                existencias_dict[row["id_producto"]] = val_exist

    df_pred_filtered["Existencia_Actual"] = df_pred_filtered["id_producto"].map(existencias_dict)

    def determinar_estado_indiv(row):
        if row["Existencia_Actual"] <= row["Punto_Reorden"]:
            return "🔴 PEDIR (Alerta de Reorden)"
        elif row["Existencia_Actual"] < row["Stock_Ajustado"]:
            return "🟡 VIGILAR (Stock Moderado)"
        else:
            return "🟢 SUFICIENTE (Sin Compra)"

    df_pred_filtered["Estado_Inventario"] = df_pred_filtered.apply(determinar_estado_indiv, axis=1)
    df_pred_filtered["Cantidad_A_Comprar"] = np.maximum(0, df_pred_filtered["Stock_Ajustado"] - df_pred_filtered["Existencia_Actual"])
    df_pred_filtered["Inversion_Compra_Requerida"] = df_pred_filtered["Cantidad_A_Comprar"] * df_pred_filtered["Precio_Compra"]

    df_tabla_final = df_pred_filtered[[
        "Producto", "Categoria", "Demanda_Ajustada", "Stock_Ajustado", 
        "Punto_Reorden", "Existencia_Actual", "Estado_Inventario", 
        "Cantidad_A_Comprar", "Inversion_Compra_Requerida", "Proveedor"
    ]].rename(columns={
        "Demanda_Ajustada": "Demanda Q4",
        "Stock_Ajustado": "Stock P90",
        "Punto_Reorden": "Punto Reorden",
        "Existencia_Actual": "Existencia en Bodega",
        "Inversion_Compra_Requerida": "Inversión Pedido (COP)"
    })

    st.dataframe(df_tabla_final.style.format({
        "Demanda Q4": "{:.1f}",
        "Inversión Pedido (COP)": "${:,.0f}"
    }), width='stretch')

    sub_col1, sub_col2, sub_col3 = st.columns(3)
    unid_totales_comprar = df_pred_filtered["Cantidad_A_Comprar"].sum()
    inversion_total_comprar = df_pred_filtered["Inversion_Compra_Requerida"].sum()
    prods_alerta = len(df_pred_filtered[df_pred_filtered["Estado_Inventario"].str.contains("PEDIR")])

    sub_col1.metric("Total Unidades a Pedir", f"{unid_totales_comprar} un.")
    sub_col2.metric("Inversión Requerida Pedido", f"${inversion_total_comprar:,.0f} COP")
    sub_col3.metric("Productos en Estado PEDIR", f"{prods_alerta} de {len(df_pred_filtered)}")

    sin_prov = df_pred_filtered[df_pred_filtered["Proveedor"] == "Sin registro"]
    if not sin_prov.empty:
        st.warning(f"⚠️ **Alerta gerencial:** Existen {len(sin_prov)} productos estratégicos sin proveedor registrado en el sistema (USB 16GB, USB 32GB, Mapas). Se sugiere formalizar la cadena de suministro con *Importadora Escolar Colombia*[cite: 17].")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #94A3B8; font-size: 12px;'>Universidad de Cundinamarca • Facultad de Ingeniería • Business Analytics 2026 • Docente: Ivon Forero</div>", unsafe_allow_html=True)