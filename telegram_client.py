"""Cliente mínimo de la Telegram Bot API.

Nota de seguridad: la URL de la API lleva el bot token adentro. Ni `raise_for_status()` ni las
excepciones de red de `requests` se propagan tal cual, porque ambas incluyen la URL en su
mensaje y el token terminaría en los logs (el repo y sus logs de Actions son públicos; GitHub
enmascara los secrets registrados, pero mejor no depender solo de eso)."""
import os

import requests


def enviar_mensaje(texto: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        response = requests.post(
            url,
            json={"chat_id": chat_id, "text": texto, "parse_mode": "HTML"},
            timeout=10,
        )
    except requests.RequestException as error:
        # `from None`: el mensaje de la excepción original contiene la URL con el token.
        raise RuntimeError(
            f"No se pudo contactar a la API de Telegram: {type(error).__name__}"
        ) from None
    if not response.ok:
        # El cuerpo de error de Telegram no incluye el token; la URL sí — no se usa
        # raise_for_status() a propósito.
        raise RuntimeError(f"Telegram respondió {response.status_code}: {response.text[:300]}")
