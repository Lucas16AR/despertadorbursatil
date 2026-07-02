# PROGRESS.md

## 2026-07-01 — Primera tarea: script MVP (dólar + MERVAL → Telegram)

### Qué se hizo

Implementado el script completo pedido en `CLAUDE.md` ("Primera tarea"): pega a dolarapi.com y estadisticasbcra.com, arma el mensaje agrupado por categoría, lo manda al bot de Telegram. Sin panel, sin IOL, sin recomendaciones.

Archivos nuevos:
- `dolar.py` — fetch a dolarapi.com, filtra las casas relevantes (oficial, blue, MEP, CCL).
- `bcra.py` — fetch a estadisticasbcra.com, calcula variación % de MERVAL vs. el cierre anterior de la propia serie histórica que devuelve la API.
- `snapshot.py` — lee/escribe `data/last_snapshot.json`.
- `formatter.py` — arma el texto del mensaje: destacado del día + secciones por categoría + flechas de variación + disclaimer.
- `telegram_client.py` — POST a la Telegram Bot API (`sendMessage`, HTML parse mode).
- `main.py` — orquesta: fetch → formatear → enviar → guardar snapshot.
- `.github/workflows/daily-report.yml` — cron diario 8am Argentina (11:00 UTC), corre el script y commitea el snapshot actualizado.
- `requirements.txt`, `.env.example`, `README.md` (setup local + secrets de Actions).

### Decisiones técnicas

- **Snapshot en JSON commiteado por el propio workflow, no base de datos.** dolarapi.com no expone histórico, así que para calcular la variación día a día del dólar hacía falta persistir el valor de ayer entre corridas de GitHub Actions (que son efímeras). Una base de datos es la solución "correcta" pero es exactamente lo que el MVP pospone a V2 (ver "Arquitectura V2" en `mvp-despertador-bursatil.md`) — un archivo JSON que el workflow lee, actualiza y commitea de vuelta al repo resuelve el mismo problema sin infraestructura nueva.
- **Destacado del día = brecha MEP/oficial**, no "el dato con mayor variación". Se eligió porque es siempre calculable sin histórico (a diferencia de la variación del dólar, que si depende del snapshot) y porque coincide literalmente con el caso de uso de Ana en el doc del MVP ("la brecha MEP/oficial subió a 27%").
- **MERVAL sí tiene variación desde el primer envío**, sin depender del snapshot propio, porque estadisticasbcra.com devuelve la serie histórica completa (se toman los últimos dos puntos `d/v`) — a diferencia de dolarapi.com que solo da el valor actual.
- **Riesgo país y FCI quedaron afuera del script**, no solo por alcance del MVP sino porque el doc no confirma ninguna fuente con API pública gratuita para esos datos (queda como scraping/manual, sin resolver).
- **`from __future__ import annotations` en los módulos con tipos `X | None`**, porque el entorno local de desarrollo tiene Python 3.9 (esa sintaxis es de 3.10+) mientras que el workflow de GitHub Actions usa 3.12 — así el código corre en ambos sin duplicar sintaxis de tipos.
- **Sin la parte de "resumen macro con IA" (Claude API/Haiku)** todavía, aunque figura en el stack del MVP: la sección "Primera tarea" de `CLAUDE.md` la definió explícitamente como 3 pasos (fetch, formatear, mandar a Telegram) sin mencionar IA, y el propio doc del MVP deja "qué prompt genera el análisis" como pendiente de definir en otra sesión.

### Validado

- Fetch real a dolarapi.com probado en vivo (respuesta con las 4 casas esperadas).
- `formatter.armar_mensaje` probado con y sin snapshot previo — confirma flechas de variación correctas en ambos escenarios y que el primer envío (sin histórico) no rompe.
- No se probó el envío real a Telegram ni el fetch a estadisticasbcra.com (requieren credenciales que todavía no existen — ver pendientes).

### Actualización 2026-07-02 — credenciales y validación end-to-end local

- Bot de Telegram creado con BotFather. `TELEGRAM_CHAT_ID` obtenido vía `getUpdates` (chat privado de prueba).
- Token de estadisticasbcra.com obtenido en `/api/registracion` (expira al año, límite de 100 consultas/día — el script hace 1 por día, sobra margen).
- `python main.py` corrido localmente con las 3 credenciales reales: llegó el mensaje a Telegram con el formato esperado (destacado + dólar + MERVAL con variación), y `data/last_snapshot.json` quedó actualizado. Primer envío end-to-end validado.

### Pendiente

- Cargar los 3 secrets (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `BCRA_API_TOKEN`) en GitHub → Settings → Secrets and variables → Actions (no se pudo automatizar con `gh CLI` porque no está instalado en la máquina local — se hace manual por la web).
- Correr el workflow una vez a mano (`workflow_dispatch`) para confirmar que también funciona en GitHub Actions, no solo local, antes de dejar el cron de las 8am corriendo solo.
- Confirmar que el paso de commit-back del snapshot en el workflow funciona (permisos `contents: write` ya están seteados en el YAML, pero no probado en CI todavía).
- Del doc del MVP, sigue sin resolver: punto legal de "recomendaciones" (no aplica a este script, pero bloquea sumar esa sección más adelante), trámite de acceso a la API de IOL, fuentes de noticias/macro para el resumen con IA, nombre comercial del Despertador.
