"""Resumen macro del día vía Claude API (Haiku): sintetiza los titulares de las
últimas 24hs + los datos duros ya calculados (dólar, MERVAL, brecha). Sin
instrucciones de inversión, coherente con no tener sección de recomendaciones."""
from __future__ import annotations

import html

import anthropic

from agrupador import agrupar_titulares

MODEL = "claude-haiku-4-5"

# Cuántos grupos de titulares (ya deduplicados y ordenados por relevancia) se le pasan a Claude.
# Acota el costo de tokens con muchas fuentes sin perder lo importante: los más cubiertos van
# primero.
MAX_GRUPOS_PROMPT = 20

SYSTEM_PROMPT = (
    "Sos un analista que redacta un resumen macro diario para un reporte de "
    "mercados argentino. Con los titulares de noticias y los datos duros que te "
    "pasan, escribí una síntesis de 2 a 4 puntos (no fuerces 4 si con 2-3 alcanza), "
    "cada uno una idea o tema distinto, en español rioplatense, neutral y directo. "
    "Cada punto es UNA sola oración corta (máximo ~25 palabras) — nunca un párrafo "
    "ni varias oraciones — y va en su propia línea, empezando con '• '. No repitas "
    "entre puntos un dato que ya diste en otro. Nunca dés recomendaciones de "
    "inversión ni instrucciones de compra/venta de ningún instrumento — solo "
    "describí el contexto. Si los titulares no tienen nada relevante, basate solo "
    "en los datos duros. El objetivo es legibilidad, no recortar información: "
    "priorizá los datos/eventos más importantes del día, cada uno en una línea "
    "breve y concreta, en vez de desarrollarlos en extenso."
)


def _armar_prompt(
    titulares: list[dict],
    dolares: dict,
    merval: dict | None,
    brecha_mep_oficial: float | None,
    enfoque: str | None = None,
    riesgo_pais: dict | None = None,
    inflacion: dict | None = None,
) -> str:
    lineas = []
    if enfoque:
        lineas.append(enfoque)
        lineas.append("")
    if brecha_mep_oficial is not None:
        lineas.append(f"Brecha MEP/oficial: {brecha_mep_oficial:.1f}%")
    for casa, info in dolares.items():
        lineas.append(f"Dólar {info['nombre']}: venta ${info['venta']:.0f}")
    if merval is not None:
        lineas.append(f"MERVAL: {merval['valor']:.0f} ({merval['variacion_pct']:+.1f}%)")
    if riesgo_pais is not None:
        lineas.append(
            f"Riesgo país: {riesgo_pais['valor']:.0f} pts ({riesgo_pais['variacion_pct']:+.1f}%)"
        )
    if inflacion is not None:
        mensual = inflacion.get("mensual")
        interanual = inflacion.get("interanual")
        partes = []
        if mensual is not None:
            partes.append(f"{mensual['valor']:.1f}% mensual")
        if interanual is not None:
            partes.append(f"{interanual['valor']:.1f}% interanual")
        if partes:
            lineas.append(f"Inflación: {' / '.join(partes)}")

    lineas.append("")
    grupos = agrupar_titulares(titulares)
    if grupos:
        lineas.append(
            "Titulares de las últimas 24hs, agrupados por evento y ordenados por relevancia. "
            "Entre corchetes va cuántos medios distintos cubren cada evento: cuantos más medios, "
            "más importante — priorizá esos al escribir el resumen."
        )
        for g in grupos[:MAX_GRUPOS_PROMPT]:
            n = g["n_fuentes"]
            etiqueta = f"{n} fuentes" if n > 1 else "1 fuente"
            lineas.append(f"- [{etiqueta}] {g['titulo']} ({', '.join(g['fuentes'])})")
    else:
        lineas.append("(sin titulares relevantes)")

    return "\n".join(lineas)


def generar_resumen_macro(
    titulares: list[dict],
    dolares: dict,
    merval: dict | None,
    brecha_mep_oficial: float | None,
    enfoque: str | None = None,
    riesgo_pais: dict | None = None,
    inflacion: dict | None = None,
) -> str | None:
    """Devuelve el resumen en bullets cortos (2-4 líneas), o None si falla la llamada a la API.
    `enfoque` es la instrucción del momento del día (pre-apertura, cierre, etc.) para
    que el resumen sea coherente con la tanda y no repita el mismo texto genérico."""
    client = anthropic.Anthropic()
    prompt = _armar_prompt(
        titulares, dolares, merval, brecha_mep_oficial, enfoque, riesgo_pais, inflacion
    )
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as error:
        print(f"Claude API falló al generar el resumen macro: {error}")
        return None
    texto = next((block.text for block in response.content if block.type == "text"), None)
    if texto is None:
        return None
    # El mensaje se manda con parse_mode=HTML: si algún titular trae '<', '>' o '&' y Claude lo
    # reproduce tal cual, rompería el parseo de Telegram y tiraría abajo el envío entero. Se
    # escapa acá, antes de insertar el texto en el mensaje armado por formatter.py. quote=False:
    # Telegram sólo exige escapar '&', '<' y '>' en el texto — escapar comillas de más (ej.
    # "Moody's" -> "Moody&#x27;s") ensucia el mensaje sin necesidad.
    return html.escape(texto.strip(), quote=False)
