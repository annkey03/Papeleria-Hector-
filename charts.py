"""
Capa visual: construcción de las figuras Plotly del dashboard.

Cada función recibe DataFrames ya procesados y devuelve una figura; no lee
datos ni hace cálculos de negocio.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import (
    COLOR_ALERTA,
    COLOR_OK,
    COLOR_PRIMARIO,
    COLOR_SECUNDARIO,
    PERIODOS_PRONOSTICO,
)

FUENTE = dict(family="sans-serif", size=12, color="#334155")


def _estilo(fig: go.Figure, **kwargs) -> go.Figure:
    """Aplica el estilo común (fondo transparente, fuente y márgenes)."""
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=FUENTE,
        margin=dict(l=0, r=0, t=40, b=0),
        **kwargs,
    )
    return fig


def demanda_vs_stock(plan: pd.DataFrame) -> go.Figure:
    """Barras horizontales: demanda esperada Q4 frente al stock objetivo."""
    datos = plan.sort_values("stock_objetivo").rename(
        columns={"demanda_q4": "Ventas esperadas", "stock_objetivo": "Stock recomendado"}
    )
    fig = px.bar(
        datos, y="producto", x=["Ventas esperadas", "Stock recomendado"],
        barmode="group", orientation="h",
        color_discrete_sequence=[COLOR_PRIMARIO, COLOR_SECUNDARIO],
        labels={"value": "Unidades", "variable": "", "producto": ""},
    )
    return _estilo(fig, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))


def distribucion_inversion(plan: pd.DataFrame) -> go.Figure:
    """Dona con el dinero invertido en inventario por producto."""
    fig = px.pie(
        plan, names="producto", values="inversion_inventario", hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    return _estilo(fig)


def ventas_por_categoria(largo: pd.DataFrame) -> go.Figure:
    """Nivel 1 del drill-down: ventas mensuales apiladas por categoría."""
    agg = largo.groupby(["periodo", "categoria"], as_index=False)["unidades"].sum()
    fig = px.bar(
        agg, x="periodo", y="unidades", color="categoria",
        labels={"periodo": "Mes", "unidades": "Unidades vendidas", "categoria": "Categoría"},
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    return _estilo(fig, title="Ventas mensuales por categoría",
                   legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5))


def ventas_por_producto(largo: pd.DataFrame, titulo: str) -> go.Figure:
    """Nivel 2 del drill-down: líneas mensuales por producto."""
    fig = px.line(
        largo, x="periodo", y="unidades", color="producto", markers=True,
        labels={"periodo": "Mes", "unidades": "Unidades vendidas", "producto": "Producto"},
    )
    return _estilo(fig, title=titulo,
                   legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5))


def detalle_producto(historico: pd.DataFrame, fila: pd.Series) -> go.Figure:
    """Nivel 3 del drill-down: histórico del producto frente a su pronóstico Q4."""
    mensual_demanda = fila["demanda_q4"] / len(PERIODOS_PRONOSTICO)
    mensual_stock = fila["stock_objetivo"] / len(PERIODOS_PRONOSTICO)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=historico["periodo"], y=historico["unidades"], mode="lines+markers",
        name="Ventas históricas", line=dict(color=COLOR_PRIMARIO, width=3),
    ))
    fig.add_trace(go.Bar(
        x=PERIODOS_PRONOSTICO, y=[mensual_demanda] * len(PERIODOS_PRONOSTICO),
        name="Ventas esperadas (por mes)", marker_color=COLOR_OK, opacity=0.7,
    ))
    fig.add_trace(go.Scatter(
        x=PERIODOS_PRONOSTICO, y=[mensual_stock] * len(PERIODOS_PRONOSTICO), mode="lines",
        name="Stock recomendado (por mes)", line=dict(color=COLOR_ALERTA, dash="dash", width=2),
    ))
    return _estilo(
        fig, title=f"{fila['producto']}: ventas pasadas y pronóstico oct–dic",
        xaxis_title="Mes", yaxis_title="Unidades",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
