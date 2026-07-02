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

## Primera tarea

Script en Python que:
1. Pega a dolarapi.com y estadisticasbcra.com
2. Arma el mensaje con el formato agrupado por categoría (ver mockup en `mvp-despertador-bursatil.md`)
3. Lo manda al bot de Telegram

Sin panel, sin IOL, sin recomendaciones. El MVP más chico que valida la hipótesis.
