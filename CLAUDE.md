# CLAUDE.md — Despertador Bursátil Argentino

Este es el repo de código del producto. El contexto de negocio completo vive en:

- `mvp-despertador-bursatil.md` (esta misma carpeta) — MVP, stack, riesgos, formato del mensaje, arquitectura V2 futura, y la sección "Repo y arranque en Claude Code" con la primera tarea concreta.
- `../CLAUDE.md` — contexto de toda la división bursátil (los otros 2 productos, prioridades, reglas de routing).
- `../../00-comando-central/snapshot-holding-2026.md` — contexto del holding completo, si hace falta.

**Leé `mvp-despertador-bursatil.md` completo antes de escribir código.** Ahí está todo lo decidido: qué entra en el MVP y qué no.

## Resumen ultra rápido para arrancar

- Stack: Python + GitHub Actions (cron) + Claude API (Haiku)
- Fuentes del MVP: dolarapi.com + estadisticasbcra.com (gratis, sin trámite). IOL API opcional/pluggable, no bloqueante — todavía sin aprobar.
- Contenido: dólar + MERVAL/BCRA + resumen macro con IA. **Sin recomendaciones de inversión** (riesgo regulatorio sin resolver).
- Canal: Telegram primero (bot con publicación 8am). WhatsApp (Canal) y el resto, después.
- **No construir panel de administración todavía** — es V2, documentado pero fuera de alcance ahora.

## Primera tarea — hecha (2026-07-02)

Script en Python que pega a dolarapi.com y estadisticasbcra.com, arma el mensaje agrupado por categoría, y lo manda al bot de Telegram. Operativo en producción vía GitHub Actions (cron 8am Argentina). Detalle completo en `PROGRESS.md`.

## Segunda tarea — resumen macro con IA — hecha (2026-07-02)

Sumado al mensaje diario un resumen de 2-4 oraciones del contexto macro, generado con Claude API (`claude-haiku-4-5`), a partir de 3 feeds RSS (Ámbito, Infobae Economía, El Cronista) + los datos duros ya calculados (dólar, MERVAL, brecha). No bloqueante: si falla el fetch o la API, el reporte de dólar + MERVAL se manda igual. Código en `rss_news.py` y `macro_summary.py`. Validado end-to-end local (llegó a Telegram con la sección de contexto macro) y `ANTHROPIC_API_KEY` ya cargada como secret de GitHub Actions. Detalle completo en `PROGRESS.md`.

## Tercera tarea — disclaimer legal (chica, lista para implementar)

Capi trajo un documento de referencia sobre riesgo regulatorio (CNV) y riesgo de baneo de WhatsApp por contenido percibido como "señales de trading". Confirma que el formato actual (datos + eventos fácticos, sin instrucción de compra/venta) está del lado seguro — no bloquea nada de lo ya construido, pero falta sumar el disclaimer fijo al final del mensaje.

Texto exacto a agregar en `formatter.py`, al final del mensaje (mismo criterio no bloqueante que el resto — si por algún motivo falla, no debe frenar el envío):

```
🤖 Alerta automatizada con fines puramente informativos y educativos. No constituye una recomendación de inversión, oferta de compra/venta ni asesoramiento bursátil. Operar bajo su propio riesgo.
```

Detalle completo del hallazgo en `mvp-despertador-bursatil.md`, sección de riesgos.

## Próxima tarea (después de la tercera) — pendiente de definir

Ver "Pendiente de decidir en próxima sesión" en `mvp-despertador-bursatil.md` (fuentes de datos adicionales, Canal de WhatsApp, nombre comercial, etc.). Sin panel, sin IOL, sin sección de recomendaciones con instrumentos específicos — se mantiene el mismo criterio de alcance chico del MVP original.
