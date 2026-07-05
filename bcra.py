"""Cliente de estadisticasbcra.com — MERVAL e indicadores BCRA."""
from __future__ import annotations

import os

import requests

BCRA_BASE_URL = "https://api.estadisticasbcra.com"


def _headers() -> dict:
    token = os.environ["BCRA_API_TOKEN"]
    return {"Authorization": f"BEARER {token}"}


def fetch_merval() -> dict | None:
    """Devuelve {"valor", "variacion_pct", "fecha_origen"} del último cierre de MERVAL, o
    None si no hay serie suficiente. `fecha_origen` es la fecha (YYYY-MM-DD) del último punto
    de la serie — permite detectar que la serie no avanzó (el tier gratis de
    estadisticasbcra.com sirve una serie que puede quedar congelada en el pasado)."""
    response = requests.get(f"{BCRA_BASE_URL}/merval", headers=_headers(), timeout=10)
    if not response.ok:
        print(f"estadisticasbcra.com respondió {response.status_code}: {response.text[:500]}")
    response.raise_for_status()
    serie = response.json()
    if len(serie) < 2:
        return None
    hoy, ayer = serie[-1], serie[-2]
    variacion_pct = (hoy["v"] - ayer["v"]) / ayer["v"] * 100
    return {"valor": hoy["v"], "variacion_pct": variacion_pct, "fecha_origen": hoy.get("d")}
