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

## Cuarta tarea — bugs encontrados revisando los mensajes de 3 días (2026-07-04, prioridad antes de seguir sumando features)

Capi compartió los mensajes reales del 02/07, 03/07 y 04/07. Dos problemas concretos:

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
- **Orden de prioridad confirmado:** Cuarta tarea (bugs) > distribución de Telegram/WhatsApp > recién ahí 3 tandas diarias > redes sociales. El panel (Quinta tarea) y el bot pago (nivel 3) corren en paralelo a todo esto, no bloquean ni son bloqueados.
- Nombre comercial del Despertador: sigue sin definir, no bloquea nada.
