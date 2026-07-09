"""Helper mínimo sobre Claude API (Haiku), compartido por los generadores de contenido
(lección educativa, efemérides). Mismo modelo barato que el resumen macro; una sola llamada
por mensaje. Devuelve None si la llamada falla, para que el que llama decida no enviar."""
from __future__ import annotations

import anthropic

MODEL = "claude-haiku-4-5"


def completar(system: str, prompt: str, max_tokens: int = 400) -> str | None:
    """Una llamada a Claude Haiku. Devuelve el texto, o None si la API falla."""
    client = anthropic.Anthropic()
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as error:
        print(f"Claude API falló: {error}")
        return None
    return next((block.text for block in response.content if block.type == "text"), None)
