# PROGRESS.md

## 2026-07-22 — Duodécima, Decimotercera, Decimocuarta, Decimoquinta y Decimosexta tarea

Ronda de 5 tareas ya especificadas en sesiones anteriores de Cowork, todas validadas con datos
reales antes de commitear (fetch real de dolarapi.com/argentinadatos.com, corrida real de
`generar_resumen_macro` contra Claude Haiku con titulares reales, sin enviar nada a Telegram).
40 tests unitarios pasan (28 previos + 12 nuevos).

**Duodécima tarea — 4 mejoras al mensaje:**
1. `dolar.py`: sumadas `mayorista` y `tarjeta` a `CASAS_RELEVANTES` (dolarapi.com trae 7 casas,
   antes se mostraban 5). `ORDEN_CASAS` en `formatter.py` actualizado: Oficial, Blue, MEP, CCL,
   Mayorista, Cripto, Tarjeta.
2. `_precio_texto()` (nuevo helper en `formatter.py`): 2 decimales cuando la casa los tiene (ej.
   MEP `$1506.40`), sin decimales cuando el valor es entero (ej. Oficial `$1500`).
3. Leyenda de frescura de dolarapi.com (`Datos obtenidos de DolarApi.com... / Actualizado el
   dd/mm/aaaa a las HH:MM`) agregada después del bloque de cotizaciones — toma la fecha/hora más
   reciente entre las 7 casas, convertida a horario de Argentina.
4. `_miles()` (nuevo helper): separador de miles en formato argentino (punto). MERVAL ahora se
   muestra `1.714.487` en vez de `1714487`.

**Decimotercera tarea — legibilidad del resumen de contexto macro:**
`SYSTEM_PROMPT` de `macro_summary.py` reescrito para pedir 2-4 puntos cortos (una sola oración
cada uno, prefijo `• `), no un párrafo corrido. Primera corrida con datos reales dio 3 párrafos
largos con bullet pegado — no era lo pedido; se ajustó el prompt para exigir explícitamente "UNA
sola oración corta (máximo ~25 palabras) — nunca un párrafo" y una segunda corrida confirmó
bullets realmente cortos, uno por idea, sin perder contenido (mismo criterio de "legibilidad, no
recortar información" que pidió Capi). De paso, se sumó `html.escape(texto, quote=False)` al
texto que devuelve Claude antes de insertarlo en el mensaje HTML — sin esto, un titular con `<`,
`>` o `&` podría romper el parseo de Telegram y tirar abajo el envío completo. `quote=False`
porque Telegram sólo exige escapar `&`/`<`/`>`; con `quote=True` (default de `html.escape`)
apóstrofes como en "Moody's" salían literalmente como `Moody&#x27;s` en el mensaje.

**Decimocuarta tarea — inflación mensual/interanual:**
`inflacion.py` (nuevo, mismo patrón que `riesgo_pais.py`): `fetch_inflacion()` trae el último
punto de las series mensual e interanual de argentinadatos.com, cada una no bloqueante por
separado. **Bug encontrado en la fuente al validar con datos reales:** el endpoint documentado
en el CLAUDE.md, `.../inflacion-interanual` (con guiones), devuelve 404 — el endpoint real es
`.../inflacionInteranual` (camelCase), confirmado con `curl`. Corregido en el código antes de
commitear. Sumada la línea `Inflación: 2.1% mensual / 45.3% interanual (dato de mayo 2026)` a
"📊 Índices" (helper `_fecha_mes_anio()` nuevo, con nombres de mes en español) y como dato duro
más en el prompt de `macro_summary.py`. No se compara contra la tanda anterior (es un dato
mensual, no diario), mismo criterio ya establecido para riesgo país.

**Decimoquinta tarea — acreditar las fuentes de noticias:**
El pie del mensaje ahora tiene dos líneas separadas: `Datos: dolarapi.com, estadisticasbcra.com,
argentinadatos.com.` y `Noticias: Ámbito, Infobae, El Cronista, La Nación, Bloomberg Línea.`. Las
fuentes de noticias se toman de `rss_news.FEEDS.keys()` en `main.py` y se pasan como parámetro
(`fuentes_noticias`) a `armar_mensaje()` — **no** se importa `rss_news` directamente desde
`formatter.py`, porque `tests.py` depende explícitamente de que `formatter.py` no tenga
dependencias externas (`feedparser`, en este caso) para poder correr sin instalar nada; importar
`rss_news` ahí rompía esa garantía y tumbaba la suite de tests. Sólo aplica a los mensajes de
datos (lección y efemérides no usan RSS, quedan sin este pie).

**Decimosexta tarea — desfasar los cron:**
Los 4 cron que caían en la hora/cuarto exacto (`0 11`, `0 14`, `0 15`, `0 22`) se corrieron unos
minutos después (`3 11`, `4 14`, `7 15`, `2 22`), siguiendo el desfasaje exacto que ya había
dejado especificado Cowork — para evitar la cola de carga de GitHub Actions en los minutos
redondos. Los otros dos (`15 20`, `30 1`) ya estaban desfasados, sin cambios. **Importante:** el
mapeo de `SCHEDULE` a `MOMENTO` en el `case` del workflow usa el string exacto del cron para
identificar qué tanda es — se actualizó en el mismo commit que el `schedule`, si se desfasan sin
actualizar el `case` el workflow cae al default (`pre_apertura`) en las 4 tandas movidas.

**Housekeeping aparte (mismo día):** se commiteó documentación de sesiones de Cowork que estaba
sólo en el working tree (tareas Duodécima a Decimonovena en `CLAUDE.md`) y el PDF de la auditoría
general (Undécima tarea) que Cowork había dejado en la carpeta sin trackear.

## 2026-07-09 — Undécima tarea: auditoría general del sistema (esfuerzo máximo)

Auditoría de punta a punta de todo lo construido (Primera a Décima tarea): los 15 módulos
Python, los 2 workflows, seguridad/secretos, costos, consistencia de producto y el panel.
Todo cambio se validó antes de commitear (compilación + 28 tests unitarios nuevos + corrida
con datos reales de todas las fuentes + build del panel). Estructura en los 3 grupos pedidos.

### (a) Bugs reales encontrados y corregidos

1. **Cualquier caída de estadisticasbcra.com tumbaba el envío completo.** `fetch_merval()` se
   llamaba sin protección en `main.py` — un 403 (ya pasó una vez, ver 2026-07-02) o un
   `BCRA_API_TOKEN` ausente cancelaban todo el reporte, cuando `formatter` ya sabe armar el
   mensaje sin MERVAL. Ahora es no bloqueante: si falla, el reporte sale sin esa línea. Con esto
   se cierra la pregunta de la auditoría "¿de verdad ningún fetch individual puede tirar abajo
   el envío?": ahora **solo** la caída de dolarapi.com (el dato central) detiene el envío; MERVAL,
   riesgo país, RSS y el resumen con IA son todos no bloqueantes.
2. **Una casa faltante o con precio nulo en dolarapi.com crasheaba el pipeline.**
   `calcular_brecha_mep_oficial` hacía `dolares["oficial"]["venta"]` sin chequear (KeyError si la
   fuente no trae esa casa) y el formateo `:.0f` tiraba TypeError si `venta` venía null. Ahora:
   `fetch_dolares` filtra casas con valores no numéricos, la brecha devuelve `None` si faltan sus
   casas, y el mensaje omite el "Destacado del día" en ese caso — el resto del reporte sale igual.
3. **La variación "· día" del cierre podía comparar contra otro día.** Si la pre-apertura de hoy
   fallaba, `inicio_dia.json` quedaba con los datos de ayer (o más viejos) y el cierre mostraba
   una variación "del día completo" falsa. El snapshot ahora guarda la fecha (ART) y el cierre lo
   ignora si no es de hoy. (Mismo espíritu que el Bug A de la Cuarta tarea: nunca mostrar una
   variación engañosa.)
4. **Un feed RSS colgado podía demorar el envío horas.** `feedparser.parse(url)` descarga con
   urllib **sin timeout**; un feed que no responde bloqueaba la corrida hasta el timeout del job
   de Actions (6 horas). Ahora cada feed se baja con `requests` (timeout 10s) y si uno falla se
   sigue con los demás. Validado en vivo: los 5 feeds siguen entregando (173 titulares).
5. **El bot token podía filtrarse a los logs (seguridad).** La URL de la API de Telegram lleva el
   token adentro, y tanto `raise_for_status()` como las excepciones de red de `requests` incluyen
   la URL en su mensaje → un envío fallido habría impreso el token en el traceback. **El repo es
   público** (verificado vía API de GitHub), así que esos logs de Actions son visibles; GitHub
   enmascara los secrets registrados, pero no hay que depender de una sola capa.
   `telegram_client.py` ahora sanitiza ambos caminos de error (nunca propaga la URL).

### (b) Mejoras aplicadas directamente (bajo riesgo)

1. **Disclaimer legal en los 6 mensajes** (ítem 5 de la auditoría): la lección educativa y las
   efemérides llevaban textos cortos propios, no el disclaimer de la Tercera tarea. El texto legal
   se extrajo a una constante compartida (`formatter.DISCLAIMER`) y ahora cierra los 6 mensajes.
   Las efemérides conservan además su atribución "Datos históricos vía Wikipedia".
2. **Las corridas fallidas ahora quedan registradas en Supabase** con `estado="error"` y el motivo.
   Antes el panel tenía el badge de error pero ningún fallo llegaba a la tabla (si algo crasheaba,
   no se registraba nada). `main.py` registra el error y **re-lanza** — el run de Actions sigue
   marcándose rojo, no se pierde visibilidad. Aplica también al caso "contenido no generado, no se
   envía nada", que antes quedaba solo en los logs.
3. **El panel muestra la tanda de cada envío** (badge con `datos.momento`): con 6 mensajes/día el
   historial era indistinguible. Tolera envíos viejos sin ese campo. `npm run build` OK.
4. **28 tests unitarios nuevos (`tests.py`)** sobre la lógica más frágil y más retocada: parseo de
   fechas/zonas, frescura relativa, variaciones (%, pp, colores invertidos), brecha con casas
   faltantes, armado del mensaje (destacado condicional, "· día" solo en cierre, MERVAL congelado,
   riesgo país sin flecha, disclaimer al final), agrupador de titulares y momentos. Corren sin
   red y sin API keys (`python -m unittest tests`). **Workflow de CI nuevo** (`tests.yml`) en cada
   push/PR — separado del reporte diario a propósito: un test fallido avisa pero jamás bloquea un
   envío de producción.
5. Higiene menor de tipos: `brecha_mep_oficial` es ahora `float | None` en las firmas que la
   reciben (macro_summary), coherente con el fix (a)2.

### Workflow y seguridad — auditados, sin hallazgos pendientes

- **`daily-report.yml`:** los 6 cron ↔ horario argentino verificados uno a uno (11→8:00, 14→11:00,
  15→12:00, 20:15→17:15, 22→19:00, 01:30→22:30 del día anterior ART). `concurrency` serializa
  corridas solapadas sin cancelarlas. Si una corrida falla a mitad de camino, el paso de commit
  del snapshot no corre y el repo no queda en estado raro (el runner es efímero; lo único que se
  perdía era el caso del `inicio_dia`, cerrado en (a)3). `git pull --rebase --autostash` cubre la
  divergencia con el remoto entre tandas.
- **Secretos:** sin keys hardcodeadas en ningún módulo (barrido con grep); ningún `print` expone
  valores sensibles; `supabase_log.py` sigue mandando la `service_role` key solo en headers
  (nunca en URLs ni en mensajes de error) y el panel la usa solo server-side. Único hallazgo real:
  el token de Telegram en excepciones, corregido en (a)5.

### Costo real de Haiku con 6 mensajes/día (ítem 4 — ahora con número)

Precios vigentes de `claude-haiku-4-5`: **US$1 por millón de tokens de entrada, US$5 por millón
de salida.** Con los tamaños medidos en las validaciones reales de esta semana:

| Mensaje | Corridas/día | Input aprox. | Output aprox. |
|---|---|---|---|
| Reporte de datos (resumen macro) | 4 | ~1.500 tokens | ~250 tokens |
| Lección educativa | 1 | ~120 tokens | ~350 tokens |
| Efemérides | 1 | ~1.300 tokens | ~400 tokens |

Diario: ~7.400 in + ~1.750 out. Mensual (30 días): ~222k in (US$0,22) + ~53k out (US$0,26) ≈
**US$0,48/mes**. Incluso duplicando los tamaños queda debajo de US$1/mes — "despreciable"
confirmado, ahora con número para el control de costos del panel.

### (c) Hallazgos que requieren decisión de Cowork/Capi (no se tocó nada)

1. **La brecha puede mezclar un oficial rezagado con un MEP fresco.** El oficial de dolarapi.com
   suele venir con lag (Cuarta tarea); la brecha se calcula igual con el último valor disponible,
   así que en esos días el número puede sobre/subestimar la brecha real del momento. Opciones:
   marcarla `(al dd/mm)` cuando el oficial está rezagado, ocultarla ese día, o dejarla como está
   asumiendo el lag. Es exactamente la misma familia de decisión que el MERVAL congelado.
2. **El riesgo país queda fuera de `detectar_anomalias` a propósito.** Su lag de 1-2 días hábiles
   es normal (publicación diaria hábil); incluirlo con el criterio actual generaría una falsa
   alarma todos los días en el panel. Si se lo quiere vigilar, necesita un umbral propio (ej.
   alertar recién con >3 días hábiles de atraso).
3. **Límite de Telegram: 4.096 caracteres por mensaje.** El reporte actual usa ~700-1.500; lejos
   del límite, pero si algún día se agranda el resumen macro o se suman secciones, `sendMessage`
   fallaría. Anotado como límite de diseño, no requiere acción hoy.
4. **La lección educativa rota entre 25 temas** (se repite cada ~25 días). Ampliar la lista es
   decisión de contenido — editar `leccion_educativa.TEMAS` es trivial.
5. **El texto del disclaimer es idéntico en los 6 mensajes** por consistencia con la Tercera
   tarea. Si para efemérides/lección se prefiere una variante más suave ("contenido educativo…"
   en vez de "operar bajo su propio riesgo"), es un cambio de texto de un minuto.
6. Arrastrados ya conocidos: MERVAL congelado de 2024 (ocultar vs. fuente nueva), pegado manual
   del mensaje fijado/descripción del canal, deploy del panel a Vercel, nombre comercial.

**Nota para Cowork:** esta sección está escrita para servir de base directa del PDF que pidió
Capi (título, subtítulos y los 3 grupos). El detalle técnico de cada fix está en el diff del
commit correspondiente.

## 2026-07-09 — Sexta tarea (parte C): 4 tandas diarias ancladas al mercado

**Qué se hizo:** el reporte pasó de 1 envío diario a **4 tandas**, cada una con su propio
título, emoji y enfoque de resumen macro, para que no repitan el mismo texto genérico sino que
aporten algo propio del momento. Horarios anclados a la rueda real de BYMA (10:30–17:00 ART)
más una tanda nocturna:

| Tanda | Hora ART | Cron (UTC) | Enfoque |
|---|---|---|---|
| 🌅 Pre-apertura | 08:00 | `0 11 * * *` | Cierre de ayer + agenda del día |
| 🔔 Apertura | 11:00 | `0 14 * * *` | Primeros movimientos de la rueda |
| 🌇 Cierre | 17:15 | `15 20 * * *` | Cómo cerró la rueda local |
| 🌙 Balance del día | 22:30 | `30 1 * * *` | Wall Street cerrado + balance de la jornada |

> **La tanda de las 22:30 la pidió Capi (2026-07-09)**, sumada a las 3 que había propuesto
> Cowork (8:00 / 11:00 / 17:15). **Cowork: tenerla en cuenta** en todo lo que planifique de acá
> en más (redes/nivel 1, panel, encuestas, mensaje educativo diario, etc.): ahora son 4 momentos,
> no 3.

**Cómo quedó implementado:**
- **`momento.py` (nuevo):** define los 4 momentos (emoji, título, subtítulo y `enfoque_macro`
  —la instrucción que se le pasa a Claude para que el resumen sea coherente con la tanda—). Si
  la clave llega vacía o desconocida, cae en `pre_apertura` (un envío nunca falla por un
  `MOMENTO` mal seteado).
- **Workflow (`daily-report.yml`):** 4 entradas de cron + un paso que mapea el cron que disparó
  la corrida (`github.event.schedule`) al momento, pasado por env var (no interpolado en el
  script, para no abrir inyección de shell). `workflow_dispatch` ahora tiene un input `momento`
  (choice) para disparar cualquier tanda a mano. Sumado `concurrency` + `git pull --rebase
  --autostash` antes del push del snapshot, para que dos tandas no se pisen al commitear.
- **`formatter.py`:** encabezado según el momento. Además **fix de un bug latente**: la fecha se
  toma ahora en horario de Argentina (`datetime.now(ARG_TZ)`), no del runner —la tanda de las
  22:30 ART corre a la 01:30 UTC del día siguiente y `date.today()` habría impreso la fecha de
  mañana—.
- **`macro_summary.py`:** `generar_resumen_macro()` acepta `enfoque` y lo antepone al prompt.
- **`main.py`:** lee `MOMENTO` del env, lo cablea al resumen, al mensaje y al registro de
  Supabase (guarda el `momento` dentro del jsonb `datos`, sin cambiar el esquema de la tabla).

**Nada requiere acción manual:** los 4 cron ya viven en el workflow; no hay que tocar nada en
GitHub más allá de que ya estaban los secrets. No se tocó de dónde salen los datos (dolarapi.com
/ estadisticasbcra.com siguen igual).

**Validado (2026-07-09):** compilan todos los módulos; corrida local con **fetch real** de dólar
+ MERVAL (sin enviar a Telegram) renderizó las 4 tandas con encabezados distintos y la lógica de
frescura intacta (MERVAL marcado `(al 30/08/2024)` sin flecha). El envío real por cada cron se
confirma en las próximas corridas automáticas (mismo criterio que se usó para el MVP original).

**Decisiones / puntos para Cowork y Capi (no bloquean, pero conviene definir):**
1. **La flecha de variación ahora compara contra la tanda anterior, no contra el día anterior.**
   El snapshot se guarda en cada corrida, así que apertura compara vs. pre-apertura, cierre vs.
   apertura, etc. (para el dólar que sí se mueve intradía: blue/MEP/CCL). Es coherente con un
   producto de varias tandas ("qué se movió desde el último reporte"), pero **es un cambio de
   comportamiento respecto del reporte único día-a-día** — si se prefiere otra base de
   comparación (ej. siempre contra el cierre del día anterior), es una decisión de producto a
   tomar.
2. **La tanda de las 22:30 aporta poco dato de precio nuevo** (a esa hora BYMA y Wall Street ya
   cerraron; MEP/CCL casi no operan post-cierre). Su valor está sobre todo en el **resumen macro**
   (balance del día + cierre externo), no en números frescos — tenerlo en cuenta al pensar el
   contenido de esa tanda. Ver también: el mensaje educativo/efeméride diario (Octava tarea)
   podría vivir bien acá.
3. Costo: son 4 llamadas a Haiku/día en vez de 1 — sigue siendo prácticamente nulo, pero queda
   anotado (se conecta con el "control de costos" del panel).

## 2026-07-09 — Séptima tarea: de 3 a 5 fuentes + deduplicación/priorización

**Qué se hizo:** se sumaron 2 fuentes de noticias (5 en total) y, como el propio análisis de la
Séptima anticipaba, a partir de ~5 fuentes se agregó una capa de **deduplicación y priorización**
antes de mandarle los titulares a Claude, para que la síntesis no se diluya con docenas de
titulares crudos.

**Fuentes: validadas con `curl` + `feedparser` (mismo proceso que las 3 originales).**
- **Sumadas** (RSS válido, con ítems recientes en 24hs): **La Nación Economía** (feed Arc, 58
  ítems/24hs) y **Bloomberg Línea** (feed Arc, 25 ítems/24hs). Ambas Arc, el mismo patrón
  confiable que ya usaban Infobae/Cronista.
- **Descartadas tras probarlas:** Clarín economía (el feed viene sin ítems reales, solo el título
  del canal), Perfil (no tiene feed de economía; solo `/feed` general, demasiado ruidoso para un
  reporte de mercados), BAE Negocios (sin RSS que responda), INDEC (devuelve HTML, no RSS) y BCRA
  (404). Las institucionales quedan afuera por el mismo criterio ya aplicado a CNV/FCI: sin RSS
  público confirmado, no se scrapea.

**Deduplicación/priorización — `agrupador.py` (nuevo, solo stdlib):**
- `agrupar_titulares()` agrupa los titulares que cubren el mismo evento (varios medios sobre la
  misma noticia) comparando sus términos significativos (minúsculas, sin acentos, sin stopwords,
  4+ letras; solapamiento ≥ 0.5 sobre el titular más corto) y **ordena por frecuencia entre
  fuentes**: si varios medios distintos cubren lo mismo el mismo día, es señal barata de que es
  relevante.
- `macro_summary._armar_prompt()` ahora le pasa a Claude los **grupos ya deduplicados y
  ordenados** (top 20, `MAX_GRUPOS_PROMPT`, para acotar tokens), anotando entre corchetes cuántos
  medios cubren cada evento e instruyéndolo a priorizar los más cubiertos. `fetch_titulares` y
  `main.py` no cambiaron: la priorización ocurre justo antes de armar el prompt.

**Validado (2026-07-09) con datos reales:**
- Fetch real de las 5 fuentes: **172 titulares crudos → 140 grupos**, 11 eventos multi-fuente. El
  ranking puso arriba lo genuinamente importante (visita de Georgieva/FMI y plazo fijo con 4
  medios cada uno; reservas del BCRA, inflación CABA, proyección del FMI con 2).
- **Una** llamada real a Haiku con el prompt nuevo (sin enviar a Telegram): el resumen priorizó
  esos eventos, en rioplatense, sin recomendaciones. Costo: ~1.440 tokens de input / 200 de
  output — nulo (con 4 tandas/día sigue siendo despreciable).

**Sin dependencias nuevas** (el agrupador es stdlib puro; `requirements.txt` no cambia).

**Para Cowork / Capi (no bloquea):**
1. **Actualizar el texto del mensaje fijado y la descripción del canal** (borradores de la Sexta
   tarea, sección B): hoy listan "Ámbito, Infobae, El Cronista" — ahora también están La Nación y
   Bloomberg Línea. Conviene sumarlas o poner "entre otras".
2. El pie del mensaje (`formatter.py`) sigue acreditando solo las fuentes de dato duro
   (dolarapi.com, estadisticasbcra.com); las de noticias alimentan el "Contexto macro" pero no se
   listan ahí para no ensuciar cada envío con 5 medios. Si se quiere acreditarlas, es decisión de
   contenido.
3. Límite de mantenimiento ya conocido: cada feed es un punto más de falla si cambia de URL, pero
   el diseño no bloqueante lo mitiga (si un feed cae, el resto sigue y el reporte sale igual).

## 2026-07-09 — Octava tarea (casi gratis): cripto en el mensaje

Sumada la cotización **Cripto** (dólar cripto/USDT) a la sección "💵 Dólar", después de CCL.
dolarapi.com ya la devuelve en el mismo endpoint (`casa: "cripto"`), así que fue agregar la casa
al fetch (`dolar.py`) y al orden de renderizado (`formatter.py`) — sin integración nueva. La
lógica de frescura y la flecha de variación la toman sola (tiene `fecha_origen` y entra al
snapshot como cualquier otra casa; la flecha aparece a partir de la segunda corrida, cuando el
snapshot ya la tiene). Validado con fetch real: `Cripto: compra $1558 / venta $1560`.

**Resto de la Octava tarea — pendiente de definición de contenido con Capi (no es solo código):**
glosario para principiantes, encuestas nativas de Telegram y el mensaje educativo/efeméride
diario requieren decidir contenido/cadencia/ubicación (¿mensaje aparte o sección de una tanda?)
antes de implementar. La cripto era el único ítem "casi gratis" 100% especificado y autónomo.

## 2026-07-09 — Octava tarea (más trabajo): riesgo país como dato duro

Sumado el **riesgo país** como dato propio en la sección "📊 Índices", al lado del MERVAL. En la
investigación original de fuentes había quedado sin resolver por falta de API gratuita; ahora se
usa **argentinadatos.com** (`/v1/finanzas/indices/riesgo-pais`, gratis, sin key), que además
sirve la serie histórica para calcular la variación (últimos dos puntos, igual que el MERVAL).

- `riesgo_pais.py` (nuevo): `fetch_riesgo_pais()` → `{valor, variacion_pct, fecha_origen}`.
- `main.py`: fetch **no bloqueante** (si falla, el reporte sale igual), cableado al mensaje, al
  resumen macro (antes el riesgo país solo aparecía si algún titular lo mencionaba) y al registro
  de Supabase.
- `formatter.py`: se muestra `Riesgo país: 405 pts (-0.7%) (al 07/07)`. **Sin flecha de color** a
  propósito: en riesgo país bajar es "bueno", así que el verde/rojo (pensado para precios, donde
  subir es verde) confundiría — va la variación neutra. La fecha `(al dd/mm)` aparece porque el
  riesgo país se publica por día hábil y suele venir 1-2 días detrás del dólar intradía (mismo
  criterio de frescura que el resto). Pie de "Fuente" actualizado con argentinadatos.com.
- Validado con datos reales: `Riesgo país: 405 pts (-0.7%) (al 07/07)`, conviviendo con el MERVAL
  en Índices, y presente en el prompt de la IA. Sin dependencias nuevas.

## 2026-07-09 — Novena tarea (A-D): de 4 a 6 mensajes diarios

Implementadas las 4 respuestas de Capi. El sistema pasa a **6 mensajes/día**:
`8:00 pre-apertura → 11:00 apertura → 12:00 lección educativa → 17:15 cierre → 19:00 efemérides
→ 22:30 panorama del día`.

**A. Tanda 22:30 — panorama general del día (no solo mercados).** Se amplió el `enfoque_macro`
de `cierre_global` en `momento.py`: ahora pide un panorama de todo lo que pasó (incluidas
decisiones políticas/medidas que afecten la economía), no solo el cierre de precios. Título de la
tanda: "Panorama del día".

**B. Cierre (17:15) también compara contra el inicio del día (8:00).** La pre-apertura graba un
`data/inicio_dia.json` (nuevo snapshot en `snapshot.py`); la tanda de cierre lo carga y muestra,
por campo de dólar, una segunda cifra `· día ±X%` (variación del día completo) además de la
variación contra la tanda anterior. `obtener_momento` devuelve la clave resuelta para que
`main.py` sepa cuándo grabar/leer. El workflow ahora commitea todo `data/`.

**C. Variación en % en todos los campos de dólar.** Antes el dólar solo tenía flecha; ahora
muestra también el número (`🔴▼ (-0.3%)`), como el MERVAL. Helper `_variacion_texto` en
`formatter.py`. *Nota:* el destacado de brecha se dejó con solo la flecha a propósito — su
"variación" son puntos porcentuales de una brecha, no un %, y mostrar "(+0.3%)" ahí confundiría.
Si Capi lo quiere igual, se agrega como "pp".

**D. Dos mensajes nuevos de contenido (12:00 lección, 19:00 efemérides).** `main.py` bifurca por
`tipo` de momento (`datos` vs `contenido`). Mecanismo elegido por Code (el CLAUDE.md lo dejó a
criterio) priorizando la credibilidad:
- **Lección educativa (`leccion_educativa.py`):** un concepto de economía/finanzas explicado por
  Haiku en 2-4 oraciones para principiantes, sin asesoramiento. El tema **rota por fecha** (lista
  de 25 conceptos generales, no atados a Argentina) para no repetir dentro del ciclo.
- **Efemérides (`efemerides.py`):** decisión clave de diseño — **los hechos salen de Wikipedia**
  (feed REST "un día como hoy", gratis, sin key), NO de la memoria del modelo. Haiku solo elige 1
  efeméride argentina (con énfasis) + 1 mundial de esa lista real y las redacta. Así se evita el
  riesgo de que un LLM invente o se equivoque de fecha, que en un canal público dañaría la
  credibilidad.
- `ia.py` (nuevo): helper compartido sobre Haiku. Si la generación falla, el mensaje de contenido
  **no se envía** (el contenido ES el mensaje; no tiene sentido mandarlo vacío) — a diferencia de
  las tandas de datos, donde el resumen macro es opcional y el reporte igual sale.

**Validado (2026-07-09) con generación real:** lección (FCI) coherente y sin asesoramiento;
efemérides del 9/7 correctas y sourced (Congreso de Tucumán 1816 + último recital de Grateful
Dead 1995). Estructura de ambos mensajes OK. Sin dependencias nuevas (Wikipedia y la API de
Claude via `requests`/`anthropic` ya presentes).

**Para Cowork / Capi:**
- Costo: se pasa de 4 a 6 llamadas a Haiku/día — sigue siendo despreciable.
- Los mensajes de contenido también se registran en Supabase (historial del panel).
- Pendiente de contenido menor: afinar la lista de temas de la lección o el tono de las
  efemérides es trivial (editar `leccion_educativa.TEMAS` / los system prompts).

## 2026-07-09 — Décima tarea: variación de la brecha en pp

Cerrado el pendiente que había quedado de la Novena C. La brecha del dólar ahora muestra su
variación en **puntos porcentuales** (diferencia simple contra la tanda anterior), con el sufijo
`pp` para que quede claro que no es un % relativo como el resto de los campos. Ejemplo real:
`Brecha MEP/oficial: 1.4% 🔴▲ (+0.4pp)`.

- Helper `_variacion_brecha_texto` en `formatter.py`, con **colores invertidos** respecto de los
  precios (como pidió Capi en el ejemplo `🔴▲`): brecha más ancha = desfavorable (▲ rojo), más
  angosta = favorable (▼ verde). El resto de los campos (dólar, MERVAL, riesgo país) sigue en %,
  sin cambios.
- Validado con datos reales y casos borde (+/–/0/None).

**Pendiente de acción manual de Capi (no código):** copiar al mensaje fijado y a la descripción
del canal en Telegram el texto de fuentes ya actualizado en el `CLAUDE.md` (suma La Nación,
Bloomberg Línea y argentinadatos.com).

## 2026-07-05 — Cuarta tarea (bugs A+B) + arranque de la Quinta (panel)

**Resumen de la sesión (para Cowork):** se cerraron los dos bugs que Capi detectó revisando los
mensajes reales (datos congelados + el reporte no le llegaba a nadie más que a él) y se arrancó
en paralelo el panel de administración. Todo quedó **commiteado, pusheado a `origin/master` y
validado end-to-end** (envío real al canal + fila real en Supabase + panel leyéndola). Al cierre
faltaban dos acciones manuales de Capi (crear el canal y cargar la key de Supabase): ambas se
hicieron y se validaron en esta misma sesión. Detalle abajo, y el bloque final "Cierre de la
sesión" tiene los archivos tocados, los commits y el estado operativo resultante.

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

**Cerrado (2026-07-05):** canal público `@despertadorbursatil` creado, bot agregado como
admin, `TELEGRAM_CHAT_ID` actualizado (secret de Actions + `.env`). Validado con un envío real:
el reporte se publicó en el canal (HTTP 200, `message_id` 2). El cron de las 8am ya postea ahí.

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

**Cerrado (2026-07-05):** `service_role` key cargada en los secrets de GitHub Actions
(`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`), en el `.env` raíz y en `panel/.env.local`.
Validado end-to-end con la key real: el pipeline insertó una fila en `envios` (verificada en la
DB) y el panel la leyó y renderizó (fecha ART, estado, anomalías y preview). La tabla se dejó
vacía para que producción arranque en limpio; la puebla el próximo envío del cron.

**Pendiente opcional (no bloquea):** deployar el panel a Vercel para no correrlo local.

### Cierre de la sesión — archivos, commits y estado operativo

**Archivos tocados / creados:**
- `dolar.py`, `bcra.py` — capturan `fecha_origen` de cada dato (modificados).
- `formatter.py` — frescura relativa + `detectar_anomalias()` (modificado).
- `main.py` — cablea el registro en Supabase, no bloqueante (modificado).
- `supabase_log.py` — **nuevo**: inserta la fila del envío vía PostgREST.
- `telegram_client.py` — **sin cambios** (el mismo `sendMessage` publica en el canal).
- `.env.example`, `.github/workflows/daily-report.yml` — sumadas envs de Supabase (modificados).
- `README.md` — sección "Distribución: Canal de Telegram" (modificado).
- `panel/` — **nuevo**: app Next.js completa (App Router, `app/`, `lib/supabase.ts`, estilos
  propios light/dark, `.env.local.example`, `.gitignore` propio que excluye `node_modules`/`.next`).

**Commits (todos en `origin/master`, working tree limpio):**
- `534afa5` — Bug A: frescura del dato, sin variación falsa.
- `f24eeb8` — Bug B (Canal de Telegram) + arranque del panel.
- `4235681` — PROGRESS + notas de planificación (Cuarta/Quinta).
- `dcf267d` — Cierre de las 2 acciones manuales (canal + Supabase).

**Credenciales / infra (referencia):**
- Secrets nuevos en GitHub Actions: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`. `TELEGRAM_CHAT_ID`
  pasó del chat privado de Capi a `@despertadorbursatil`.
- Proyecto Supabase: `despertador-bursatil`, ref `kazjrgekyxwloumkkhvu`, región sa-east-1, free
  tier ($0/mes). Tabla `envios` con RLS activa sin policies públicas (acceso sólo server-side con
  la service_role key).
- La `service_role` key vive sólo en los secrets de Actions, en el `.env` raíz (gitignored) y en
  `panel/.env.local` (gitignored). Nunca se commitea ni llega al browser.

**Cómo correr el panel** (para quien lo levante después): `cd panel && npm install && npm run dev`
(con `panel/.env.local` completado a partir de `.env.local.example`). Lee la tabla `envios` de
Supabase server-side y lista los envíos con estado, anomalías y preview. Deploy a Vercel: opcional.

**Estado operativo al cierre de la sesión:**
- El reporte diario se publica solo, cada mañana 8am (AR), en el **Canal de Telegram**
  `@despertadorbursatil` — abierto a cualquier suscriptor. Datos honestos (campos rezagados
  marcados `(al dd/mm)` y sin flecha).
- Cada envío del cron queda **registrado en Supabase** y visible desde el panel.
- La tabla `envios` se dejó **vacía** a propósito; la puebla el próximo envío del cron.

**Pendientes para próximas sesiones (documentados, ninguno bloquea):**
1. Decisión de producto sobre el **MERVAL congelado de 2024** (ocultar la línea vs. buscar fuente
   fresca — IOL / API BCRA). Ver la nota "Pendiente de producto" en el Bug A de arriba.
2. Réplica del contenido al **Canal de WhatsApp** (próximo paso de distribución ya decidido).
3. Escalar a **3 tandas diarias** y luego redes sociales (nivel 1) — según el "Modelo de negocio
   ampliado" del `mvp-despertador-bursatil.md`.
4. Próximas rebanadas del **panel**: gestión de fuentes sin código, métricas de audiencia por
   canal, preview-antes-de-enviar con aprobación, alertas proactivas, interruptor por canal.
5. Deploy opcional del panel a Vercel.
6. Nombre comercial del Despertador (sigue sin definir, no bloquea nada).

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
