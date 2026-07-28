"""Cliente del Banco Central de Brasil (SGS — Sistema Gerenciador de Séries Temporais) —
PTAX (real/dólar) y Selic. Fuente gratuita, sin API key.

El CLAUDE.md original especulaba que la API del BCB (vía Olinda/OData, la documentada en
Swagger) podía traer XML/OData en vez de JSON directo — no hizo falta: el SGS (`api.bcb.gov.br`)
es mucho más simple, devuelve JSON plano, mismo patrón de bajo esfuerzo que argentinadatos.com."""
from __future__ import annotations

from datetime import date, datetime

import requests

# Series del SGS: 1 = PTAX venda (real por dólar, diaria); 432 = meta Selic definida por el
# Copom (se pide una ventana de 15 días porque esta serie viene precargada con fechas futuras,
# ver `_ultimo_no_futuro`).
PTAX_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados/ultimos/5?formato=json"
SELIC_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/15?formato=json"


def _ultimo_no_futuro(registros: list[dict]) -> dict | None:
    """La serie de meta Selic viene con fechas futuras ya cargadas (el valor no cambia hasta
    la próxima reunión del Copom, así que el BCB precarga varios días adelante) — se descartan
    los puntos posteriores a hoy para no mostrar una fecha del futuro como `fecha_origen`."""
    hoy = date.today()
    candidatos = []
    for r in registros:
        try:
            fecha = datetime.strptime(r["data"], "%d/%m/%Y").date()
            valor = float(r["valor"])
        except (KeyError, ValueError, TypeError):
            continue
        if fecha <= hoy:
            candidatos.append((fecha, valor))
    if not candidatos:
        return None
    fecha, valor = max(candidatos, key=lambda item: item[0])
    return {"valor": valor, "fecha_origen": fecha.isoformat()}


def fetch_ptax() -> dict | None:
    """Devuelve {"valor", "fecha_origen"} con la última cotización PTAX venda (reales por
    dólar), o None si la fuente falla. No bloqueante."""
    try:
        response = requests.get(PTAX_URL, timeout=10)
        response.raise_for_status()
        registros = response.json()
    except Exception as error:
        print(f"No se pudo obtener la PTAX de Brasil (no bloqueante): {error}")
        return None
    if not registros:
        return None
    ultimo = registros[-1]
    try:
        fecha = datetime.strptime(ultimo["data"], "%d/%m/%Y").date()
        valor = float(ultimo["valor"])
    except (KeyError, ValueError, TypeError):
        return None
    return {"valor": valor, "fecha_origen": fecha.isoformat()}


def fetch_selic() -> dict | None:
    """Devuelve {"valor", "fecha_origen"} con la meta Selic vigente (% anual), o None si la
    fuente falla. No bloqueante."""
    try:
        response = requests.get(SELIC_URL, timeout=10)
        response.raise_for_status()
        registros = response.json()
    except Exception as error:
        print(f"No se pudo obtener la Selic de Brasil (no bloqueante): {error}")
        return None
    return _ultimo_no_futuro(registros)
