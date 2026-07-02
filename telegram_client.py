"""Cliente mínimo de la Telegram Bot API."""
import os

import requests


def enviar_mensaje(texto: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = requests.post(
        url,
        json={"chat_id": chat_id, "text": texto, "parse_mode": "HTML"},
        timeout=10,
    )
    response.raise_for_status()
