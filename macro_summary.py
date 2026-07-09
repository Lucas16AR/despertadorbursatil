"""Resumen macro del día vía Claude API (Haiku): sintetiza los titulares de las
últimas 24hs + los datos duros ya calculados (dólar, MERVAL, brecha). Sin
instrucciones de inversión, coherente con no tener sección de recomendaciones."""
from __future__ import annotations

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
    "pasan, escribí una síntesis de 2 a 4 oraciones en español rioplatense, "
    "neutral y directa. Nunca dés recomendaciones de inversión ni instrucciones "
    "de compra/venta de ningún instrumento — solo describí el contexto. Si los "
    "titulares no tienen nada relevante, basate solo en los datos duros."
)


def _armar_prompt(
    titulares: list[dict],
    dolares: dict,
    merval: dict | None,
    brecha_mep_oficial: float,
    enfoque: str | None = None,
) -> str:
    lineas = []
    if enfoque:
        lineas.append(enfoque)
        lineas.append("")
    lineas.append(f"Brecha MEP/oficial: {brecha_mep_oficial:.1f}%")
    for casa, info in dolares.items():
        lineas.append(f"Dólar {info['nombre']}: venta ${info['venta']:.0f}")
    if merval is not None:
        lineas.append(f"MERVAL: {merval['valor']:.0f} ({merval['variacion_pct']:+.1f}%)")

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
    brecha_mep_oficial: float,
    enfoque: str | None = None,
) -> str | None:
    """Devuelve el resumen de 2-4 oraciones, o None si falla la llamada a la API.
    `enfoque` es la instrucción del momento del día (pre-apertura, cierre, etc.) para
    que el resumen sea coherente con la tanda y no repita el mismo texto genérico."""
    client = anthropic.Anthropic()
    prompt = _armar_prompt(titulares, dolares, merval, brecha_mep_oficial, enfoque)
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
    return next((block.text for block in response.content if block.type == "text"), None)
