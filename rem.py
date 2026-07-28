"""Cliente de argentinadatos.com — REM (Relevamiento de Expectativas de Mercado, BCRA).

Mismo patrón que `riesgo_pais.py`/`inflacion.py`: fuente gratuita, sin API key. A diferencia
del resto de los datos del canal, es un dato PROSPECTIVO (lo que el mercado espera que pase),
no un valor medido — se marca explícitamente como expectativa en el mensaje."""
from __future__ import annotations

import requests

REM_URL = "https://api.argentinadatos.com/v1/finanzas/rem/ultimo"

# El endpoint devuelve decenas de indicadores (desocupación, PBI, tipo de cambio, etc.) en una
# lista plana — se filtra por este indicador puntual, mismo criterio de "confirmar con curl
# antes de codear" que ya destapó el bug de inflacionInteranual en la Decimocuarta tarea.
INDICADOR_INFLACION = "Precios minoristas (IPC nivel general-Nacional; INDEC)"


def fetch_rem() -> dict | None:
    """Devuelve {"valor", "fecha_origen"} con la expectativa de inflación interanual a
    próximos 12 meses (mediana de "todos" los participantes, no sólo el top 10), o None si la
    fuente falla o no trae ese punto. Es un dato mensual (el BCRA publica el REM una vez por
    mes) — no bloqueante, mismo criterio que `inflacion.py`."""
    try:
        response = requests.get(REM_URL, timeout=10)
        response.raise_for_status()
        registros = response.json()
    except Exception as error:
        print(f"No se pudo obtener el REM (no bloqueante): {error}")
        return None
    punto = next(
        (
            r
            for r in registros
            if r.get("indicador") == INDICADOR_INFLACION
            and r.get("periodoTipo") == "proximos_12_meses"
            and r.get("muestra") == "todos"
        ),
        None,
    )
    if punto is None:
        return None
    valor = punto.get("mediana")
    if not isinstance(valor, (int, float)):
        return None
    return {"valor": valor, "fecha_origen": punto.get("fecha")}
