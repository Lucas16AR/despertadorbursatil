"""Registro de cada envío en Supabase (tabla `envios`), para el panel de administración.

No bloqueante por diseño: se llama después de que el reporte ya se mandó, y si falla (o si
Supabase no está configurado) sólo se loguea, nunca frena el pipeline. Escribe vía PostgREST
con la service_role key del lado servidor — no suma dependencias (reusa `requests`)."""
from __future__ import annotations

import json
import os

import requests


def registrar_envio(
    mensaje: str,
    datos: dict,
    anomalias: list,
    estado: str = "ok",
    canal: str = "telegram",
    error: str | None = None,
) -> None:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Supabase no configurado (SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY) — se omite el registro.")
        return

    response = requests.post(
        f"{url}/rest/v1/envios",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        data=json.dumps(
            {
                "canal": canal,
                "estado": estado,
                "mensaje": mensaje,
                "datos": datos,
                "anomalias": anomalias,
                "error": error,
            }
        ),
        timeout=10,
    )
    response.raise_for_status()
