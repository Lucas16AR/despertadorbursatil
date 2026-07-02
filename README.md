# despertadorbursatil

Reporte diario de dólar, MERVAL y resumen macro con IA por Telegram. Contexto completo del producto en `mvp-despertador-bursatil.md`.

## Setup local

1. `pip install -r requirements.txt`
2. Copiar `.env.example` a `.env` y completar:
   - `TELEGRAM_BOT_TOKEN`: token del bot (hablar con [@BotFather](https://t.me/BotFather))
   - `TELEGRAM_CHAT_ID`: chat/canal donde postea el bot
   - `BCRA_API_TOKEN`: token gratuito de [estadisticasbcra.com/api](https://estadisticasbcra.com/api)
   - `ANTHROPIC_API_KEY`: API key de [console.anthropic.com](https://console.anthropic.com) para el resumen macro (Claude Haiku)
3. `python main.py`

El resumen macro (RSS de Ámbito/Infobae/El Cronista + Claude API) es no bloqueante: si falla la conexión a un feed o a la API, el script sigue y manda el reporte de dólar + MERVAL sin esa sección.

## GitHub Actions

`.github/workflows/daily-report.yml` corre el script todos los días a las 8am (Argentina). Cargar los mismos cuatro valores como *secrets* del repo (Settings → Secrets and variables → Actions).

El workflow commitea `data/last_snapshot.json` después de cada corrida — se usa para calcular la variación día a día del dólar (dolarapi.com no expone histórico).
