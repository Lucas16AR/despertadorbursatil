"""Cliente de argentinadatos.com — inflación mensual e interanual (INDEC).

Mismo patrón que `riesgo_pais.py`: fuente gratuita, sin API key."""
from __future__ import annotations

import requests

INFLACION_URL = "https://api.argentinadatos.com/v1/finanzas/indices/inflacion"
# El CLAUDE.md original documentaba "inflacion-interanual" (con guiones) — devuelve 404. El
# endpoint real, confirmado con curl (2026-07-22), es camelCase.
INFLACION_INTERANUAL_URL = "https://api.argentinadatos.com/v1/finanzas/indices/inflacionInteranual"


def _ultimo_punto(url: str) -> dict | None:
    """Cada serie se resuelve por separado y no bloqueante: si una de las dos falla, la otra
    igual se puede mostrar en el mensaje."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        serie = response.json()
    except Exception as error:
        print(f"No se pudo obtener {url} (no bloqueante): {error}")
        return None
    if not serie:
        return None
    ultimo = serie[-1]
    valor = ultimo.get("valor")
    if not isinstance(valor, (int, float)):
        return None
    return {"valor": valor, "fecha_origen": ultimo.get("fecha")}


def fetch_inflacion() -> dict | None:
    """Devuelve {"mensual": {...} | None, "interanual": {...} | None} con el último punto de
    cada serie, o None si ninguna de las dos trajo datos. Es un dato mensual (INDEC publica con
    1-2 semanas de rezago): no se compara contra la tanda anterior como el resto de los campos,
    sólo se muestra el último valor conocido con su fecha de referencia."""
    mensual = _ultimo_punto(INFLACION_URL)
    interanual = _ultimo_punto(INFLACION_INTERANUAL_URL)
    if mensual is None and interanual is None:
        return None
    return {"mensual": mensual, "interanual": interanual}
