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

## Decimoséptima tarea — MERVAL fresco vía API de IOL (2026-07-11, requiere acción manual de Capi primero)

Capi preguntó qué hacer con el MERVAL. Investigación de Cowork (2026-07-11): **confirmado que estadisticasbcra.com no es arreglable** — entré a su página pública (no solo la API) y el propio sitio muestra el mismo dato congelado del 30/08/2024 (`1714490`). No es una limitación del tier gratis ni un problema de nuestro fetch: la fuente dejó de actualizar esa serie hace casi 2 años, en el sitio entero.

**Camino elegido por Capi: API de IOL (invertironline.com).** Es la fuente oficial/regulada, con cotizaciones en tiempo real del MERVAL y, a futuro, de acciones/CEDEARs/cauciones (ya estaba anotado como trámite pendiente en Notion desde el arranque del proyecto — esta tarea lo retoma con foco concreto en MERVAL).

**Paso 1 — acción manual de Capi, no de Code:**
1. Abrir una cuenta en IOL (gratis, sin costo de mantenimiento) si no tenés una — `https://www.invertironline.com`.
2. Pedir acceso a la API desde la cuenta: sección de consultas, "Tipo de solicitud" = "Mi cuenta", "Razón de contacto" = "Api" (instrucciones en `https://www.invertironline.com/api`).
3. Una vez aprobado, guardar las credenciales (usuario/contraseña o el mecanismo de auth que dé IOL — su API usa OAuth con usuario/clave de la cuenta, a confirmar en la documentación real `https://api.invertironline.com/`) como nuevo secret de GitHub Actions.

**Paso 2 — para Code, recién cuando Capi confirme que el trámite está aprobado:**
1. Revisar la documentación real de la API en `https://api.invertironline.com/` (autenticación, endpoint de cotización del índice MERVAL — probablemente bajo "Cotización de Título" con símbolo del índice, a confirmar).
2. `merval.py` (reemplaza el uso de `bcra.py` para MERVAL, o convive si `bcra.py` sigue usándose para otra cosa del BCRA — revisar): `fetch_merval()` con la misma forma que hoy (`{valor, variacion_pct, fecha_origen}`) para no tener que tocar `formatter.py` más que lo mínimo.
3. Mantener el mismo criterio de no bloqueante ya reforzado en la Undécima tarea (auditoría): si el fetch de IOL falla, el reporte sale igual sin esa línea.
4. Si el token/sesión de IOL tiene expiración corta (a confirmar en la documentación), sumar el refresh como parte del fetch, no como paso manual repetido.

**No implementar nada de código todavía** — esta tarea queda bloqueada hasta que Capi complete el paso 1. Mientras tanto, el MERVAL sigue mostrándose con `(al 30/08/2024)` como hasta ahora, honesto pero desactualizado.

**Descartado en esta ronda:** un JSON público de Rava Bursátil (su web sí muestra el MERVAL actualizado al día, pero no hay una API pública documentada — mismo criterio ya aplicado a CNV/INDEC: sin API/RSS confirmado, no se scrapea).

## Decimoquinta tarea — acreditar las fuentes de noticias en el mensaje (2026-07-11, para la próxima sesión)

Cuarto ítem de la ronda. Este pendiente ya estaba anotado desde la Séptima tarea (PROGRESS.md, 2026-07-09: "el pie del mensaje sigue acreditando solo las fuentes de dato duro... si se quiere acreditarlas, es decisión de contenido") — **Capi confirma ahora: sí, sumarlas.**

**Estado actual:** el pie del mensaje (`formatter.py`, línea ~244) dice `Fuente: dolarapi.com, estadisticasbcra.com, argentinadatos.com.` — solo las 3 fuentes de dato duro. Las 5 fuentes de noticias que alimentan "📰 Contexto macro" (`rss_news.FEEDS`: Ámbito, Infobae, El Cronista, La Nación, Bloomberg Línea) no aparecen acreditadas en ningún lado del mensaje.

**Qué hacer:** sumar las fuentes de noticias al pie, distinguibles de las de dato duro para que no se lea como una lista plana de 8 nombres sin contexto — ej. dos líneas:
```
Datos: dolarapi.com, estadisticasbcra.com, argentinadatos.com.
Noticias: Ámbito, Infobae, El Cronista, La Nación, Bloomberg Línea.
```
Tomar los nombres directamente de `rss_news.FEEDS.keys()` (no hardcodear la lista aparte, para que si se agrega/saca una fuente en el futuro el pie se actualice solo). Aplica a los 4 mensajes de datos; en lección educativa y efemérides no corresponde (no usan RSS).

## Decimosexta tarea — investigar por qué los envíos no salen a horario exacto (2026-07-11, para la próxima sesión)

Capi reportó que los mensajes no están saliendo en los horarios definidos (8:00, 11:00, 12:00, 17:15, 19:00, 22:30 ART).

**Diagnóstico de Cowork (2026-07-11), a confirmar/profundizar con Code:** los 6 `cron` de `daily-report.yml` están bien mapeados a horario argentino (revisado uno por uno en la Undécima tarea), así que no parece un error de cálculo de horario. La causa más probable es una **limitación conocida de GitHub Actions, no un bug del código**: los `schedule` triggers de Actions son *best-effort* — GitHub explícitamente advierte que pueden demorarse en momentos de carga alta, y esa carga alta se concentra justo **en los minutos exactos de cada hora** (`:00`), que es exactamente donde caen 4 de los 6 cron actuales (`0 11`, `0 14`, `0 15`, `0 22`). Cuantos más workflows de todo el mundo estén programados para el mismo minuto redondo, más chance de cola y demora — a veces varios minutos, a veces más.

**Qué hacer:**
1. Confirmar el diagnóstico revisando el historial real de corridas en GitHub Actions (hora programada vs. hora real de inicio de cada run de las últimas corridas) — si el patrón de demora coincide con los minutos en punto, confirma la hipótesis.
2. **Mitigación recomendada:** correr los cron unos minutos *desfasados* de la hora/cuarto exactos (ej. `3 11 * * *` en vez de `0 11 * * *`, `4 14 * * *`, `7 15 * * *`, `2 22 * * *`, manteniendo `15 20 * * *` y `30 1 * * *` que ya están desfasados) — reduce la probabilidad de quedar en la cola de carga pico, aunque no la elimina del todo (sigue siendo best-effort de la plataforma).
3. Dejar documentado en `README.md` o en el pie del panel que los horarios son aproximados por una limitación de la plataforma de cron gratuita (GitHub Actions), no una garantía exacta al minuto — para que quede claro que no es indicativo de un bug si algún día sale con unos minutos de diferencia.
4. Si la demora resulta ser sistemática y grande (no solo unos minutos), es una señal de que GitHub Actions no alcanza como scheduler para este nivel de precisión y habría que evaluar alternativas (ej. un cron externo tipo cron-job.org que dispare el workflow vía `workflow_dispatch`/repository_dispatch) — pero no implementar esto todavía, primero confirmar qué tan grave es la demora real.

> **Decisión de Capi (2026-07-11):** avanzar solo con el desfasaje de minutos (punto 2) por ahora. La opción de cron externo (punto 4) queda documentada pero **no se implementa** — agrega una dependencia de terceros y un token de GitHub guardado fuera del repo, y no se justifica todavía sin antes medir si el desfasaje simple ya resuelve el problema. Si después de una semana con los cron desfasados la demora sigue siendo notoria, se retoma esa opción.

## Decimotercera tarea — legibilidad del resumen de contexto macro (2026-07-11, para la próxima sesión)

Segundo ítem de la ronda de mejoras que empezó la Duodécima tarea ("vamos uno a uno"). Capi pidió mejorar la legibilidad del bloque "📰 Contexto macro": hoy sale como un párrafo de 2-4 oraciones todo junto, sin ningún corte visual, y en el celular se lee como un bloque de texto pesado.

**Causa:** `macro_summary.SYSTEM_PROMPT` le pide a Claude una "síntesis de 2 a 4 oraciones" en prosa corrida, sin ninguna instrucción de formato. `formatter.py` inserta ese texto tal cual después del header "📰 <b>Contexto macro</b>" (línea ~239) — no reformatea nada, así que el formato depende 100% de lo que devuelva el prompt.

**Qué hacer:** cambiar `SYSTEM_PROMPT` (y `_armar_prompt` si hace falta más contexto) para que Claude devuelva el resumen en **puntos cortos separados por salto de línea**, no un párrafo corrido. Criterio sugerido:
- 2 a 4 líneas, cada una una idea/tema distinto (ej. una línea de dólar/mercados, otra de la noticia más relevante del día, otra de algo político/macro si aplica) — no forzar 4 si con 2-3 alcanza.
- Cada línea arranca con un bullet simple (`• `) para que se lea separado en Telegram (el mensaje ya usa `parse_mode=HTML`, así que un bullet de texto plano + `\n` entre líneas alcanza, no hace falta `<ul>/<li>`, Telegram no los soporta).
- Frases cortas y directas, mismo tono rioplatense y mismas reglas de siempre (sin recomendaciones de inversión).
- Verificar que el texto que devuelve Claude no rompa el parseo HTML del mensaje si por accidente incluye `<`, `>` o `&` (algún titular con esos caracteres) — si no hay un escape ya aplicado en el pipeline, sumarlo acá de paso.

**Validar con datos reales** (mismo criterio que toda tarea anterior): correr `generar_resumen_macro` con titulares reales y confirmar que el mensaje final se ve bien en Telegram (líneas separadas, no un bloque).

**No tocar en esta tarea:** el resto del mensaje (dólar, MERVAL, disclaimer) ni el criterio de qué se cuenta — solo el formato visual de este bloque puntual.

> **Aclaración de Capi (2026-07-11), aplica también a esta tarea y a cualquier ajuste de formato futuro:** el objetivo es legibilidad, no recortar información. El resumen tiene que seguir siendo informativo y con contenido valioso — no vaciar el mensaje ni forzar brevedad artificial que corte algo real solo por entrar en menos líneas. Si un día hay más para contar, mejor 4 bullets bien informativos que 2 bullets vacíos de contenido.

## Decimocuarta tarea — indicador de microeconomía: inflación mensual/interanual (2026-07-11, para la próxima sesión, viable ahora)

Tercer ítem de la ronda de mejoras. Capi pidió sumar algo de microeconomía — datos que importen "en tiempos de crisis como el actual" — y preguntó si es viable ahora o si queda para más adelante. **Es viable ahora**, con la misma fuente que ya se usa para riesgo país.

**Fuente confirmada (Cowork, 2026-07-11):** `argentinadatos.com`, gratis, sin key, mismo patrón que `riesgo_pais.py`.
- `GET https://api.argentinadatos.com/v1/finanzas/indices/inflacion` → serie histórica mensual, `{"fecha": "2026-05-31", "valor": 2.1}` (variación % del mes, no acumulado).
- `GET https://api.argentinadatos.com/v1/finanzas/indices/inflacion-interanual` → mismo formato, interanual.

**Qué hacer:**
1. `inflacion.py` (nuevo, mismo patrón que `riesgo_pais.py`): `fetch_inflacion()` → trae el último punto de cada serie (mensual + interanual), no bloqueante (si falla, el reporte sale igual).
2. Sumar una línea a la sección "📊 Índices" (o una sección nueva "📉 Microeconomía" si Code considera que separa mejor el tema del resto de índices bursátiles — a criterio, no es una decisión de contenido sensible): `Inflación: 2.1% mensual / X% interanual (dato de mayo 2026)`. El INDEC publica con 1-2 semanas de rezago, así que casi siempre va a mostrar `(al dd/mm)` — es normal, mismo criterio de frescura relativa que el resto.
3. Sumarlo también al prompt de `macro_summary.py` (`_armar_prompt`) como dato duro más, para que el resumen lo pueda mencionar cuando sea relevante.
4. **No forzar la inflación en el resumen de cada tanda** — es un dato mensual, no diario, así que no cambia entre tandas del mismo día. Mostrarla igual en el bloque de datos (es información de contexto útil aunque no varíe hoy), pero no tiene sentido que la IA la repita como "novedad" en las 4 tandas de datos.

**Otras ideas de microeconomía que Capi mencionó en términos generales pero que NO tienen fuente gratuita confirmada todavía — quedan para más adelante, no bloquean esta tarea:**
- Canasta básica / línea de pobreza: INDEC no tiene API (ya se había descartado su RSS en la Séptima tarea, devuelve HTML) — requeriría scraping, fuera del criterio actual de fuentes.
- Salario mínimo, vital y móvil: no encontrado en argentinadatos.com todavía — a revisar en la próxima ronda de revisión de fuentes (ver tarea programada quincenal `despertador-revision-fuentes-rss`).
- UVA (índice usado para indexar alquileres y créditos hipotecarios) sí está disponible en argentinadatos.com (`GET /v1/finanzas/indices/uva`) — muy relevante en crisis para quien alquila o tiene un crédito UVA, pero es un tema aparte de la inflación general. Anotado como candidato a una futura tarea si Capi lo confirma, no se suma en esta.

## Duodécima tarea — mejoras al mensaje tras los primeros días en producción (2026-07-11, para la próxima sesión)

Capi lleva un par de días con el canal andando bien (mensajes, efemérides y lecciones saliendo sin problemas) y pide la primera ronda de ajustes de calidad, revisando el contenido real. Primer bloque de una serie ("vamos uno a uno") — esta sesión solo cubre lo de abajo, no anticipar el resto.

**A. Mostrar las 7 cotizaciones del dólar que ofrece dolarapi.com, no solo 5.**
Hoy `dolar.py` (`CASAS_RELEVANTES`) sólo trae oficial, blue, bolsa (MEP), contadoconliqui (CCL) y cripto. dolarapi.com (`GET https://dolarapi.com/v1/dolares`) devuelve 7 casas — faltan sumar:
- `mayorista` → "Mayorista"
- `tarjeta` → "Tarjeta"

Orden sugerido para `ORDEN_CASAS` en `formatter.py` (agrupa lo más consultado primero, tarjeta al final por ser un recargo sobre el oficial, no una cotización de mercado): Oficial, Blue, MEP (bolsa), CCL (contadoconliqui), Mayorista, Cripto, Tarjeta.

**B. Mostrar los centavos cuando la casa los tiene.**
El formateo actual usa `:.0f` en `compra ${info['compra']:.0f} / venta ${info['venta']:.0f}` — trunca los decimales. dolarapi.com sí devuelve centavos en varias casas (ej. `bolsa: compra 1513.3`, `cripto: compra 1561.21`). Cambiar a mostrar 2 decimales cuando el valor no es entero, y sin decimales cuando sí lo es (para no mostrar "1460.00" en el oficial si viene redondo) — un helper tipo `_precio_texto(valor)` que decida el formato según si `valor == int(valor)`.

**C. Sumar la leyenda de fuente/fecha de dolarapi.com al final de la sección de dólar.**
Referencia exacta que dio Capi (texto real de dolarapi.com, hay que replicar el formato):
```
Datos obtenidos de DolarApi.com (https://dolarapi.com/)
Actualizado el 11/07/2026 a las 17:59
```
Tomar el `fechaActualizacion` más reciente entre las 7 casas (ISO 8601 UTC), convertirlo a horario de Argentina y formatearlo `dd/mm/aaaa` + `HH:MM`. Esto es aparte del pie de "Fuente" que ya existe al final de todo el mensaje (dolarapi.com + estadisticasbcra.com + argentinadatos.com) — va específicamente después del bloque de cotizaciones de dólar, como referencia de frescura de esa fuente puntual.

**D. MERVAL — mejorar la legibilidad del número grande.**
Hoy `formatter.py` muestra `MERVAL: {valor:.0f}` sin separadores (ej. `1714487`). Capi pidió separarlo en miles para que se lea mejor (referencia visual: cómo Bull Market presenta sus cotizaciones — números grandes con separador de miles, formato argentino). Usar separador de miles con punto, formato argentino (`1.714.487`, no `1,714,487`) — un helper de formateo de miles compartido, reutilizable si en el futuro otro campo grande lo necesita (ej. si se suma un índice en pesos).

**No tocar en esta tarea:** contenido/tono de los mensajes de efemérides o lección, horarios, ni ninguna de las tandas — es puramente presentación de datos.

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

## Decimoctava tarea — pivot de enfoque: de "reporte de mercado" a "central de noticias económicas" (2026-07-22, investigación de Cowork, para la próxima sesión)

Capi planteó un cambio de fondo (no un ajuste chico): quiere que el canal cubra economía y finanzas en general, no solo mercado bursátil/cambiario. Lo de hoy (dólar, MERVAL, riesgo país + contexto macro con IA) está bien como base, pero es insuficiente para ese objetivo más amplio. Pidió avanzar en 3 ejes a la vez: más datos duros de economía real, más fuentes institucionales, y reestructurar el formato del mensaje para que economía general tenga su propio lugar (no sea un agregado pegado al reporte bursátil). Investigación hecha por Cowork el 2026-07-22, nada implementado todavía.

**A. Fuentes institucionales — revisitado (última vez en la Séptima tarea, 2026-07-08).**

- **BCRA: hay novedad real.** Desde entonces el BCRA lanzó un catálogo de APIs oficiales propio (`bcra.gob.ar/en/central-bank-api-catalog`), sin token, con 5 APIs: Estadísticas Cambiarias, Estadísticas Monetarias (v4, "incluye Informe Monetario Diario"), Cheques Denunciados, Central de Deudores, Régimen de Transparencia. Esto es distinto de `estadisticasbcra.com` (la fuente no oficial que ya sabemos que tiene el MERVAL congelado desde 2024) — es la fuente primaria del propio Banco Central. Útil para reservas internacionales, base monetaria, tasas de referencia (LELIQ/pases) — datos de economía real que hoy el canal no toca. **No resuelve el MERVAL** (no es un dato que publique el BCRA), pero abre una fuente confiable para todo lo demás de política monetaria. Documentación técnica: manual de desarrollo en PDF por cada API, linkeado desde esa misma página.
- **CNV: sigue sin API/RSS de comunicados.** Solo catálogos estáticos en XLSX/JSON vía `argentina.gob.ar/cnv/transparencia/catalogos-de-datos-abiertos` (datos de transparencia institucional, no comunicados/noticias en tiempo real) — no sirve para un pipeline diario automatizado. Mismo resultado que la Séptima tarea: queda afuera.
- **INDEC: no tiene RSS, pero hay una vía nueva no evaluada antes — la API Series de Tiempo de `datos.gob.ar`.** Es un servicio de la Jefatura de Gabinete (`argentina.gob.ar/datos-abiertos/api-series-de-tiempo`) que agrega más de 30.000 series de tiempo de organismos nacionales, incluido INDEC — IPC, comercio exterior, actividad económica (EMAE), entre otros. No es RSS de noticias, es consulta de series estructuradas (JSON/CSV) vía `apis.datos.gob.ar/series/api/series/?ids=<serie_id>`. **Falta el paso concreto que hicimos con dolarapi/argentinadatos en su momento:** identificar los IDs de series específicas que interesan (IPC nacional, EMAE, comercio exterior) y validarlas con una consulta real — no alcanza con saber que la API existe, hay que confirmar que trae lo que promete antes de construir nada.

**B. Datos duros de economía real — más allá de lo ya anotado en la Decimocuarta tarea (inflación, sigue sin implementar).**

Revisé el índice completo de `argentinadatos.com` (la misma fuente que ya usamos para riesgo país/UVA) — trae más de lo que el canal usa hoy:
- **REM (Relevamiento de Expectativas de Mercado)** — encuesta del BCRA a analistas privados con proyecciones de inflación, tipo de cambio, tasa, PBI. Es información *prospectiva* (qué espera el mercado que pase), distinto de todo lo que el canal muestra hoy (que es todo retrospectivo/actual). Endpoint: `GET /v1/finanzas/rem` y `GET /v1/finanzas/rem/ultimo`. Encaja bien con el objetivo de "central de noticias" — es contenido genuinamente nuevo, no otro número de mercado.
- **Tasas de plazo fijo, depósitos a 30 días, cuentas remuneradas en USD** — relevante para "qué hacer con los ahorros", ángulo de economía cotidiana que hoy el canal no toca (todo lo actual es de mercado/trading).
- **Letras capitalizables (LECAP/BONCAP)** — más específico de mercado, no suma al objetivo de "economía general", queda para más adelante si se prioriza el ángulo inversor.
- **No hay salario mínimo, vital y móvil ni canasta básica en argentinadatos.com** (se había anotado en la Decimocuarta tarea como pendiente de fuente) — quedan sin resolver todavía; la API Series de Tiempo de datos.gob.ar (punto A) es el próximo lugar a revisar para esto, no confirmado aún.
- La Decimocuarta tarea (inflación mensual/interanual, viable con la misma fuente) **sigue sin implementarse** — es el punto de partida más directo y ya especificado, antes de sumar REM o tasas.

**C. Propuesta de reestructuración del mensaje — separar "Mercado" de "Economía".**

Hoy la estructura es: 💵 Dólar → 📊 Índices (MERVAL + riesgo país) → 📰 Contexto macro (síntesis de noticias con IA) → Fuente → Disclaimer. Todo lo que no es "Contexto macro" es mercado/cambiario — no hay una sección de datos duros de economía real, y por eso agregar inflación o REM ahí adentro se sentiría forzado.

Propuesta (a confirmar con Capi antes de que Code la implemente): sumar una sección nueva entre "📊 Índices" y "📰 Contexto macro", con nombre tentativo **"📈 Economía"** (o "📉 Indicadores", a definir el tono), que agrupe los datos duros no bursátiles: inflación (Decimocuarta tarea), REM cuando esté listo, y más adelante lo que salga de la API de BCRA/series de tiempo. Mantiene el mismo criterio de frescura relativa y no bloqueante que ya usa todo el resto del mensaje — si no hay dato nuevo ese día (ej. inflación es mensual), no se repite como "novedad" en cada tanda, mismo criterio ya establecido en la Decimocuarta tarea. El "Contexto macro" (síntesis de noticias con IA) queda como está, como cierre narrativo — pero al tener más datos duros de economía real disponibles, el prompt de `macro_summary.py` los puede citar con más precisión en vez de depender solo de lo que mencionen los titulares de RSS.

**Orden sugerido para la próxima sesión (a confirmar con Capi, no bloquea nada de lo que ya funciona):**
1. Cerrar la Decimocuarta tarea (inflación) — ya especificada, es la base de la sección nueva.
2. Sumar la sección "📈 Economía" en `formatter.py` con inflación adentro (aunque sea con un solo dato al principio).
3. Sumar REM (`rem.py`, mismo patrón que `riesgo_pais.py`/`inflacion.py`) a esa sección.
4. Validar concretamente los IDs de series de INDEC en la API de `datos.gob.ar` (con `curl`, mismo criterio que se usó para validar los RSS) antes de prometer nada de esa fuente.
5. Revisar la API oficial del BCRA (punto A) para reemplazar o complementar el uso de `estadisticasbcra.com`, empezando por reservas/tasas de referencia — no por el MERVAL, que sigue bloqueado en la Decimoséptima tarea (IOL).

**No tocar en esta ronda:** nada de lo que ya funciona (6 tandas, disclaimer, panel, Telegram) — este es un plan de ampliación de contenido, no un rediseño del sistema de envíos.

## Decimonovena tarea — fuentes del exterior (2026-07-22, investigación de Cowork, para la próxima sesión)

Capi pidió, antes de pasarle nada a Code, sumar a la investigación de la Decimoctava tarea fuentes de afuera de Argentina — la economía real del país está atada al contexto global (commodities, Fed, Brasil), y hoy el canal no tiene ningún dato duro de eso, solo lo que se cuela en el resumen de IA si algún titular local lo menciona.

**A. Commodities agrícolas (soja/maíz/trigo) — relevante porque son el principal ingreso de dólares del país.**
No encontré una API pública gratuita y sin registro con el mismo patrón de bajo esfuerzo que dolarapi.com. La fuente más seria es la **API de Índices MtR de A3 Mercados/MATba-Rofex** (`matbarofex.com.ar/Indices-mtr/documentacion`) — I.SOJA, I.MAIZ, I.TRIGO — pero es vía WebSocket y probablemente requiere registro/autorización, no confirmado como abierta sin trámite. Alternativas de solo lectura web (PrecioGrano.com.ar, Agrofy News, Rosario Finanzas) no tienen API documentada, solo páginas — requerirían scraping, mismo criterio que ya descartó a INDEC/CNV en la Séptima tarea. **Queda sin resolver**, es el hueco más grande de esta ronda porque es el commodity más relevante para Argentina.

**B. Índices de Wall Street (S&P 500, Dow Jones, Nasdaq) — relevante porque la tanda de las 22:30 ya menciona "Wall Street cerrado" en el resumen de IA, pero sin ningún dato duro propio.**
No hay una API 100% gratuita y sin key con buen límite diario. Dos caminos viables, ninguno ideal:
- **Stooq.com**: descarga CSV sin key, pero con límite diario bajo no documentado con precisión ("Exceeded the daily hits limit" reportado por otros usuarios) — con 1 consulta/día (una tanda) probablemente alcanza, pero no está garantizado.
- **Alpha Vantage** (u otro proveedor con free tier tipo Twelve Data): requiere key gratis, límites de pocas decenas de consultas/día — sobra para 1 consulta diaria. Mismo patrón que ya se usa con `BCRA_API_TOKEN`/`ANTHROPIC_API_KEY` (registro + secret de Actions).
Ninguna de las dos es "gratis sin key" como dolarapi.com; si se prioriza este dato, la vía más simple es Alpha Vantage con key gratuita.

**C. FRED (Federal Reserve Economic Data, EE.UU.) — la más sólida de todas las nuevas.**
API oficial de la Reserva Federal de St. Louis, gratis, requiere key gratuita (alta inmediata, sin trámite largo — `fredaccount.stlouisfed.org/apikeys`), **800.000+ series** de EE.UU.: inflación, tasa de la Fed, PBI, empleo. Es el dato macro global con más impacto indirecto sobre Argentina (suba de tasa de la Fed = presión sobre emergentes) y hoy no está en el canal en ningún formato, ni siquiera vía noticias. Mismo patrón de key gratuita que Alpha Vantage.

**D. Brasil — no estaba en el radar de rondas anteriores, y es el principal socio comercial de Argentina.**
El Banco Central de Brasil tiene un **portal de datos abiertos propio, gratis, sin key** (`dadosabertos.bcb.gov.br`), con Swagger documentado: cotización del dólar (PTAX, histórico desde 1984) y datos de la tasa Selic. Mismo nivel de calidad/confiabilidad que la nueva API oficial del BCRA argentino (punto A de la Decimoctava tarea). Un Real competitivo/débil frente al dólar afecta directamente la competitividad de las exportaciones argentinas a Brasil — dato con lectura económica real, no solo curiosidad.

**E. World Bank / IMF — sirven para contenido de fondo, no para el reporte diario.**
Ambas son gratis y sin key (`api.worldbank.org/v2/...`, IMF World Economic Outlook), pero los datos son anuales o de baja frecuencia (PBI, pobreza, proyecciones a 5 años) — no tiene sentido consultarlas en una tanda diaria porque el valor no cambia día a día. Mejor encaje: alimentar contenido ocasional (ej. la lección educativa de las 12:00, o un futuro "resumen semanal/mensual" ya anotado como idea en la Octava tarea) en vez de una sección de datos diarios.

**F. Petróleo (WTI/Brent) — relevante para Vaca Muerta y la balanza energética.**
Sin opción gratuita sin key. La más accesible es OilPriceAPI, con key gratuita y 100 consultas/mes en el free tier — de sobra para 1 consulta/día (30/mes). Mismo patrón que Alpha Vantage/FRED: registro simple, no es un trámite largo como IOL.

**Resumen para decidir prioridad (a confirmar con Capi antes de pasarle nada a Code):**
- **Gratis y sin key, mismo nivel de fricción que lo que ya existe:** Brasil (BCB) — el más directo de sumar.
- **Gratis pero con key de alta inmediata (mismo patrón que ANTHROPIC_API_KEY):** FRED (el más valioso de este grupo), Alpha Vantage/Wall Street, OilPriceAPI.
- **Sin resolver, requiere más investigación o trámite:** commodities agro (el más importante para Argentina, pero el más difícil de conseguir gratis).
- **No aplican al reporte diario, sí a contenido ocasional:** World Bank, IMF.

**No implementar nada todavía** — mismo criterio que la Decimoctava tarea, esto queda para que Capi decida qué priorizar antes de pasarlo a Code. Ninguna fuente nueva reemplaza nada de lo que ya funciona.
