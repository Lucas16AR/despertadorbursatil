"""Punto de entrada. Según el momento del día (que setea el workflow de Actions vía MOMENTO)
manda uno de dos tipos de mensaje al canal de Telegram:

- `datos`: el reporte de mercados (dólar + MERVAL + riesgo país + resumen macro con IA).
- `contenido`: un mensaje de valor agregado (lección educativa 12:00, efemérides 19:00)."""
import os
from datetime import datetime

from dotenv import load_dotenv

import snapshot
import supabase_log
from bcra import fetch_merval
from dolar import fetch_dolares
from efemerides import generar_efemerides
from formatter import ARG_TZ, armar_mensaje, calcular_brecha_mep_oficial, detectar_anomalias
from leccion_educativa import generar_leccion
from macro_summary import generar_resumen_macro
from momento import obtener_momento
from riesgo_pais import fetch_riesgo_pais
from rss_news import fetch_titulares
from telegram_client import enviar_mensaje


def _registrar(
    mensaje: str | None,
    datos: dict,
    anomalias: list,
    estado: str = "ok",
    error: str | None = None,
) -> None:
    """Registra la corrida en Supabase para el panel. No bloqueante: si falla, sólo se loguea."""
    try:
        supabase_log.registrar_envio(
            mensaje=mensaje, datos=datos, anomalias=anomalias, estado=estado, error=error
        )
    except Exception as err:
        print(f"No se pudo registrar el envío en Supabase (no bloqueante): {err}")


def enviar_reporte_datos(momento_cfg: dict) -> None:
    """Las 4 tandas de mercado: dólar + MERVAL + riesgo país + resumen macro."""
    dolares = fetch_dolares()
    snapshot_anterior = snapshot.load_previous()
    brecha_mep_oficial = calcular_brecha_mep_oficial(dolares)

    # MERVAL: no bloqueante — si estadisticasbcra.com falla (ya devolvió 403 alguna vez),
    # el reporte sale sin la línea de MERVAL en vez de no salir.
    merval = None
    try:
        merval = fetch_merval()
    except Exception as error:
        print(f"No se pudo obtener el MERVAL (no bloqueante): {error}")

    # Snapshot de inicio del día: se graba en la pre-apertura y lo usa la tanda de cierre para
    # mostrar la variación del día completo (además de la variación contra la tanda anterior).
    # Lleva la fecha (ART): si la pre-apertura de hoy falló, el archivo es de otro día y usarlo
    # daría una variación "del día" engañosa — en ese caso se omite.
    hoy_art = datetime.now(ARG_TZ).date().isoformat()
    snapshot_inicio_dia = None
    if momento_cfg["clave"] == "pre_apertura":
        snapshot.save_inicio_dia(
            {"fecha": hoy_art, "dolares": dolares, "brecha_mep_oficial": brecha_mep_oficial}
        )
    elif momento_cfg["clave"] == "cierre":
        inicio = snapshot.load_inicio_dia()
        if inicio is not None and inicio.get("fecha") == hoy_art:
            snapshot_inicio_dia = inicio
        elif inicio is not None:
            print("inicio_dia.json es de otro día — se omite la variación del día completo.")

    # Riesgo país: fuente aparte (argentinadatos.com), no bloqueante — si falla, el reporte sale igual.
    riesgo_pais = None
    try:
        riesgo_pais = fetch_riesgo_pais()
    except Exception as error:
        print(f"No se pudo obtener el riesgo país (no bloqueante): {error}")

    resumen_macro = None
    try:
        titulares = fetch_titulares()
        resumen_macro = generar_resumen_macro(
            titulares,
            dolares,
            merval,
            brecha_mep_oficial,
            enfoque=momento_cfg["enfoque_macro"],
            riesgo_pais=riesgo_pais,
        )
    except Exception as error:
        print(f"No se pudo generar el resumen macro (no bloqueante): {error}")

    mensaje = armar_mensaje(
        dolares,
        merval,
        snapshot_anterior,
        resumen_macro,
        momento=momento_cfg,
        riesgo_pais=riesgo_pais,
        snapshot_inicio_dia=snapshot_inicio_dia,
    )
    enviar_mensaje(mensaje)

    snapshot.save_current({"dolares": dolares, "brecha_mep_oficial": brecha_mep_oficial})

    _registrar(
        mensaje,
        datos={
            "momento": momento_cfg["titulo"],
            "dolares": dolares,
            "merval": merval,
            "riesgo_pais": riesgo_pais,
            "brecha_mep_oficial": brecha_mep_oficial,
        },
        anomalias=detectar_anomalias(dolares, merval),
    )


def enviar_mensaje_contenido(momento_cfg: dict) -> None:
    """Los mensajes de valor agregado (lección 12:00, efemérides 19:00). Si la generación falla,
    no se envía nada (el contenido ES el mensaje; no tiene sentido mandarlo vacío) — pero la
    corrida queda registrada como error para que el panel la muestre."""
    generadores = {
        "leccion_educativa": generar_leccion,
        "efemerides": generar_efemerides,
    }
    generar = generadores[momento_cfg["clave"]]
    mensaje = generar(momento_cfg)
    if not mensaje:
        print(f"No se pudo generar el contenido de '{momento_cfg['clave']}' — no se envía nada.")
        _registrar(
            None,
            datos={"momento": momento_cfg["titulo"]},
            anomalias=[],
            estado="error",
            error="la generación del contenido falló — no se envió el mensaje",
        )
        return
    enviar_mensaje(mensaje)
    _registrar(mensaje, datos={"momento": momento_cfg["titulo"]}, anomalias=[])


def main() -> None:
    load_dotenv()

    # El workflow de Actions setea MOMENTO según el cron que disparó la corrida; en local, default.
    momento_cfg = obtener_momento(os.getenv("MOMENTO"))
    print(f"Momento: {momento_cfg['titulo']} ({momento_cfg['tipo']})")

    try:
        if momento_cfg["tipo"] == "contenido":
            enviar_mensaje_contenido(momento_cfg)
        else:
            enviar_reporte_datos(momento_cfg)
    except Exception as error:
        # Deja la corrida fallida registrada para el panel y re-lanza para que Actions
        # marque el run en rojo (la visibilidad del fallo no cambia).
        _registrar(
            None,
            datos={"momento": momento_cfg["titulo"]},
            anomalias=[],
            estado="error",
            error=str(error),
        )
        raise


if __name__ == "__main__":
    main()
