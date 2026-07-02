"""Fetch de titulares de las últimas 24hs desde los RSS de noticias macro/mercados
(Ámbito, Infobae Economía, El Cronista) para alimentar el resumen con IA."""
from __future__ import annotations

from calendar import timegm
from datetime import datetime, timedelta, timezone

import feedparser

FEEDS = {
    "Ámbito": "https://www.ambito.com/rss/pages/economia.xml",
    "Infobae": "https://www.infobae.com/arc/outboundfeeds/rss/category/economia/?outputType=xml",
    "El Cronista": "https://www.cronista.com/arc/outboundfeeds/rss/category/finanzas-mercados/?outputType=xml",
}

VENTANA_HORAS = 24


def fetch_titulares() -> list[dict]:
    """Devuelve [{"fuente", "titulo", "resumen"}] publicados en las últimas 24hs."""
    corte = datetime.now(timezone.utc) - timedelta(hours=VENTANA_HORAS)
    titulares = []
    for fuente, url in FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            publicado = entry.get("published_parsed")
            if publicado is None:
                continue
            fecha = datetime.fromtimestamp(timegm(publicado), tz=timezone.utc)
            if fecha < corte:
                continue
            titulares.append(
                {
                    "fuente": fuente,
                    "titulo": entry.get("title", "").strip(),
                    "resumen": entry.get("summary", "").strip(),
                }
            )
    return titulares
