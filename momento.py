"""Define los momentos del día en que sale un mensaje. Hay dos tipos:

- `datos`: las 4 tandas del reporte de mercados (pre-apertura, apertura, cierre, panorama de la
  noche). Cada una con su enfoque para el resumen macro, para que no repitan el mismo texto.
- `contenido`: los 2 mensajes de valor agregado (lección educativa 12:00, efemérides 19:00),
  que no llevan datos de mercado.

En total, 6 mensajes diarios. Los horarios de datos están anclados a la rueda real de BYMA
(10:30–17:00 ART desde 2025) más una tanda nocturna. El mapeo horario → momento vive en el
workflow de GitHub Actions; acá sólo está el contenido de cada momento."""
from __future__ import annotations

MOMENTO_DEFAULT = "pre_apertura"

MOMENTOS = {
    "pre_apertura": {
        "tipo": "datos",
        "emoji": "🌅",
        "titulo": "Pre-apertura",
        "subtitulo": "Cierre de ayer y agenda del día",
        "enfoque_macro": (
            "Este es el reporte de PRE-APERTURA, antes de que abra la rueda local. "
            "Enfocá el resumen en cómo cerró ayer y en lo que hay que mirar hoy "
            "(agenda económica, licitaciones, datos por publicarse)."
        ),
    },
    "apertura": {
        "tipo": "datos",
        "emoji": "🔔",
        "titulo": "Apertura",
        "subtitulo": "Primeros movimientos de la rueda",
        "enfoque_macro": (
            "Este es el reporte de APERTURA: la rueda local arrancó a las 10:30. "
            "Enfocá el resumen en la reacción inicial del mercado y el tono con el "
            "que abre la jornada."
        ),
    },
    "cierre": {
        "tipo": "datos",
        "emoji": "🌇",
        "titulo": "Cierre",
        "subtitulo": "Cómo cerró la rueda local",
        "enfoque_macro": (
            "Este es el reporte de CIERRE de la rueda local (17:00). Enfocá el "
            "resumen en cómo terminó la jornada del mercado argentino."
        ),
    },
    "cierre_global": {
        "tipo": "datos",
        "emoji": "🌙",
        "titulo": "Panorama del día",
        "subtitulo": "Todo lo que pasó hoy y puede mover la economía",
        "enfoque_macro": (
            "Este es el reporte de la NOCHE: un PANORAMA GENERAL de todo lo que pasó "
            "en el día, no solo precios. Cubrí el cierre de los mercados (local y "
            "externos, con Wall Street ya cerrado) pero también las decisiones "
            "políticas, medidas de gobierno y hechos relevantes que puedan afectar la "
            "economía o las finanzas, y cerrá con lo que puede marcar la agenda de mañana."
        ),
    },
    "leccion_educativa": {
        "tipo": "contenido",
        "emoji": "📚",
        "titulo": "Lección del día",
        "subtitulo": "Un concepto de economía y finanzas, simple",
    },
    "efemerides": {
        "tipo": "contenido",
        "emoji": "📜",
        "titulo": "Efemérides",
        "subtitulo": "Un día como hoy en Argentina y el mundo",
    },
}


def obtener_momento(clave: str | None) -> dict:
    """Devuelve la config del momento pedido (con su `clave` resuelta incluida), o la de
    pre-apertura si la clave es desconocida o vacía — así un envío nunca falla por un `MOMENTO`
    mal seteado. Devuelve una copia para no mutar la tabla del módulo."""
    resuelta = clave if clave in MOMENTOS else MOMENTO_DEFAULT
    config = dict(MOMENTOS[resuelta])
    config["clave"] = resuelta
    return config
