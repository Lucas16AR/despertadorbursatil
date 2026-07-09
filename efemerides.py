"""Mensaje de efemérides diario (19:00): una efeméride argentina (con énfasis) y una del mundo.

Los HECHOS salen de Wikipedia ('un día como hoy'), no de la memoria del modelo — así no se
inventan ni se equivocan fechas, que es el riesgo de generar efemérides con un LLM a secas.
Claude Haiku solo elige las más relevantes de esa lista real y las redacta en tono ameno."""
from __future__ import annotations

from datetime import datetime

import requests

from formatter import ARG_TZ, encabezado
from ia import completar

WIKI_URL = "https://es.wikipedia.org/api/rest_v1/feed/onthisday/events/{mes:02d}/{dia:02d}"

SYSTEM_PROMPT = (
    "Redactás la sección de efemérides de un canal argentino. Te paso una lista de hechos "
    "históricos reales ocurridos un día como hoy (sacados de Wikipedia). Elegí DOS: uno de "
    "Argentina (dale más protagonismo y ubicalo primero) y uno del resto del mundo. Escribí "
    "cada uno en 1 o 2 oraciones amenas, en español rioplatense, empezando por el año. NO "
    "inventes ni agregues datos que no estén en la lista; si un hecho no te cierra, elegí otro. "
    "Devolvé SOLO las dos efemérides, sin títulos ni introducción, separadas por una línea en blanco."
)


def _fetch_eventos(fecha) -> list[dict]:
    url = WIKI_URL.format(mes=fecha.month, dia=fecha.day)
    resp = requests.get(
        url, headers={"User-Agent": "DespertadorBursatil/1.0 (canal informativo)"}, timeout=15
    )
    resp.raise_for_status()
    return resp.json().get("events", [])


def _es_argentino(evento: dict) -> bool:
    if "Argentin" in evento.get("text", ""):
        return True
    return any("Argentin" in (p.get("title", "")) for p in evento.get("pages", []))


def _lista_para_prompt(eventos: list[dict], limite: int) -> list[str]:
    return [f"- {e.get('year')}: {e.get('text', '').strip()}" for e in eventos[:limite]]


def _armar_prompt(eventos: list[dict]) -> str:
    """Separa los hechos en argentinos y del resto del mundo y arma el texto para Claude."""
    argentinos = [e for e in eventos if _es_argentino(e)]
    mundiales = [e for e in eventos if not _es_argentino(e)]

    lineas = ["Hechos de Argentina un día como hoy:"]
    lineas += _lista_para_prompt(argentinos, 15) or ["(no hay hechos específicos de Argentina)"]
    lineas += ["", "Hechos del resto del mundo un día como hoy:"]
    lineas += _lista_para_prompt(mundiales, 20)
    if not argentinos:
        lineas += ["", "No hay hechos de Argentina hoy: elegí dos hechos del mundo."]
    return "\n".join(lineas)


def generar_efemerides(momento: dict) -> str | None:
    """Arma el mensaje de efemérides, o None si falla el fetch/generación (para no enviar vacío)."""
    fecha = datetime.now(ARG_TZ).date()
    try:
        eventos = _fetch_eventos(fecha)
    except Exception as error:
        print(f"No se pudieron traer efemérides de Wikipedia: {error}")
        return None
    if not eventos:
        return None

    texto = completar(SYSTEM_PROMPT, _armar_prompt(eventos), max_tokens=400)
    if not texto:
        return None
    lineas = [
        *encabezado(momento),
        "",
        texto.strip(),
        "",
        "<i>🤖 Efemérides automatizadas. Datos históricos vía Wikipedia.</i>",
    ]
    return "\n".join(lineas)
