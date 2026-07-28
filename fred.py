"""Cliente de FRED (Federal Reserve Economic Data, St. Louis Fed) — tasa de referencia de la
Fed. Requiere API key gratuita (`FRED_API_KEY`), alta inmediata — a diferencia de IOL, no es
un trámite largo.

Serie usada: DFEDTARU (Federal Funds Target Range - Upper Limit), diaria y sin lag — el valor
vigente el mismo día, no un promedio mensual retrasado como FEDFUNDS (la otra serie candidata,
descartada por publicarse con casi un mes de rezago)."""
from __future__ import annotations

import os

import requests

SERIES_ID = "DFEDTARU"
OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"


def fetch_fed_rate() -> dict | None:
    """Devuelve {"valor", "fecha_origen"} con la tasa techo del rango objetivo de la Fed
    vigente, o None si falta la key, la fuente falla o no hay datos. No bloqueante."""
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        return None
    try:
        response = requests.get(
            OBSERVATIONS_URL,
            params={
                "series_id": SERIES_ID,
                "api_key": api_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 10,
            },
            timeout=10,
        )
        response.raise_for_status()
        observaciones = response.json().get("observations", [])
    except Exception as error:
        print(f"No se pudo obtener la tasa de la Fed (no bloqueante): {error}")
        return None
    # FRED marca los días sin dato con el valor literal "." (fines de semana/feriados en
    # algunas series) — se descartan hasta encontrar el primer valor numérico real.
    for obs in observaciones:
        valor_texto = obs.get("value")
        if valor_texto in (None, "."):
            continue
        try:
            valor = float(valor_texto)
        except ValueError:
            continue
        return {"valor": valor, "fecha_origen": obs.get("date")}
    return None
