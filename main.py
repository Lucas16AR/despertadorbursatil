"""Punto de entrada: pega a dolarapi.com + estadisticasbcra.com, arma el
mensaje del día y lo manda al bot de Telegram."""
from dotenv import load_dotenv

import snapshot
from bcra import fetch_merval
from dolar import fetch_dolares
from formatter import armar_mensaje, calcular_brecha_mep_oficial
from telegram_client import enviar_mensaje


def main() -> None:
    load_dotenv()

    dolares = fetch_dolares()
    merval = fetch_merval()
    snapshot_anterior = snapshot.load_previous()

    mensaje = armar_mensaje(dolares, merval, snapshot_anterior)
    enviar_mensaje(mensaje)

    snapshot.save_current(
        {
            "dolares": dolares,
            "brecha_mep_oficial": calcular_brecha_mep_oficial(dolares),
        }
    )


if __name__ == "__main__":
    main()
