# Panel — Despertador Bursátil

Panel de administración del reporte diario. Primera rebanada: **Historial de envíos** —qué se
mandó, a qué canal, con qué estado y qué anomalías de datos se detectaron (ej. dólar oficial
congelado o MERVAL de una serie que no avanza)— leído de la tabla `envios` de Supabase.

Stack: Next.js (App Router) + Supabase. La lectura es 100% server-side con la `service_role`
key; nada sensible llega al browser.

## Setup local

1. `npm install`
2. Copiar `.env.local.example` a `.env.local` y completar `SUPABASE_URL` y
   `SUPABASE_SERVICE_ROLE_KEY` (dashboard de Supabase → Project Settings → API).
3. `npm run dev` → http://localhost:3000

## De dónde salen los datos

El pipeline del reporte (`../main.py` → `../supabase_log.py`) inserta una fila en `envios`
después de cada envío, con el mensaje, los datos crudos y las anomalías de frescura. El panel
sólo lee.

## Próximas rebanadas (documentadas, fuera del arranque)

Gestión de fuentes sin tocar código · métricas de audiencia por canal · preview del mensaje
antes de enviar con aprobación manual · alertas proactivas · interruptor por canal.
Ver `../mvp-despertador-bursatil.md`, sección "Arquitectura V2".
