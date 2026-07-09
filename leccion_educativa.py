"""Mensaje de la lección educativa diaria (12:00): un concepto de economía/finanzas explicado
simple. El tema rota por fecha (determinístico, sin repetir dentro del ciclo) y Claude Haiku lo
explica en 2-4 oraciones para principiantes, sin dar recomendaciones de inversión."""
from __future__ import annotations

from datetime import datetime

from formatter import ARG_TZ, encabezado
from ia import completar

# Conceptos generales (no atados a Argentina, como pidió Capi), pensados para que alguien sin
# formación financiera aprenda algo nuevo cada día. Rotan por día del año.
TEMAS = [
    "qué es la inflación y por qué suben los precios",
    "el interés compuesto y por qué se lo llama 'la octava maravilla del mundo'",
    "la diferencia entre ahorrar e invertir",
    "qué es un plazo fijo y cómo se calcula su rendimiento",
    "qué es la tasa de interés y quién la fija",
    "qué significa diversificar una inversión y por qué reduce el riesgo",
    "la relación entre riesgo y rendimiento",
    "qué es un bono y cómo le paga a quien lo compra",
    "qué es una acción y qué significa ser accionista de una empresa",
    "qué son los dividendos",
    "qué es la liquidez de una inversión",
    "qué mide el PBI de un país",
    "qué es el tipo de cambio y por qué se mueve",
    "qué son las reservas de un banco central",
    "qué es el riesgo país y qué refleja",
    "qué es un fondo común de inversión (FCI)",
    "qué es la volatilidad en los mercados",
    "la diferencia entre invertir y especular",
    "qué es un fondo de emergencia y por qué conviene tenerlo",
    "qué es la capitalización de mercado de una empresa",
    "qué es la deflación y por qué también puede ser un problema",
    "en qué se diferencia el interés simple del compuesto",
    "qué es la brecha cambiaria",
    "qué es una caución bursátil",
    "qué es el costo de oportunidad en las decisiones financieras",
]

SYSTEM_PROMPT = (
    "Sos un divulgador que enseña economía y finanzas a principiantes. Explicá el concepto que "
    "te pidan en 2 a 4 oraciones, en español rioplatense, claro y simple, con un ejemplo "
    "cotidiano si ayuda. No des recomendaciones de inversión ni instrucciones de compra/venta: "
    "es contenido educativo, no asesoramiento. No uses emojis ni títulos, solo el texto."
)


def _tema_del_dia(fecha) -> str:
    return TEMAS[fecha.timetuple().tm_yday % len(TEMAS)]


def generar_leccion(momento: dict) -> str | None:
    """Arma el mensaje de la lección del día, o None si falla la generación (para no enviar
    un mensaje vacío)."""
    fecha = datetime.now(ARG_TZ).date()
    tema = _tema_del_dia(fecha)
    texto = completar(SYSTEM_PROMPT, f"Explicá: {tema}.", max_tokens=350)
    if not texto:
        return None
    lineas = [
        *encabezado(momento),
        "",
        texto.strip(),
        "",
        "<i>🤖 Contenido educativo automatizado, con fines informativos.</i>",
    ]
    return "\n".join(lineas)
