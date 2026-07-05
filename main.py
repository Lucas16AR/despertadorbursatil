"""Punto de entrada: pega a dolarapi.com + estadisticasbcra.com, arma el
mensaje del día y lo manda al bot de Telegram."""
from dotenv import load_dotenv

import snapshot
import supabase_log
from bcra import fetch_merval
from dolar import fetch_dolares
from formatter import armar_mensaje, calcular_brecha_mep_oficial, detectar_anomalias
from macro_summary import generar_resumen_macro
from rss_news import fetch_titulares
from telegram_client import enviar_mensaje


def main() -> None:
    load_dotenv()

    dolares = fetch_dolares()
    merval = fetch_merval()
    snapshot_anterior = snapshot.load_previous()
    brecha_mep_oficial = calcular_brecha_mep_oficial(dolares)

    resumen_macro = None
    try:
        titulares = fetch_titulares()
        resumen_macro = generar_resumen_macro(titulares, dolares, merval, brecha_mep_oficial)
    except Exception as error:
        print(f"No se pudo generar el resumen macro (no bloqueante): {error}")

    mensaje = armar_mensaje(dolares, merval, snapshot_anterior, resumen_macro)
    enviar_mensaje(mensaje)

    snapshot.save_current(
        {
            "dolares": dolares,
            "brecha_mep_oficial": brecha_mep_oficial,
        }
    )

    # Registro del envío para el panel de administración (no bloqueante: el reporte ya salió).
    try:
        supabase_log.registrar_envio(
            mensaje=mensaje,
            datos={
                "dolares": dolares,
                "merval": merval,
                "brecha_mep_oficial": brecha_mep_oficial,
            },
            anomalias=detectar_anomalias(dolares, merval),
        )
    except Exception as error:
        print(f"No se pudo registrar el envío en Supabase (no bloqueante): {error}")


if __name__ == "__main__":
    main()
