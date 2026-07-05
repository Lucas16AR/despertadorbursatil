# PROGRESS.md

## 2026-07-05 — Cuarta tarea (bugs A+B) + arranque de la Quinta (panel)

### Bug A — datos "congelados" (dólar oficial + MERVAL) → resuelto (presentación honesta)

Diagnóstico (verificado en vivo, no era bug de parseo):
- **Dólar oficial:** dolarapi.com sirve el oficial con lag — su `fechaActualizacion` va uno o
  más días detrás de blue/MEP/CCL. El valor $1460/$1510 era real, sólo viejo.
- **MERVAL:** peor — la serie del tier gratis de estadisticasbcra.com **termina el
  2024-08-30** (valor 1714487.33). Está congelada hace ~2 años; por eso valor y variación
  (+2.9%, el movimiento 29→30/08/2024) se repetían idénticos todos los días.

Solución (decisión de Capi: mostrar la fecha del dato, no marcar variación falsa):
- `dolar.py` y `bcra.py` ahora devuelven `fecha_origen` de cada dato.
- `formatter.py` usa **frescura relativa**: compara cada valor contra el más nuevo del propio
  lote (no contra "hoy", porque a las 8am/fin de semana la fuente siempre trae el cierre del
  día hábil anterior y marcaría todo como viejo). Si un campo quedó rezagado, muestra
  `(al dd/mm)` —con año si es de otro año, ej. `(al 30/08/2024)`— y **omite la flecha**.
  Un campo fresco se comporta igual que antes.
- Nuevo `detectar_anomalias()` reutiliza esa lógica para alimentar el panel.
- Validado local con datos reales + unit checks del parseo de fechas y del sufijo.

> **Pendiente de producto (no de código):** mostrar un MERVAL de agosto 2024 todos los días,
> aunque sea honesto, es de poca utilidad. A decidir con Capi en la próxima ronda: ocultar la
> línea de MERVAL hasta tener una fuente fresca, o buscar fuente alternativa (IOL / API BCRA).
> Esta ronda dejó la opción "buscar fuente" explícitamente afuera.

### Bug B — el reporte sólo le llegaba a Capi → resuelto por diseño (Canal de Telegram)

Causa: se enviaba a un único `TELEGRAM_CHAT_ID` (chat 1:1). Un bot 1:1 no puede escribirle a
quien no le habló primero. Decisión de Capi: **Canal de Telegram** (el bot publica, cualquiera
se suscribe). No requiere cambio de código —`sendMessage` publica igual en un canal si el bot
es admin— sólo setup manual + cambiar el secret. Documentado en `README.md` y `.env.example`.

**Acción manual pendiente de Capi:** crear el canal, sumar el bot como admin, y apuntar
`TELEGRAM_CHAT_ID` (secret de Actions + `.env`) al `@usuario`/id del canal.

### Quinta tarea — arranque del panel (primera rebanada: Historial de envíos)

- **Supabase:** proyecto nuevo `despertador-bursatil` (id `kazjrgekyxwloumkkhvu`, región
  sa-east-1, free tier $0). Tabla `envios` (fecha, canal, estado, mensaje, datos jsonb,
  anomalías jsonb, error). RLS activa **sin policies públicas**: acceso sólo server-side.
- **Pipeline → DB:** `supabase_log.py` inserta una fila por corrida vía PostgREST (sin sumar
  dependencias). Cableado en `main.py`, **no bloqueante** (mismo criterio que el resumen
  macro). Envs nuevas: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.
- **Panel Next.js** en `panel/`: App Router + diseño propio (light/dark), página "Historial de
  envíos" que lee de Supabase server-side (service_role, nunca en el browser) y muestra fecha,
  estado, canal, anomalías destacadas y preview del mensaje. `npm run build` OK; render
  validado end-to-end contra una fila de ejemplo.

**Acciones manuales pendientes de Capi para dejarlo operativo:**
1. Copiar la `service_role` key de Supabase (dashboard → Project Settings → API) a:
   los secrets de GitHub Actions (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`) y a
   `panel/.env.local`.
2. (Opcional) deployar el panel a Vercel para no correrlo local.

### Pendiente de commit

Los cambios de código de esta tanda están en el working tree, **sin commitear todavía** (a la
espera de revisión). El `.gitignore` del panel ya excluye `node_modules` y `.next`; se
commitea sólo el código fuente.

## Estado actual (2026-07-02, fin del día)

MVP operativo: el cron de GitHub Actions manda el reporte de dólar + MERVAL + resumen macro con IA a Telegram todos los días a las 8am (Argentina). Los 4 secrets (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `BCRA_API_TOKEN`, `ANTHROPIC_API_KEY`) ya están cargados en GitHub. Las dos tareas del roadmap de hoy (script base + resumen macro con IA) están hechas y validadas en local; falta solo ver la corrida automática de mañana para confirmar que también anda sola en Actions con las 4 credenciales — no requiere acción manual, se revisa mañana.

**Modelo de IA usado:** `claude-haiku-4-5` (Claude Haiku) — es el modelo más barato del catálogo de Anthropic. Elegido a propósito, no por default: el resumen macro es una tarea simple (sintetizar titulares + datos ya calculados en 2-4 oraciones), no necesita el razonamiento de un modelo más caro, y el volumen es 1 llamada/día — el costo es prácticamente nulo.

## 2026-07-04 — Tercera tarea: disclaimer legal + housekeeping git

### Disclaimer legal (hecho)

Agregado el texto de descargo exacto al final de cada mensaje en `formatter.py`
(commit `42f243d`), por el riesgo regulatorio CNV y el riesgo de baneo en
WhatsApp por contenido percibido como "señales de trading":

> 🤖 Alerta automatizada con fines puramente informativos y educativos. No
> constituye una recomendación de inversión, oferta de compra/venta ni
> asesoramiento bursátil. Operar bajo su propio riesgo.

Reemplaza la versión corta previa ("No es asesoramiento financiero"). Es un
string estático dentro de `armar_mensaje()`, no puede fallar ni bloquear el
envío. Validado localmente: el mensaje renderiza con el disclaimer al final,
después de la línea de fuentes. **Tercera tarea del roadmap cerrada.**

### Housekeeping git (hecho)

`git pull` (fast-forward de 1 commit: snapshot actualizado por el cron) +
commit/push de: `.gitignore` (ahora ignora `.claude/`), `CLAUDE.md`
actualizado y `decisiones.md` nuevo (nombre de la división "Atuel Insights" +
incorporación del Dashboard de inversiones). Commit `0de9a93`. `.claude/` ya no
está trackeado.

## 2026-07-02 — Segunda tarea: resumen macro con IA (Claude Haiku)

### Qué se hizo

Implementado el resumen macro definido en `mvp-despertador-bursatil.md` (sección "Resumen macro con IA"): titulares de RSS + datos duros ya calculados → síntesis de 2-4 oraciones con Claude API (Haiku), sin instrucciones de inversión.

Archivos nuevos:
- `rss_news.py` — `fetch_titulares()`: pega a los RSS de Ámbito Financiero, Infobae Economía y El Cronista (feeds `arc/outboundfeeds` para Infobae/Cronista, `rss/pages` para Ámbito — URLs exactas confirmadas con `curl`, no solo las páginas genéricas de canales que daba el doc), filtra por `published_parsed` a las últimas 24hs.
- `macro_summary.py` — `generar_resumen_macro()`: arma el prompt (brecha + dólares + MERVAL + titulares) y llama a Claude API con `model="claude-haiku-4-5"` — modelo fijado explícitamente por instrucción del propio proyecto (`CLAUDE.md` dice "Claude API (Haiku)"), no el default de Opus. Devuelve `None` si la llamada falla, para no bloquear el resto del reporte.

Archivos modificados:
- `formatter.py` — `armar_mensaje()` ahora acepta `resumen_macro: str | None` opcional y agrega una sección "📰 Contexto macro" solo si hay resumen.
- `main.py` — orquesta el fetch de titulares + la llamada a Claude dentro de un `try/except` que no bloquea el envío del reporte si falla (mismo criterio "no bloqueante" que ya se usa para IOL en el doc del MVP).
- `requirements.txt` — sumadas `feedparser==6.0.11` y `anthropic==0.115.1`.
- `.env.example` y el workflow de GitHub Actions — sumada `ANTHROPIC_API_KEY`.

### Decisiones técnicas

- **No bloqueante por diseño.** Si el fetch de RSS o la llamada a Claude fallan (red caída, rate limit, feed roto), el script sigue y manda el reporte de dólar + MERVAL sin la sección de contexto macro, en vez de que falle todo el envío. Mismo criterio que "IOL opcional/pluggable" del doc del MVP.
- **Modelo Haiku, no el default de Opus.** El proyecto define explícitamente Claude API (Haiku) como parte del stack en `CLAUDE.md` y `mvp-despertador-bursatil.md` — se respetó esa decisión ya tomada en vez de usar el modelo por default de las guías generales de la API.
- **Prompt sin instrucciones de inversión**, coherente con la sección de riesgos del MVP (recomendaciones = zona gris regulatoria) — el system prompt lo prohíbe explícitamente.

### Validado

- `rss_news.fetch_titulares()` probado en vivo: trajo 89 titulares reales de los 3 feeds en la ventana de 24hs.
- `formatter.armar_mensaje()` probado con y sin `resumen_macro` — la sección nueva aparece solo cuando corresponde y no rompe el formato existente.
- `macro_summary._armar_prompt()` probado con datos de ejemplo — arma el texto esperado (brecha + dólares + MERVAL + titulares).
- Compilación (`py_compile`) e import de todos los módulos nuevos/modificados sin errores.

### Actualización 2026-07-02 — validación end-to-end con Claude API real

- `ANTHROPIC_API_KEY` cargada en `.env` local.
- `generar_resumen_macro()` probado en aislado con datos reales (85 titulares de los 3 feeds + dólar/MERVAL/brecha del día): devolvió una síntesis de 3 oraciones, coherente y sin instrucciones de inversión.
- `python main.py` corrido completo: llegó el mensaje a Telegram con la sección "📰 Contexto macro" incluida, y `data/last_snapshot.json` quedó actualizado. Primer envío end-to-end con resumen macro validado localmente.

`ANTHROPIC_API_KEY` ya cargada también como secret de GitHub Actions (2026-07-02) — con esto, el resumen macro con IA queda completo y operativo en los 3 entornos (local, Actions). Sin pendientes propios de esta tarea; queda solo confirmar en la corrida automática de mañana (o un `workflow_dispatch` manual) que también funciona en Actions, mismo criterio que se usó para validar el MVP original.

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

### Actualización 2026-07-02 — commit/push inicial y primera corrida en GitHub Actions

- El repo estaba sin commitear/pushear hasta este punto (todo el trabajo anterior era solo local) — commiteado y pusheado a `origin/master`, incluyendo el snapshot de la corrida local de prueba.
- Primer intento de `workflow_dispatch` falló: `403 Forbidden` en la llamada a estadisticasbcra.com/merval. Se agregó logging del cuerpo de la respuesta en `bcra.py` para diagnosticar (token mal cargado vs. bloqueo de IP de datacenter, ambos dan 403 en esta API).
- Causa real: el secret `BCRA_API_TOKEN` en GitHub Actions se había cargado mal (error de tipeo al pegar el valor). Corregido en Settings → Secrets → Actions, no era un problema de código ni de bloqueo de IP.
- Segunda corrida de `workflow_dispatch`: **exitosa**. El MVP completo (dólar + MERVAL → Telegram) corre end-to-end en GitHub Actions, no solo local. El cron diario de las 8am (Argentina) queda operativo.

### Pendiente

- Confirmar en la próxima corrida automática (mañana 8am) que el paso de commit-back del snapshot en el workflow efectivamente actualiza `data/last_snapshot.json` en el repo sin intervención manual.
- Del doc del MVP, sigue sin resolver: punto legal de "recomendaciones" (no aplica a este script, pero bloquea sumar esa sección más adelante), trámite de acceso a la API de IOL, fuentes de noticias/macro para el resumen con IA, nombre comercial del Despertador.
