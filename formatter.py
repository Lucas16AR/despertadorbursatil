"""Arma el mensaje del reporte diario: agrupado por categoría, con flechas de
variación y un destacado del día arriba."""
from __future__ import annotations

from datetime import date

FECHA_FORMATO = "%d/%m/%Y"

ORDEN_CASAS = ["oficial", "blue", "bolsa", "contadoconliqui"]


def _flecha(variacion_pct: float | None) -> str:
    if variacion_pct is None:
        return ""
    if variacion_pct > 0:
        return " 🟢▲"
    if variacion_pct < 0:
        return " 🔴▼"
    return " ➖"


def calcular_brecha_mep_oficial(dolares: dict) -> float:
    oficial = dolares["oficial"]["venta"]
    mep = dolares["bolsa"]["venta"]
    return (mep - oficial) / oficial * 100


def armar_mensaje(dolares: dict, merval: dict | None, snapshot_anterior: dict | None) -> str:
    hoy = snapshot_anterior or {}
    dolares_ayer = hoy.get("dolares", {})
    brecha_ayer = hoy.get("brecha_mep_oficial")

    brecha_hoy = calcular_brecha_mep_oficial(dolares)
    variacion_brecha = None
    if brecha_ayer is not None:
        variacion_brecha = brecha_hoy - brecha_ayer

    lineas = [
        f"📅 <b>Despertador Bursátil</b> — {date.today().strftime(FECHA_FORMATO)}",
        "",
        "🔥 <b>Destacado del día</b>",
        f"Brecha MEP/oficial: {brecha_hoy:.1f}%{_flecha(variacion_brecha)}",
        "",
        "💵 <b>Dólar</b>",
    ]

    for casa in ORDEN_CASAS:
        info = dolares.get(casa)
        if info is None:
            continue
        variacion = None
        ayer = dolares_ayer.get(casa)
        if ayer is not None:
            variacion = (info["venta"] - ayer["venta"]) / ayer["venta"] * 100
        lineas.append(
            f"{info['nombre']}: compra ${info['compra']:.0f} / venta ${info['venta']:.0f}{_flecha(variacion)}"
        )

    if merval is not None:
        lineas += [
            "",
            "📊 <b>Índices</b>",
            f"MERVAL: {merval['valor']:.0f}{_flecha(merval['variacion_pct'])} ({merval['variacion_pct']:+.1f}%)",
        ]

    lineas += [
        "",
        "<i>Fuente: dolarapi.com, estadisticasbcra.com. No es asesoramiento financiero.</i>",
    ]

    return "\n".join(lineas)
