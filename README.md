# despertadorbursatil

Reporte diario de dólar, MERVAL y resumen macro con IA por Telegram. Contexto completo del producto en `mvp-despertador-bursatil.md`.

## Setup local

1. `pip install -r requirements.txt`
2. Copiar `.env.example` a `.env` y completar:
   - `TELEGRAM_BOT_TOKEN`: token del bot (hablar con [@BotFather](https://t.me/BotFather))
   - `TELEGRAM_CHAT_ID`: **Canal** de Telegram donde publica el bot (ver abajo)
   - `BCRA_API_TOKEN`: token gratuito de [estadisticasbcra.com/api](https://estadisticasbcra.com/api)
   - `ANTHROPIC_API_KEY`: API key de [console.anthropic.com](https://console.anthropic.com) para el resumen macro (Claude Haiku)
3. `python main.py`

El resumen macro (RSS de Ámbito/Infobae/El Cronista + Claude API) es no bloqueante: si falla la conexión a un feed o a la API, el script sigue y manda el reporte de dólar + MERVAL sin esa sección.

## Distribución: Canal de Telegram

El reporte se publica en un **Canal de Telegram** (no un chat 1:1), para que cualquiera pueda suscribirse libremente sin que el bot tenga que conocer cada `chat_id`. Un bot 1:1 sólo le puede escribir a quien le habló primero, así que no sirve para difusión.

Setup (una sola vez):

1. Crear un canal en Telegram (público, con `@usuario`, o privado).
2. Agregar el bot como **administrador** del canal con permiso de publicar.
3. Poner en `TELEGRAM_CHAT_ID` el `@usuario` del canal (o su id numérico `-100…`).

El código de envío no cambia: `sendMessage` publica en el canal igual que en un chat, siempre que el bot sea admin.

## GitHub Actions

`.github/workflows/daily-report.yml` corre el script todos los días a las 8am (Argentina). Cargar los mismos cuatro valores como *secrets* del repo (Settings → Secrets and variables → Actions).

El workflow commitea `data/last_snapshot.json` después de cada corrida — se usa para calcular la variación día a día del dólar (dolarapi.com no expone histórico).
