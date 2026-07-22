"""Arma el mensaje del reporte diario: agrupado por categoría, con flechas de
variación y un destacado del día arriba."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

FECHA_FORMATO = "%d/%m/%Y"

ORDEN_CASAS = ["oficial", "blue", "bolsa", "contadoconliqui", "mayorista", "cripto", "tarjeta"]

MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

# Argentina no aplica horario de verano: siempre UTC-3.
ARG_TZ = timezone(timedelta(hours=-3))

# Disclaimer legal fijo (Tercera tarea): va al final de TODOS los mensajes del canal — los de
# datos y los de contenido (lección, efemérides) — por el riesgo regulatorio CNV y el riesgo de
# baneo en WhatsApp por contenido percibido como "señales de trading".
DISCLAIMER = (
    "<i>🤖 Alerta automatizada con fines puramente informativos y educativos. "
    "No constituye una recomendación de inversión, oferta de compra/venta ni "
    "asesoramiento bursátil. Operar bajo su propio riesgo.</i>"
)


def encabezado(momento: dict | None) -> list[str]:
    """Las líneas de título del mensaje (emoji + nombre + momento + fecha, y subtítulo).
    Compartido por el reporte de datos y los mensajes de contenido (lección, efemérides).
    La fecha se toma en horario de Argentina, no del runner (que corre en UTC): la tanda de
    las 22:30 ART arranca a las 01:30 UTC del día siguiente y date.today() daría mañana."""
    fecha_hoy = datetime.now(ARG_TZ).date().strftime(FECHA_FORMATO)
    if momento:
        return [
            f"{momento['emoji']} <b>Despertador Bursátil · {momento['titulo']}</b> — {fecha_hoy}",
            f"<i>{momento['subtitulo']}</i>",
        ]
    return [f"📅 <b>Despertador Bursátil</b> — {fecha_hoy}"]


def _flecha(variacion_pct: float | None) -> str:
    if variacion_pct is None:
        return ""
    if variacion_pct > 0:
        return " 🟢▲"
    if variacion_pct < 0:
        return " 🔴▼"
    return " ➖"


def _variacion_texto(variacion_pct: float | None) -> str:
    """Flecha + porcentaje entre paréntesis (ej. ' 🟢▲ (+0.5%)'), o '' si no hay variación.
    Capi pidió (2026-07-09) mostrar el número, no solo la flecha, en los campos de datos."""
    if variacion_pct is None:
        return ""
    return f"{_flecha(variacion_pct)} ({variacion_pct:+.1f}%)"


def _variacion_brecha_texto(variacion_pp: float | None) -> str:
    """Variación de la brecha en puntos porcentuales (pp), no en % — es la diferencia simple
    entre la brecha de hoy y la de la tanda anterior, no una variación relativa. Colores
    invertidos respecto de los precios: una brecha más ancha es desfavorable (▲ rojo) y una más
    angosta, favorable (▼ verde). Pedido de Capi (Décima tarea, 2026-07-09)."""
    if variacion_pp is None:
        return ""
    if variacion_pp > 0:
        flecha = " 🔴▲"
    elif variacion_pp < 0:
        flecha = " 🟢▼"
    else:
        flecha = " ➖"
    return f"{flecha} ({variacion_pp:+.1f}pp)"


def _precio_texto(valor: float) -> str:
    """2 decimales cuando la casa los tiene (dolarapi.com trae centavos en varias, ej. bolsa,
    cripto), sin decimales cuando el valor es entero — para no mostrar '1460.00' en el oficial."""
    if valor == int(valor):
        return f"{valor:.0f}"
    return f"{valor:.2f}"


def _miles(valor: float) -> str:
    """Separador de miles en formato argentino (punto), ej. 1714487 -> '1.714.487'."""
    return f"{valor:,.0f}".replace(",", ".")


def _fecha_origen_a_datetime(fecha_origen: str | None) -> datetime | None:
    """Como `_fecha_origen_a_fecha` pero conserva la hora, en horario de Argentina — la usa la
    leyenda de dolarapi.com para mostrar el momento exacto de la última actualización, no sólo
    el día. Sólo aplica a fechas con hora (ISO 8601 con 'T'); series de solo fecha no tienen hora
    que mostrar."""
    if not fecha_origen or "T" not in fecha_origen:
        return None
    try:
        dt = datetime.fromisoformat(fecha_origen.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ARG_TZ)


def _fecha_mes_anio(fecha_origen: str | None) -> str:
    """Formato 'mes año' en español (ej. 'mayo 2026'), para datos mensuales como la inflación
    donde mostrar dd/mm no tiene sentido — se referencia el mes que mide el dato, no un día."""
    fecha = _fecha_origen_a_fecha(fecha_origen)
    if fecha is None:
        return ""
    return f"{MESES_ES[fecha.month - 1]} {fecha.year}"


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


def calcular_brecha_mep_oficial(dolares: dict) -> float | None:
    """Devuelve None si falta alguna de las dos casas (fuente incompleta): el destacado se
    omite del mensaje en vez de que un KeyError tire abajo el envío completo."""
    oficial = dolares.get("oficial", {}).get("venta")
    mep = dolares.get("bolsa", {}).get("venta")
    if oficial is None or mep is None or oficial == 0:
        return None
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
    riesgo_pais: dict | None = None,
    snapshot_inicio_dia: dict | None = None,
    inflacion: dict | None = None,
    fuentes_noticias: list[str] | None = None,
) -> str:
    referencia = _fecha_referencia(dolares)
    hoy = snapshot_anterior or {}
    dolares_ayer = hoy.get("dolares", {})
    brecha_ayer = hoy.get("brecha_mep_oficial")
    # Datos de la primera tanda del día (pre-apertura): sólo llegan en la tanda de cierre, para
    # mostrar además la variación del día completo (no sólo contra la tanda anterior).
    dolares_inicio_dia = (snapshot_inicio_dia or {}).get("dolares", {})

    brecha_hoy = calcular_brecha_mep_oficial(dolares)
    variacion_brecha = None
    if brecha_hoy is not None and brecha_ayer is not None:
        variacion_brecha = brecha_hoy - brecha_ayer

    lineas = [*encabezado(momento), ""]
    # Sin brecha (fuente incompleta) se omite el destacado: el resto del reporte sale igual.
    if brecha_hoy is not None:
        lineas += [
            "🔥 <b>Destacado del día</b>",
            f"Brecha MEP/oficial: {brecha_hoy:.1f}%{_variacion_brecha_texto(variacion_brecha)}",
            "",
        ]
    lineas.append("💵 <b>Dólar</b>")

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
        # Variación del día completo (contra la pre-apertura): sólo en la tanda de cierre, que es
        # la única que recibe `snapshot_inicio_dia`. Va como segunda cifra, sin reemplazar la de
        # la tanda anterior.
        extra_dia = ""
        inicio = dolares_inicio_dia.get(casa)
        if not sufijo and inicio is not None:
            variacion_dia = (info["venta"] - inicio["venta"]) / inicio["venta"] * 100
            extra_dia = f" · día {variacion_dia:+.1f}%"
        lineas.append(
            f"{info['nombre']}: compra ${_precio_texto(info['compra'])} / venta ${_precio_texto(info['venta'])}{sufijo}{_variacion_texto(variacion)}{extra_dia}"
        )

    # Leyenda de frescura de dolarapi.com (Duodécima tarea): la fecha/hora más reciente entre
    # las 7 casas, tal como la muestra la propia dolarapi.com — referencia de esa fuente puntual,
    # aparte del pie de "Datos" que cierra todo el mensaje.
    ultima_actualizacion = None
    for info in dolares.values():
        dt = _fecha_origen_a_datetime(info.get("fecha_origen"))
        if dt is not None and (ultima_actualizacion is None or dt > ultima_actualizacion):
            ultima_actualizacion = dt
    if ultima_actualizacion is not None:
        lineas += [
            "<i>Datos obtenidos de DolarApi.com (https://dolarapi.com/)</i>",
            f"<i>Actualizado el {ultima_actualizacion.strftime('%d/%m/%Y')} a las "
            f"{ultima_actualizacion.strftime('%H:%M')}</i>",
        ]

    lineas_indices = []
    if merval is not None:
        sufijo_merval = _sufijo_frescura(merval.get("fecha_origen"), referencia)
        if sufijo_merval:
            lineas_indices.append(f"MERVAL: {_miles(merval['valor'])}{sufijo_merval}")
        else:
            lineas_indices.append(
                f"MERVAL: {_miles(merval['valor'])}{_flecha(merval['variacion_pct'])} "
                f"({merval['variacion_pct']:+.1f}%)"
            )
    if riesgo_pais is not None:
        # Sin flecha de color: en riesgo país bajar es "bueno", así que el verde/rojo (pensado
        # para precios, donde subir es verde) confundiría. Va la variación neutra + la fecha si
        # el dato quedó rezagado respecto del dólar (se publica por día hábil).
        sufijo_rp = _sufijo_frescura(riesgo_pais.get("fecha_origen"), referencia)
        lineas_indices.append(
            f"Riesgo país: {riesgo_pais['valor']:.0f} pts "
            f"({riesgo_pais['variacion_pct']:+.1f}%){sufijo_rp}"
        )
    if inflacion is not None:
        # Dato mensual (INDEC vía argentinadatos.com, publicado con lag): no se compara contra
        # la tanda anterior como el resto de los campos, sólo se muestra el último valor conocido
        # con el mes que mide — no tiene sentido marcarlo como "novedad" en cada tanda del día.
        mensual = inflacion.get("mensual")
        interanual = inflacion.get("interanual")
        partes = []
        if mensual is not None:
            partes.append(f"{mensual['valor']:.1f}% mensual")
        if interanual is not None:
            partes.append(f"{interanual['valor']:.1f}% interanual")
        if partes:
            fecha_ref = (mensual or interanual)["fecha_origen"]
            mes_texto = _fecha_mes_anio(fecha_ref)
            etiqueta = f" (dato de {mes_texto})" if mes_texto else ""
            lineas_indices.append(f"Inflación: {' / '.join(partes)}{etiqueta}")
    if lineas_indices:
        lineas += ["", "📊 <b>Índices</b>", *lineas_indices]

    if resumen_macro:
        lineas += [
            "",
            "📰 <b>Contexto macro</b>",
            resumen_macro,
        ]

    lineas += ["", "<i>Datos: dolarapi.com, estadisticasbcra.com, argentinadatos.com.</i>"]
    if fuentes_noticias:
        lineas.append(f"<i>Noticias: {', '.join(fuentes_noticias)}.</i>")
    lineas += ["", DISCLAIMER]

    return "\n".join(lineas)
