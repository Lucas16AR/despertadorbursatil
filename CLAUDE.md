# CLAUDE.md — Despertador Bursátil Argentino

*Nota (2026-07-04): esta carpeta antes vivía separada en `D:\Programacion\despertadorbursatil\` (código) y `Quantix\03-division-bursatil\despertador-bursatil\` (planificación). Ahora todo vive junto acá — un solo lugar para Cowork y Claude Code.*

Este es el repo de código del producto. El contexto de negocio completo vive en:

- `mvp-despertador-bursatil.md` (esta misma carpeta) — MVP, stack, riesgos, formato del mensaje, arquitectura V2 futura.
- `decisiones.md` (esta misma carpeta) — decisiones de negocio puntuales del producto.
- `../CLAUDE.md` — contexto de toda la división Atuel Insights (los otros 3 productos, prioridades, reglas de routing).
- `../../00-comando-central/snapshot-holding-2026.md` — contexto del holding completo, si hace falta.

**Leé `mvp-despertador-bursatil.md` completo antes de escribir código.** Ahí está todo lo decidido: qué entra en el MVP y qué no.

## Resumen ultra rápido para arrancar

- Stack: Python + GitHub Actions (cron) + Claude API (Haiku)
- Fuentes del MVP: dolarapi.com + estadisticasbcra.com (gratis, sin trámite). IOL API opcional/pluggable, no bloqueante — todavía sin aprobar.
- Contenido: dólar + MERVAL/BCRA + resumen macro con IA. **Sin recomendaciones de inversión con instrumentos específicos** (riesgo regulatorio — ver `mvp-despertador-bursatil.md`). El formato actual de datos + eventos fácticos ya está confirmado como seguro.
- Canal: Telegram operativo. WhatsApp (Canal) y el resto, después.
- **No construir panel de administración todavía** — es V2, documentado pero fuera de alcance ahora.

## Primera tarea — hecha (2026-07-02)

Script en Python que pega a dolarapi.com y estadisticasbcra.com, arma el mensaje agrupado por categoría, y lo manda al bot de Telegram. Operativo en producción vía GitHub Actions (cron 8am Argentina). Detalle completo en `PROGRESS.md`.

## Segunda tarea — resumen macro con IA — hecha (2026-07-02)

Sumado al mensaje diario un resumen de 2-4 oraciones del contexto macro, generado con Claude API (`claude-haiku-4-5`), a partir de 3 feeds RSS (Ámbito, Infobae Economía, El Cronista) + los datos duros ya calculados (dólar, MERVAL, brecha). No bloqueante: si falla el fetch o la API, el reporte de dólar + MERVAL se manda igual. Código en `rss_news.py` y `macro_summary.py`. Detalle completo en `PROGRESS.md`.

## Tercera tarea — disclaimer legal

Capi trajo un documento de referencia sobre riesgo regulatorio (CNV) y riesgo de baneo de WhatsApp por contenido percibido como "señales de trading". Confirma que el formato actual (datos + eventos fácticos, sin instrucción de compra/venta) está del lado seguro — no bloquea nada de lo ya construido, pero falta sumar el disclaimer fijo al final del mensaje.

**Estado: verificar si ya se implementó** — no está confirmado en `PROGRESS.md` todavía. Si no está, texto exacto a agregar en `formatter.py`, al final del mensaje (no bloqueante — si falla, no debe frenar el envío):

```
🤖 Alerta automatizada con fines puramente informativos y educativos. No constituye una recomendación de inversión, oferta de compra/venta ni asesoramiento bursátil. Operar bajo su propio riesgo.
```

Detalle completo del hallazgo en `mvp-despertador-bursatil.md`, sección de riesgos.

## Housekeeping pendiente (2026-07-04) — hacer esto primero, en orden, antes de cualquier tarea nueva

1. `git pull` — el repo está atrasado respecto a `origin/master` por al menos 1 commit, bajarlo primero para no generar conflictos.
2. `git add` + `git commit` de: `.gitignore` (ya corregido, agrega `.claude/`), los dos `CLAUDE.md` (este y el de `../CLAUDE.md`, ya corregidos), y `decisiones.md` (contenido nuevo sin commitear: nombre de la división "Atuel Insights", incorporación del Dashboard de inversiones).
3. `git push` para respaldar todo en GitHub.

(`.claude/` ya no debería trackearse desde ahora — quedó agregado al `.gitignore`.)

## Cuarta tarea — RESUELTA (2026-07-05, ver PROGRESS.md para el detalle completo)

Bug A: no era un bug de parseo — el MERVAL del tier gratis de estadisticasbcra.com está congelado desde 2024-08-30, y el oficial de dolarapi.com viene con lag real. Solución: frescura relativa por campo, marca `(al dd/mm)` y omite flecha si el dato está rezagado. Bug B: resuelto pasando a Canal de Telegram (`@despertadorbursatil`), validado con envío real. Queda pendiente una decisión de producto sobre qué hacer con el MERVAL congelado (ocultar vs. buscar fuente fresca) — ver tarea en Notion.

Contexto original de los bugs (para referencia histórica):

**A. Dólar oficial y MERVAL parecen congelados.**
- El dólar oficial mostró exactamente $1460/$1510 los 3 días, sin variar un solo peso.
- El MERVAL mostró exactamente el mismo valor (1714487) Y la misma variación (+2.9%) los 3 días — esto es virtualmente imposible en un índice real en ruedas distintas, es casi seguro un bug de datos stale/cacheados, no una coincidencia real de mercado.
- El resto del dólar (blue, MEP, CCL) sí varió correctamente entre el día 2 y el día 3, y las flechas de variación calculan bien contra el snapshot cuando el dato de origen cambia — el problema parece acotado a estos dos campos específicos (oficial y MERVAL), no a la lógica de comparación en general.
- **A investigar:** por qué `dolar.py` (casa "oficial") y `bcra.py` (MERVAL) están devolviendo el mismo valor día tras día — revisar si es un problema del fetch (caché, endpoint mal armado, parseo de la respuesta) o si realmente estadisticasbcra.com no está actualizando esa serie.

**B. El bot no le llega a otras personas, solo a Capi.**
- Causa más probable: el script manda el mensaje a un único `TELEGRAM_CHAT_ID` fijo (el chat privado de prueba de Capi, obtenido con `getUpdates` durante el setup — ver `PROGRESS.md`, 2026-07-02). Un bot 1:1 de Telegram no puede mandarle mensajes a alguien que no inició una conversación con él, y aunque la inicie, el código actual no tiene ningún mecanismo para detectar nuevos chats ni guardar una lista de suscriptores — solo conoce el chat_id de Capi, hardcodeado.
- **Opción recomendada, coherente con la decisión que ya tomamos para WhatsApp:** pasar de bot 1:1 a **Canal de Telegram** — el bot publica en el canal, cualquiera se suscribe libremente sin que el código tenga que conocer cada chat_id individual. Mismo patrón de distribución que el Canal de WhatsApp ya decidido.
- **Alternativa si se prefiere mantener el bot 1:1:** agregar manejo de suscriptores (detectar `/start`, guardar cada chat_id nuevo en el snapshot o un archivo aparte, loopear el envío a todos). Más trabajo y no escala tan bien como un canal.
- Decisión de cuál camino tomar: pendiente, a definir con Capi antes de que Code lo implemente.

**Orden sugerido:** resolver A y B antes de sumar cualquier feature nueva (Canal de WhatsApp, más fuentes de datos, etc.) — sin datos confiables y sin que el mensaje le llegue a nadie más que a Capi, no tiene sentido seguir escalando el producto.

## Quinta tarea — panel de administración (2026-07-04, en paralelo, no bloquea ni bloquea a la Cuarta tarea)

Capi confirmó que el panel de control (antes documentado como "V2, recién con tracción real") se puede empezar a construir **en paralelo** desde ya. No es MVP, no reemplaza ni compite en prioridad con la Cuarta tarea (bugs) — son pistas separadas.

Ver detalle completo de requisitos en `mvp-despertador-bursatil.md`, sección "Arquitectura V2 (paralelo, no bloquea el MVP): panel de control". Resumen:

- Front con diseño propio (Next.js tentativo) para administrar el sistema — no consola/texto plano.
- Gestión de fuentes de datos sin tocar código.
- La IA arma las notas/mensajes automáticamente desde las fuentes activas (generaliza lo que ya existe en el MVP).
- Logs, problemas y reportes en formato legible y rápido de escanear, no logs crudos.
- Métricas de audiencia por canal (WhatsApp, Telegram gratis, bot pago).
- Propuestas adicionales a confirmar con Capi antes de construir: preview del mensaje antes de enviar (editar/aprobar a mano), alertas proactivas cuando algo falla o un dato se ve anómalo, historial de envíos con estado, evolución de suscriptores en el tiempo, control de costos de las APIs pagas, interruptor por canal, gestión de suscripciones pagas (para el bot nivel 3, más adelante).
- Stack tentativo: Supabase (backend/DB) + Next.js (frontend) + mismo pipeline de Claude API del MVP, parametrizado por fuente.

## Modelo de negocio ampliado — roadmap de producto (2026-07-04)

Ver detalle completo en `mvp-despertador-bursatil.md`, sección "Modelo de negocio ampliado". Resumen para Code:

- **Nivel 1** (futuro): redes sociales (Instagram, TikTok, X, Threads) como embudo de marketing hacia los canales.
- **Nivel 2** (futuro, después de resolver bugs): escalar de 1 a 3 tandas diarias en los canales gratis.
- **Nivel 3** (incremental, en paralelo desde ya): bot de Telegram pago con info premium (hora a hora, último momento, tendencias de X/Twitter). Se va construyendo de a poco, sin bloquear el resto.
- **Orden de prioridad confirmado:** Cuarta tarea (bugs, resuelta) > distribución de Telegram/WhatsApp (resuelta para Telegram) > recién ahí 3 tandas diarias > redes sociales. El panel (Quinta tarea) y el bot pago (nivel 3) corren en paralelo a todo esto, no bloquean ni son bloqueados.
- Nombre comercial del Despertador: sigue sin definir, no bloquea nada.

## Sexta tarea — bot repurposeado + bienvenida del canal + 3 tandas diarias (2026-07-08, para la próxima sesión)

**A. Bot de Telegram: no construir botón de "unirse al canal".**
Decisión (2026-07-08): la gente se suma directo al canal vía su link público (`t.me/despertadorbursatil`), sin pasar por el bot. Motivo: el canal ya tiene su propio link de unión sin necesidad de bot; agregarle un flujo de `/start` con botón requeriría que el bot esté escuchando mensajes entrantes todo el tiempo (webhook o polling constante), infraestructura nueva que hoy no existe (el script solo corre una vez al día vía cron y se apaga). El bot queda dormido, reservado para el **nivel 3** (bot pago) del modelo de negocio — se reutiliza ahí en vez de invertir en algo que se descarta después.

**B. Mensaje de bienvenida del canal — no es posible un DM automático, sí un mensaje fijado.**
Telegram no permite que un bot le escriba en privado a alguien que nunca inició conversación con él — aplica también a suscriptores de un canal, es una restricción de la plataforma. La alternativa funcionalmente equivalente: **fijar (pin) un mensaje** en el canal (siempre visible arriba de todo al abrirlo) + completar la **descripción del canal**. Ninguna de las dos requiere código, se hacen a mano desde la app de Telegram como admin. Textos borrador (Cowork, 2026-07-08):

Mensaje a fijar:
```
📅 Despertador Bursátil Argentino

Reporte diario y automático de mercados argentinos: dólar (oficial, blue, MEP, CCL), MERVAL y contexto macro con IA — directo, sin vueltas, todas las mañanas.

🤖 100% informativo y automatizado. No es asesoramiento financiero ni recomendación de inversión — solo datos y contexto para que decidas vos.

Fuentes: dolarapi.com, estadisticasbcra.com, argentinadatos.com, Ámbito, Infobae, El Cronista, La Nación y Bloomberg Línea.
```

> **Actualizado (2026-07-09):** el texto de arriba ya refleja las 5 fuentes de noticias vigentes (se sumaron La Nación y Bloomberg Línea en la Séptima tarea) más argentinadatos.com (riesgo país, Octava tarea). **Pendiente de acción manual de Capi:** copiar este texto actualizado al mensaje fijado y a la descripción del canal en Telegram — no se actualiza solo, hay que pegarlo a mano como admin.

Descripción del canal (campo bio):
```
Reporte diario automático de dólar, MERVAL y contexto macro argentino. Informativo, no es asesoramiento financiero.
```

**C. Propuesta: 3 tandas diarias ancladas a los horarios reales de BYMA, no a horas arbitrarias.**
BYMA cambió su horario en 2025 para alinearse con Wall Street: la rueda va de **10:30 a 17:00 ART** ahora (antes era distinto). Propuesta (Cowork, 2026-07-08, a confirmar con Capi antes de implementar):
1. **8:00 — Pre-apertura** (la que ya existe): recap de cierre de ayer + agenda del día.
2. **~11:00 — Apertura**: reacción del mercado en los primeros minutos de rueda (después de la subasta de apertura 10:25-10:30).
3. **~17:15 — Cierre**: resumen con los datos reales de cierre de rueda.

Por qué anclarlo al mercado real y no a horas arbitrarias (ej. 8-14-20): cada mensaje aporta información genuinamente nueva (apertura, cierre) en vez de repetir casi los mismos números 3 veces, que es el tipo de ruido que hace que la gente deje de prestarle atención al canal. Implica sumar más entradas de cron al workflow de GitHub Actions y, probablemente, un parámetro de "momento del día" en `formatter.py`/`macro_summary.py` para que el tono/título de cada envío sea coherente con el momento (apertura vs. cierre), no el mismo texto genérico 3 veces.

**Todo lo de esta Sexta tarea queda para implementar en la próxima sesión con Code — nada de esto se tocó todavía.**

## Séptima tarea — sumar más fuentes de noticias con deduplicación (2026-07-08, para la próxima sesión)

Capi preguntó cómo escalar de 3 a más fuentes con calidad, y qué complicaciones aparecen. Análisis completo hecho por Cowork el 2026-07-08 (ver conversación). Resumen accionable:

**Fuentes nuevas propuestas (mismo patrón RSS de bajo riesgo que ya funciona con Ámbito/Infobae/Cronista):**
- Bloomberg Línea, La Nación Economía, Clarín Economía, BAE Negocios, Perfil — buscar y validar sus feeds RSS con `curl`, mismo proceso que se usó para las 3 fuentes actuales.
- Fuentes institucionales: comunicados de BCRA, CNV, INDEC (más autoridad, menos ruido editorial que un portal de noticias).

**Cambio de arquitectura necesario a partir de ~5-6 fuentes: deduplicación/priorización antes de mandarle todo a Claude.**
Con 3 fuentes alcanzaba con tirarle los titulares crudos al prompt. Con más, sin filtro, la síntesis se vuelve más genérica o repetitiva en vez de mejorar. Propuesta: agrupar titulares que hablan del mismo evento (varios medios cubriendo la misma noticia) y usar la frecuencia entre fuentes como señal barata de relevancia — si 4 medios distintos hablan de lo mismo el mismo día, es más probable que sea genuinamente importante. Recién ahí pasarle a Claude el conjunto ya priorizado/deduplicado, no las docenas de titulares crudos de todas las fuentes.

**Límites a respetar (no cruzar):**
- Solo titular + resumen corto del RSS (lo que ya se hace) — nunca reproducir el artículo completo de otro medio, eso sí es zona de riesgo de copyright.
- Fuentes sin RSS público confirmado (requerirían scraping) quedan afuera por ahora — mismo criterio ya aplicado a CNV/FCI.
- Redes sociales (X/Twitter) como fuente de "tendencias sin confirmar" quedan explícitamente para el bot pago (nivel 3), no para el canal gratis — si en algún momento se suma, hay que distinguir claramente "noticia confirmada" de "tendencia en redes, sin confirmar" para no arriesgar credibilidad.

**A vigilar, no bloqueante para arrancar:** costo de tokens (crece con más fuentes, aunque sigue siendo bajo con Haiku — ligado a la idea de "control de costos" ya anotada para el panel) y mantenimiento (cada feed nuevo es un punto más de falla si cambia de URL/formato — el diseño no bloqueante ya mitiga esto).

## Octava tarea — features nuevas priorizadas por Capi (2026-07-08, para la próxima sesión)

Cowork propuso una lista de ideas (brainstorming, ver conversación) y Capi eligió cuáles sumar. Quedan documentadas acá, ninguna implementada todavía:

**Casi gratis, con lo que ya existe:**
- **Cripto en el mensaje**: dolarapi.com ya devuelve la cotización cripto (USDT) — agregar la línea en `formatter.py`, sin integración nueva.
- **Glosario para principiantes**: mensaje fijado o sección ocasional explicando términos (brecha MEP/CCL, caución, etc.).
- **Encuestas en el canal**: usar polls nativos de Telegram para preguntar a la audiencia qué quiere ver — valida hipótesis y genera interacción.
- **Mensaje diario corto instructivo/histórico (idea de Capi, no estaba en la lista original de Cowork)**: todos los días, un mensaje corto y gratis con contenido educativo — una lección de economía/finanzas, o una efeméride ("un dato histórico, algo importante que pasó en el país en esa fecha"). Separado del reporte de datos — es contenido de valor agregado, no números. A definir: si va como mensaje aparte o como sección dentro de alguna de las tandas diarias (ver Sexta tarea, propuesta de 3 tandas).

**Más trabajo, valor claro:**
- **Agenda económica semanal**: formalizar como sección propia (licitaciones del Tesoro, publicaciones de INDEC, decisiones de tasas) — hoy aparece mencionada suelta en el resumen de IA cuando alguna fuente la toca, sin ser un campo estructurado.
- **Riesgo país como dato duro**: hoy solo aparece si algún medio lo menciona en el texto del resumen, sin fuente propia confiable — buscar API gratuita (revisar de nuevo Ámbito/Rava/BCRA, quedó sin resolver en la investigación original de fuentes).
- **Historial navegable simple**: página pública con los reportes de días anteriores — conecta con el producto "Comparador de rendimientos" ya planeado en la división, bueno para SEO/marketing (nivel 1).

**Más adelante, necesita más infraestructura — quedan anotadas, no priorizadas todavía:**
- **Resumen semanal**: edición tipo "Panorama Semanal" (idea que ya había salido del ejemplo de DCF Inversiones y se había dejado afuera del MVP) — revisarla ahora que el diario está estable.
- **Tendencia de la semana**: mini comparación "esta semana: +X%" usando el historial que ya empieza a guardar Supabase (tabla `envios`), en vez de comparar solo contra el día anterior.

**Orden sugerido para la próxima sesión (a confirmar con Capi):** priorizar primero lo de la Sexta tarea (bienvenida del canal, 3 tandas) y Séptima (fuentes + deduplicación) por ser más chicas y ya bien especificadas, y de esta Octava tarea arrancar por lo "casi gratis" antes que lo de "más adelante".

## Novena tarea — respuestas de Capi tras revisar la sesión del 2026-07-09 (para la próxima sesión con Code)

Capi respondió a los puntos que Code dejó abiertos y sumó precisiones nuevas. Nada de esto está implementado todavía.

**A. Tanda 22:30 (Balance del día) — alcance ampliado.**
No es solo un cierre de mercados: tiene que ser un panorama general de **todo lo que pasó en el día**, incluidas decisiones políticas que puedan afectar la economía/finanzas — no acotarlo a precios. Esto es más amplio que el `enfoque_macro` actual de esa tanda en `momento.py`, hay que ajustar el prompt/enfoque para reflejar "panorama general del día", no solo "balance de mercados + cierre externo".

**B. Comparación de flechas — confirmado por tanda, con un agregado en el cierre.**
Capi confirmó que la comparación contra la tanda anterior (no contra el día anterior) está bien. **Agregado:** en la tanda de las 17:15 (Cierre), sumar además una comparación contra el inicio del día (la tanda de las 8:00) — variación del día completo, no solo desde la última tanda. Sería una segunda cifra/línea en esa tanda específica, no reemplaza la comparación normal contra la tanda anterior.

**C. Mostrar variación en porcentaje en todos los mensajes, no solo flecha.**
Hoy el dólar muestra flecha (🟢▲/🔴▼/➖) pero no un número de variación — eso solo lo tiene el MERVAL. Capi pidió que **todos los campos con variación muestren el porcentaje**, en las 4 tandas de datos (no en los mensajes educativos/efemérides, que son otro tipo de contenido).

**D. Dos mensajes nuevos, separados de las tandas de datos — el sistema pasa a 6 mensajes/día.**

- **12:00 — Lección educativa corta.** Contenido chico para que la gente aprenda algo de economía o finanzas, de cualquier tema (no tiene que ser sobre Argentina específicamente). Pensado para que le sirva a la audiencia argentina del canal.
- **19:00 — Efemérides.** Un solo mensaje con **dos efemérides**: una de Argentina y una del mundo, con más énfasis/peso en la argentina. No tienen que ser estrictamente económicas — pueden ser de cualquier tema histórico relevante. Ejemplos que dio Capi como referencia de tono/formato:
  - *"Efeméride: un día como hoy el Dr. René Favaloro se quitaría la vida debido a..."* (ejemplo de efeméride general, no económica)
  - *"Se cumplen X años del 'Día D', el día que el gobierno de Mauricio Macri cambió sus metas económicas y financieras, para muchos el inicio del fin de su gobierno"* (ejemplo de efeméride económica/política)

**Con A-D, el sistema pasa de 4 a 6 mensajes diarios:** 8:00 (pre-apertura) → 11:00 (apertura) → 12:00 (lección educativa) → 17:15 (cierre, con variación del día completo) → 19:00 (efemérides AR + mundo) → 22:30 (panorama general del día, no solo mercados). Queda para Code definir si los dos mensajes nuevos (12:00 y 19:00) se generan con Claude (mismo patrón que el resumen macro) o con otro enfoque de contenido — no quedó especificado el mecanismo, solo el contenido y el horario.

## Undécima tarea — auditoría general del sistema (2026-07-09, para la próxima sesión, esfuerzo máximo)

Capi tiene rango de sesión extendido y va a correr esta tarea con esfuerzo máximo. El objetivo NO es sumar features nuevas — es tomar el pulso real de todo lo construido hasta ahora (Primera a Décima tarea) y dejarlo más sólido antes de seguir escalando. Revisar, corregir lo que se pueda corregir con confianza, y dejar documentado lo que requiera una decisión de producto.

**Alcance — revisar TODO el sistema, de punta a punta:**

1. **Todos los módulos Python** (`dolar.py`, `bcra.py`, `riesgo_pais.py`, `snapshot.py`, `formatter.py`, `telegram_client.py`, `rss_news.py`, `agrupador.py`, `macro_summary.py`, `momento.py`, `leccion_educativa.py`, `efemerides.py`, `ia.py`, `supabase_log.py`, `main.py`): buscar bugs reales (no solo estilo) — casos borde no contemplados (valores None, fuentes caídas, listas vacías, fechas mal parseadas, timezone), lógica de frescura y de variación (¿algún campo puede mostrar una flecha o un % engañoso en algún escenario no probado?), manejo de errores no bloqueante (¿de verdad ningún fetch individual puede tirar abajo el envío completo?), duplicación de código entre módulos que se pueda extraer a un helper común.
2. **`daily-report.yml` (workflow):** revisar los 6 cron, el mapeo momento↔schedule, el manejo de `concurrency` + `git pull --rebase --autostash`, y qué pasa si dos tandas corren casi al mismo tiempo o si una tanda falla a mitad de camino (¿deja el repo en un estado raro para la siguiente?).
3. **Seguridad y secretos:** confirmar que ninguna key/token quedó hardcodeada o loggeada en texto plano en ningún módulo nuevo (sobre todo los de la Novena/Décima, que son los más recientes y menos revisados). Revisar que `supabase_log.py` siga sin exponer la `service_role` key fuera del server.
4. **Costo real:** con 6 mensajes/día (4 de datos + 2 de contenido), estimar el costo mensual real de Haiku (tokens de entrada/salida aproximados por tipo de mensaje) y dejarlo anotado — hasta ahora todo se documentó como "despreciable" pero nunca se puso un número.
5. **Consistencia de producto:** revisar que el disclaimer legal (Tercera tarea) esté presente en los 6 mensajes, no solo en los de datos — sobre todo lección educativa y efemérides, que son contenido nuevo y no quedó explícito si lo llevan.
6. **Panel (`panel/`):** ¿sigue compilando y leyendo bien la tabla `envios` de Supabase con el nuevo campo `momento` y los mensajes de tipo `contenido`? Validar que el historial de envíos no se rompa con las categorías nuevas.
7. **Tests:** si no hay tests automatizados todavía, evaluar si vale la pena sumar al menos tests unitarios chicos para la lógica más frágil (parseo de fechas, cálculo de variación/frescura, `agrupador.py`) — es la lógica que más veces se tocó y la que más silenciosamente podría romperse con el próximo cambio.

**Reglas de la auditoría:**
- **Corregir con confianza los bugs reales** (los que tienen una solución objetivamente correcta, sin ambigüedad de producto) — no dejarlos solo anotados.
- **No tocar el contenido/tono/criterio de producto** (ej. no cambiar textos, no agregar mensajes nuevos, no cambiar horarios) sin marcarlo como propuesta para Cowork/Capi primero.
- **No romper nada que hoy funciona en producción** — cualquier cambio se valida antes de commitear (mismo criterio que se usó en toda la Novena/Décima tarea).
- Documentar todo en `PROGRESS.md` como una sección nueva "Undécima tarea — auditoría general", separando claramente: (a) bugs encontrados y corregidos, (b) mejoras aplicadas directamente por ser de bajo riesgo, (c) hallazgos que requieren decisión de Cowork/Capi antes de tocar nada.
- **Capi quiere esta auditoría también en PDF.** Code no genera el PDF — alcanza con dejar la sección bien escrita y completa en `PROGRESS.md` (título, subtítulos, los 3 grupos de hallazgos de arriba). Cowork arma el PDF a partir de eso en la siguiente sesión de revisión.

## Décima tarea — mostrar la brecha también en pp (2026-07-09, para la próxima sesión)

En la Novena tarea (parte C), Code dejó la brecha del dólar solo con flecha a propósito, porque su variación es en puntos porcentuales (pp) y no en % — mostrar "(+3%)" ahí sería confuso (se leería como variación relativa, no como el cambio real de la brecha). Capi confirmó: sumarlo igual, mostrando explícitamente la unidad correcta.

**Qué hacer:** en `formatter.py`, agregar al renglón de la brecha la variación en pp (diferencia simple entre el valor actual y el de la tanda anterior, no un cálculo de %), con el sufijo "pp" para que quede claro que no es lo mismo que el resto de los campos. Ejemplo: `Brecha: 40% 🔴▲ (+3pp)`. No tocar la lógica de los demás campos (dólar, MERVAL, riesgo país), que siguen en %.
