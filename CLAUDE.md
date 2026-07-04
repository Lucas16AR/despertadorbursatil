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

## Próxima tarea (después de la tercera) — pendiente de definir

Ver "Pendiente de decidir en próxima sesión" en `mvp-despertador-bursatil.md` (fuentes de datos adicionales, Canal de WhatsApp, nombre comercial, etc.). Sin panel, sin IOL, sin sección de recomendaciones con instrumentos específicos — se mantiene el mismo criterio de alcance chico del MVP original.
