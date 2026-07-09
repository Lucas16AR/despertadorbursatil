"""Agrupa titulares que cubren el mismo evento (varios medios sobre la misma noticia) y los
prioriza por frecuencia entre fuentes: si varios medios distintos hablan de lo mismo el mismo
día, es una señal barata de que la noticia es genuinamente relevante.

Con 5+ fuentes, mandarle a Claude las docenas de titulares crudos diluye la síntesis (se vuelve
genérica o repetitiva). Esto le pasa el conjunto ya deduplicado y ordenado por relevancia.
Sin dependencias nuevas: solo la stdlib."""
from __future__ import annotations

import re
import unicodedata

# Umbral de solapamiento (sobre el titular más corto) para considerar que dos titulares
# hablan del mismo evento. Calibrado con titulares reales de las 5 fuentes.
UMBRAL_SIMILITUD = 0.5

# Palabras vacías o demasiado frecuentes en titulares de economía: no distinguen un evento de
# otro, así que no deben pesar al agrupar.
STOPWORDS = {
    "a", "al", "ante", "con", "como", "de", "del", "desde", "el", "en", "entre", "era", "es",
    "esta", "estas", "este", "estos", "fue", "ha", "han", "hay", "la", "las", "le", "les", "lo",
    "los", "mas", "más", "muy", "no", "para", "pero", "por", "que", "se", "ser", "sin", "sobre",
    "son", "su", "sus", "tras", "un", "una", "unas", "unos", "y", "ya", "o", "u", "e",
    "the", "of", "to", "in", "and", "for",
    # muy genéricas en este dominio puntual: casi todos los titulares las comparten
    "dolar", "peso", "pesos", "mercado", "mercados", "argentina", "argentino", "economia",
    "millones", "millon",
}


def _tokens(texto: str) -> set[str]:
    """Palabras significativas de un titular: minúsculas, sin acentos, de 4+ letras y sin
    stopwords. Sirven para medir cuánto se parecen dos titulares."""
    sin_acentos = unicodedata.normalize("NFKD", texto.lower())
    sin_acentos = "".join(c for c in sin_acentos if not unicodedata.combining(c))
    palabras = re.findall(r"[a-z0-9]+", sin_acentos)
    return {p for p in palabras if len(p) >= 4 and p not in STOPWORDS}


def _mismo_evento(a: set[str], b: set[str]) -> bool:
    """True si dos titulares comparten al menos UMBRAL_SIMILITUD de los términos significativos
    del más corto. Usar el más corto (y no Jaccard puro) evita que un titular muy largo, con
    muchos términos extra, deje de matchear a otro más escueto sobre el mismo hecho."""
    if not a or not b:
        return False
    return len(a & b) / min(len(a), len(b)) >= UMBRAL_SIMILITUD


def agrupar_titulares(titulares: list[dict]) -> list[dict]:
    """Agrupa por evento y ordena por relevancia. Devuelve una lista de grupos:
    {"titulo", "resumen", "fuentes": [..], "n_fuentes": int}, del más cubierto al menos.

    Agrupado codicioso de una pasada: cada titular se une al primer grupo con el que comparte
    evento, o abre uno nuevo. Los tokens del grupo son los del primer titular (semilla), estables
    para no ir "arrastrando" el grupo hacia noticias distintas; como representativo se muestra el
    titular más largo del grupo (suele ser el más informativo)."""
    grupos: list[dict] = []
    for t in titulares:
        titulo = (t.get("titulo") or "").strip()
        if not titulo:
            continue
        tokens = _tokens(titulo)
        fuente = t.get("fuente", "")
        for g in grupos:
            if _mismo_evento(tokens, g["_tokens"]):
                g["fuentes"].add(fuente)
                if len(titulo) > len(g["titulo"]):
                    g["titulo"] = titulo
                    g["resumen"] = (t.get("resumen") or "").strip()
                break
        else:
            grupos.append(
                {
                    "titulo": titulo,
                    "resumen": (t.get("resumen") or "").strip(),
                    "fuentes": {fuente},
                    "_tokens": tokens,
                }
            )

    for g in grupos:
        g["n_fuentes"] = len(g["fuentes"])
        g["fuentes"] = sorted(g["fuentes"])
        del g["_tokens"]

    # Más fuentes = más relevante; a igualdad, el titular más largo (más informativo) primero.
    grupos.sort(key=lambda g: (g["n_fuentes"], len(g["titulo"])), reverse=True)
    return grupos
