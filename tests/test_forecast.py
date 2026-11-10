"""Pruebas del motor predictivo. Ejecutar con:  pytest"""

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import data_loader as dl  # noqa: E402
import forecast as fc  # noqa: E402


@pytest.fixture(scope="module")
def datos():
    ventas = dl.cargar_ventas()
    catalogo = dl.construir_catalogo(ventas)
    mensual = dl.ventas_mensuales(ventas, dt.date(2025, 1, 1), dt.date(2026, 8, 31))
    return catalogo, mensual


def test_media_movil():
    assert fc.media_movil_trimestral(np.array([0, 0, 6, 6]), ventana=2) == 18.0


def test_escenario_base_reproduce_el_informe(datos):
    """El modelo debe dar los valores publicados en el informe del proyecto."""
    catalogo, mensual = datos
    plan = fc.calcular_plan(mensual, catalogo, factor=1.0, nivel=0.90, ventana=6)
    assert plan["demanda_q4"].round(1).tolist() == [9.0, 3.0, 6.5, 5.0, 4.5, 4.0, 2.5]
    assert plan["stock_objetivo"].tolist() == [12, 12, 11, 10, 10, 10, 9]
    assert plan["punto_reorden"].tolist() == [6, 6, 6, 6, 6, 5, 6]


def test_mayor_nivel_de_servicio_no_reduce_el_stock(datos):
    catalogo, mensual = datos
    p80 = fc.calcular_plan(mensual, catalogo, nivel=0.80)["stock_objetivo"].sum()
    p95 = fc.calcular_plan(mensual, catalogo, nivel=0.95)["stock_objetivo"].sum()
    assert p95 >= p80


def test_presupuesto_nunca_se_excede(datos):
    catalogo, mensual = datos
    plan = fc.calcular_plan(mensual, catalogo)
    existencias = dict(zip(plan["id_producto"], [0] * len(plan)))
    compras = fc.plan_de_compras(plan, existencias, presupuesto=300_000)
    assert compras["inversion_compra"].sum() <= 300_000
