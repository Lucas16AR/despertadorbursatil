"""Arma el mensaje del reporte diario: agrupado por categoría, con flechas de
variación y un destacado del día arriba."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

FECHA_FORMATO = "%d/%m/%Y"

ORDEN_CASAS = ["oficial", "blue", "bolsa", "contadoconliqui", "cripto"]

# Argentina no aplica horario de verano: siempre UTC-3.
ARG_TZ = timezone(timedelta(hours=-3))


def _flecha(variacion_pct: float | None) -> str:
    if variacion_pct is None:
        return ""
    if variacion_pct > 0:
        return " 🟢▲"
    if variacion_pct < 0:
        return " 🔴▼"
    return " ➖"


def _fecha_origen_a_fecha(fecha_origen: str | None) -> date | None:
    """Convierte el `fecha_origen` que informa cada fuente a una fecha calendario de
    Argentina. Acepta ISO 8601 con hora y zona (dolarapi, ej. '2026-07-03T18:55:00.000Z')
    o sólo fecha (estadisticasbcra, ej. '2024-08-30'). Devuelve None si no se puede parsear."""
    if not fecha_origen:
        return None
    texto = fecha_origen.strip()
    if "T" not in texto:
        # Sólo fecha (YYYY-MM-DD), sin hora ni zona: se toma literal, sin convertir zona
        # horaria (hacerlo la correría un día hacia atrás al pasar de medianoche UTC a ART).
        try:
            return date.fromisoformat(texto[:10])
        except ValueError:
            return None
    try:
        dt = datetime.fromisoformat(texto.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ARG_TZ).date()


def _fecha_referencia(dolares: dict) -> date | None:
    """La fecha más nueva entre todas las cotizaciones del lote. Sirve de referencia de
    frescura: a las 8am (o un fin de semana) la fuente trae el cierre del día hábil anterior,
    así que comparar contra 'hoy' marcaría todo como viejo. Comparar cada valor contra el más
    fresco del propio lote detecta lo que realmente importa: un campo que quedó rezagado
    respecto de sus pares (ej. el oficial congelado, o el MERVAL de una serie que no avanza)."""
    fechas = [
        f for f in (_fecha_origen_a_fecha(info.get("fecha_origen")) for info in dolares.values())
        if f is not None
    ]
    return max(fechas) if fechas else None


def _sufijo_frescura(fecha_origen: str | None, referencia: date | None) -> str:
    """Devuelve '' si el dato está tan fresco como el más nuevo del lote (o no se conoce su
    fecha/referencia), o ' (al dd/mm)' si quedó rezagado. Incluye el año cuando el dato es de
    otro año, para que un valor muy viejo (ej. una serie congelada) no aparente ser reciente."""
    fecha = _fecha_origen_a_fecha(fecha_origen)
    if fecha is None or referencia is None or fecha >= referencia:
        return ""
    etiqueta = (
        fecha.strftime("%d/%m") if fecha.year == referencia.year else fecha.strftime("%d/%m/%Y")
    )
    return f" (al {etiqueta})"


def calcular_brecha_mep_oficial(dolares: dict) -> float:
    oficial = dolares["oficial"]["venta"]
    mep = dolares["bolsa"]["venta"]
    return (mep - oficial) / oficial * 100


def detectar_anomalias(dolares: dict, merval: dict | None) -> list[dict]:
    """Lista de campos cuyo dato quedó rezagado respecto del más fresco del lote (mismo
    criterio de frescura que usa el mensaje). Alimenta las alertas del panel de administración
    —ej. el dólar oficial congelado o el MERVAL de una serie que no avanza— sin tener que
    mirar los logs crudos."""
    referencia = _fecha_referencia(dolares)
    if referencia is None:
        return []

    anomalias = []
    candidatos = list(dolares.items())
    if merval is not None:
        candidatos.append(("merval", merval))

    for campo, info in candidatos:
        fecha = _fecha_origen_a_fecha(info.get("fecha_origen"))
        if fecha is not None and fecha < referencia:
            anomalias.append(
                {
                    "campo": campo,
                    "fecha_dato": fecha.isoformat(),
                    "motivo": "el dato es más viejo que el resto del lote (posible fuente congelada)",
                }
            )
    return anomalias


def armar_mensaje(
    dolares: dict,
    merval: dict | None,
    snapshot_anterior: dict | None,
    resumen_macro: str | None = None,
    momento: dict | None = None,
) -> str:
    referencia = _fecha_referencia(dolares)
    hoy = snapshot_anterior or {}
    dolares_ayer = hoy.get("dolares", {})
    brecha_ayer = hoy.get("brecha_mep_oficial")

    brecha_hoy = calcular_brecha_mep_oficial(dolares)
    variacion_brecha = None
    if brecha_ayer is not None:
        variacion_brecha = brecha_hoy - brecha_ayer

    # La fecha se toma en horario de Argentina, no del runner (que corre en UTC): la tanda
    # de las 22:30 ART arranca a las 01:30 UTC del día siguiente, y date.today() imprimiría
    # la fecha de mañana.
    fecha_hoy = datetime.now(ARG_TZ).date().strftime(FECHA_FORMATO)
    if momento:
        encabezado = [
            f"{momento['emoji']} <b>Despertador Bursátil · {momento['titulo']}</b> — {fecha_hoy}",
            f"<i>{momento['subtitulo']}</i>",
        ]
    else:
        encabezado = [f"📅 <b>Despertador Bursátil</b> — {fecha_hoy}"]

    lineas = [
        *encabezado,
        "",
        "🔥 <b>Destacado del día</b>",
        f"Brecha MEP/oficial: {brecha_hoy:.1f}%{_flecha(variacion_brecha)}",
        "",
        "💵 <b>Dólar</b>",
    ]

    for casa in ORDEN_CASAS:
        info = dolares.get(casa)
        if info is None:
            continue
        sufijo = _sufijo_frescura(info.get("fecha_origen"), referencia)
        variacion = None
        ayer = dolares_ayer.get(casa)
        # Sólo mostramos variación si el dato es de hoy: comparar un valor que la fuente no
        # actualizó contra el snapshot de ayer daría una flecha engañosa.
        if not sufijo and ayer is not None:
            variacion = (info["venta"] - ayer["venta"]) / ayer["venta"] * 100
        lineas.append(
            f"{info['nombre']}: compra ${info['compra']:.0f} / venta ${info['venta']:.0f}{sufijo}{_flecha(variacion)}"
        )

    if merval is not None:
        sufijo_merval = _sufijo_frescura(merval.get("fecha_origen"), referencia)
        if sufijo_merval:
            linea_merval = f"MERVAL: {merval['valor']:.0f}{sufijo_merval}"
        else:
            linea_merval = (
                f"MERVAL: {merval['valor']:.0f}{_flecha(merval['variacion_pct'])} "
                f"({merval['variacion_pct']:+.1f}%)"
            )
        lineas += ["", "📊 <b>Índices</b>", linea_merval]

    if resumen_macro:
        lineas += [
            "",
            "📰 <b>Contexto macro</b>",
            resumen_macro,
        ]

    lineas += [
        "",
        "<i>Fuente: dolarapi.com, estadisticasbcra.com.</i>",
        "",
        "<i>🤖 Alerta automatizada con fines puramente informativos y educativos. "
        "No constituye una recomendación de inversión, oferta de compra/venta ni "
        "asesoramiento bursátil. Operar bajo su propio riesgo.</i>",
    ]

    return "\n".join(lineas)
