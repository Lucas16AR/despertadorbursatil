"""Cliente de argentinadatos.com — riesgo país (EMBI+ Argentina).

Fuente gratuita, sin API key. La investigación original de fuentes había dejado el riesgo país
sin resolver por falta de API pública; este endpoint la cubre."""
from __future__ import annotations

import requests

RIESGO_PAIS_URL = "https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais"


def fetch_riesgo_pais() -> dict | None:
    """Devuelve {"valor", "variacion_pct", "fecha_origen"} del último dato de riesgo país, o
    None si no hay serie suficiente. La variación sale de la propia serie (últimos dos puntos),
    igual que el MERVAL. `fecha_origen` es la fecha (YYYY-MM-DD) del último punto: el riesgo país
    se publica por día hábil, así que suele venir con 1-2 días de lag respecto del dólar intradía
    y el mensaje lo marca con '(al dd/mm)'."""
    response = requests.get(RIESGO_PAIS_URL, timeout=10)
    response.raise_for_status()
    serie = response.json()
    if len(serie) < 2:
        return None
    hoy, ayer = serie[-1], serie[-2]
    variacion_pct = (hoy["valor"] - ayer["valor"]) / ayer["valor"] * 100
    return {
        "valor": hoy["valor"],
        "variacion_pct": variacion_pct,
        "fecha_origen": hoy.get("fecha"),
    }
