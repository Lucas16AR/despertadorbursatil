"""Define los cuatro momentos del día en que sale el reporte. Cada tanda tiene su
propio título/emoji y una instrucción de enfoque para el resumen macro, para que los
cuatro envíos no repitan el mismo texto genérico sino que aporten algo propio del
momento (pre-apertura, apertura de rueda, cierre local, balance global de la noche).

Los horarios están anclados a la rueda real de BYMA (10:30–17:00 ART desde 2025) más
una tanda nocturna con Wall Street ya cerrado. El mapeo horario → momento vive en el
workflow de GitHub Actions; acá sólo está el contenido de cada momento."""
from __future__ import annotations

MOMENTO_DEFAULT = "pre_apertura"

MOMENTOS = {
    "pre_apertura": {
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
        "emoji": "🌇",
        "titulo": "Cierre",
        "subtitulo": "Cómo cerró la rueda local",
        "enfoque_macro": (
            "Este es el reporte de CIERRE de la rueda local (17:00). Enfocá el "
            "resumen en cómo terminó la jornada del mercado argentino."
        ),
    },
    "cierre_global": {
        "emoji": "🌙",
        "titulo": "Balance del día",
        "subtitulo": "Wall Street cerrado y balance de la jornada",
        "enfoque_macro": (
            "Este es el reporte de la NOCHE, con Wall Street ya cerrado. Enfocá el "
            "resumen en el balance del día completo (mercado local + mercados "
            "externos) y en lo que puede marcar la agenda de mañana."
        ),
    },
}


def obtener_momento(clave: str | None) -> dict:
    """Devuelve la config del momento pedido, o la de pre-apertura si la clave es
    desconocida o vacía — así un envío nunca falla por un `MOMENTO` mal seteado."""
    return MOMENTOS.get(clave or MOMENTO_DEFAULT, MOMENTOS[MOMENTO_DEFAULT])
