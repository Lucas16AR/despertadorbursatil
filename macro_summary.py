"""Resumen macro del día vía Claude API (Haiku): sintetiza los titulares de las
últimas 24hs + los datos duros ya calculados (dólar, MERVAL, brecha). Sin
instrucciones de inversión, coherente con no tener sección de recomendaciones."""
from __future__ import annotations

import anthropic

MODEL = "claude-haiku-4-5"

SYSTEM_PROMPT = (
    "Sos un analista que redacta un resumen macro diario para un reporte de "
    "mercados argentino. Con los titulares de noticias y los datos duros que te "
    "pasan, escribí una síntesis de 2 a 4 oraciones en español rioplatense, "
    "neutral y directa. Nunca dés recomendaciones de inversión ni instrucciones "
    "de compra/venta de ningún instrumento — solo describí el contexto. Si los "
    "titulares no tienen nada relevante, basate solo en los datos duros."
)


def _armar_prompt(titulares: list[dict], dolares: dict, merval: dict | None, brecha_mep_oficial: float) -> str:
    lineas = [f"Brecha MEP/oficial: {brecha_mep_oficial:.1f}%"]
    for casa, info in dolares.items():
        lineas.append(f"Dólar {info['nombre']}: venta ${info['venta']:.0f}")
    if merval is not None:
        lineas.append(f"MERVAL: {merval['valor']:.0f} ({merval['variacion_pct']:+.1f}%)")

    lineas.append("")
    lineas.append("Titulares de las últimas 24hs:")
    if titulares:
        for t in titulares:
            lineas.append(f"- [{t['fuente']}] {t['titulo']}")
    else:
        lineas.append("(sin titulares relevantes)")

    return "\n".join(lineas)


def generar_resumen_macro(
    titulares: list[dict], dolares: dict, merval: dict | None, brecha_mep_oficial: float
) -> str | None:
    """Devuelve el resumen de 2-4 oraciones, o None si falla la llamada a la API."""
    client = anthropic.Anthropic()
    prompt = _armar_prompt(titulares, dolares, merval, brecha_mep_oficial)
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
