# MVP — Despertador Bursátil Argentino

*Definido: 2026-07-01*

## Hipótesis a validar

Hay audiencia argentina real dispuesta a seguir un reporte diario de mercados/dólar/macro con foco local. Antes de monetizar, medir: apertura, retención semana a semana, y qué % pediría más profundidad si fuera pago.

## Decisiones tomadas

| Aspecto | Decisión |
|---|---|
| Canal | Multicanal desde el día 1: Telegram + WhatsApp + X + Instagram + email |
| Precio | Gratis para validar — sin pricing todavía |
| Contenido | Mercados locales (MERVAL, bonos, riesgo país) + acciones/CEDEARs/FCI/cauciones + dólar (oficial/MEP/CCL/blue) + noticias/macro con análisis IA + recomendaciones/oportunidades |

## ⚠️ Dos riesgos a resolver antes de ejecutar

**1. Recomendaciones de inversión = riesgo regulatorio.**
El manual operativo (sección 9, banderas rojas) marca esto como zona sensible. En Argentina, dar "recomendaciones de inversión" al público de forma sistemática puede rozar actividad regulada por la CNV (asesor de inversión registrado). Antes de publicar esa sección:
- Consultar si "análisis de oportunidades" (descriptivo, sin instrucción de compra/venta) alcanza para estar del lado seguro, vs. "recomendación" (prescriptivo).
- Evaluar disclaimer estándar ("esto no es asesoramiento financiero, es análisis informativo") — mitiga pero no elimina el riesgo si el contenido es de facto prescriptivo.
- **Recomendación para el MVP inicial:** arrancar solo con mercados + dólar + macro (sin la sección de recomendaciones), sumar esa parte cuando esté resuelto el marco legal. Queda como decisión tuya, no bloqueo mío.

**2. Multicanal desde el día 1 tensiona con los principios lean del propio manual** (lotes pequeños, WIP limit 3, Build-Measure-Learn antes de escalar). Publicar bien en 4 canales simultáneos con dedicación part-time es alto riesgo de dispersión.
- **Sugerencia de secuencia práctica** (no cambia la decisión "multicanal", solo el orden de implementación): armar el contenido una vez por día → publicar primero en Telegram (canal más rápido de setup, sin fricción de aprobación) → replicar el mismo formato a WhatsApp (mismo texto, canal/lista de difusión) → luego a X/Instagram/email una vez que el formato esté estable, no los 5 al mismo tiempo desde el día 1 literal.

**Nota técnica sobre WhatsApp — decidido:** se usa **Canal de WhatsApp** (no lista de difusión, no Business API). Gratis, sin límite de contactos, el destinatario no necesita tenerte agendado, formato broadcast unidireccional igual que Telegram. Se descartó la lista de difusión (tope de 256 contactos) y la Business API (paga, requiere aprobación de Meta, pensada para volumen/CRM que no aplica a un MVP gratis en validación).

## Fuentes de datos posibles (investigadas hoy)

| Fuente | Cubre | Acceso |
|---|---|---|
| [dolarapi.com](https://dolarapi.com) | Dólar oficial, blue, MEP, CCL, tarjeta, cripto | Gratis, sin registro |
| [estadisticasbcra.com/api](https://estadisticasbcra.com/api/documentacion) | Variación MERVAL, indicadores BCRA | Gratis, requiere API key |
| [IOL (InvertirOnline) API](https://www.invertironline.com/api) | Acciones, CEDEARs, bonos, opciones, **cauciones**, futuros, en tiempo real y históricos | Requiere cuenta + solicitud de acceso |
| [BYMA Open Data](https://open.bymadata.com.ar/) | Cotizaciones oficiales del mercado argentino | Gratis, datos oficiales de la bolsa |
| [CNV — Valores diarios de cuotaparte](https://www.cnv.gov.ar/SitioWeb/FondosComunesInversion/CuotaPartes) | FCI (fondos comunes de inversión), valor de cuotaparte diario | Gratis, sin API pública confirmada — scraping de la página oficial |
| Riesgo país (Ámbito / Rava) | Riesgo país EMBI | Sin API pública confirmada — posible scraping o fuente manual diaria |

**Ruta técnica más simple para el MVP:** dolarapi.com (dólar) + estadisticasbcra.com (MERVAL/BCRA) cubren el contenido macro sin fricción de aprobación. **Para acciones, CEDEARs y cauciones, IOL API es la única fuente encontrada con esa cobertura completa** — requiere pedir acceso a la cuenta, así que conviene solicitarlo ahora para no bloquear el desarrollo más adelante. FCI queda atado a scraping de la página de CNV (sin API oficial confirmada) — es la pieza más frágil técnicamente del set de fuentes.

## Inspiración de diseño (widgets y app de TradingView)

Capi compartió capturas de los widgets de home screen y la app de TradingView (2026-07-01). Patrones a reutilizar en el formato del reporte:

- **Agrupación por categoría**: Dólar / Índices y riesgo país / Acciones y CEDEARs / Cauciones y FCI, en vez de un bloque de texto plano.
- **Color verde/rojo para variación**: escaneo inmediato de qué subió y qué bajó.
- **Un "destacado del día"** arriba del reporte (equivalente al badge 🔥 de la card de noticias de TradingView) — un dato o titular que resuma lo más relevante de la jornada.
- Ícono/logo por instrumento: para fase posterior, no bloquea el MVP de texto.
- Idea a futuro (no MVP): widget nativo tipo el de home screen de TradingView, con un dato único (ej. brecha MEP/oficial) — evaluar cuando el producto tenga tracción.

Mockup del formato actualizado (agrupado + colores + destacado) armado y guardado como referencia visual del reporte.

## Referencia real: canal de WhatsApp "DCF Inversiones" (2026-06-30)

Capi compartió un ejemplo real de mensajes de un canal de noticias de mercado/inversiones. Notas, sin rediseñar el MVP ya definido:

- Confirma el patrón de encabezados por sección con emoji (ya lo tenemos vía agrupación por categoría).
- Tienen una edición "Panorama Semanal" (recap de la semana) — idea para una fase futura, **no suma al MVP ahora**.
- Su sección de "Recomendación" con instrumentos específicos (ej. "LECAP noviembre 2026") **confirma el riesgo regulatorio ya marcado** — ese tipo de contenido específico normalmente lo puede dar un agente registrado en la CNV (ALyC). Refuerza dejar "recomendaciones" fuera del MVP hasta resolver el marco legal.

## Stack técnico propuesto

- Lenguaje/runtime: Python
- Orquestación: cron job — GitHub Actions (`schedule` trigger), gratis, sin servidor propio 24/7
- Datos: dolarapi.com + estadisticasbcra.com
- Análisis: Claude API (Haiku — resumen diario simple, no requiere Opus/Sonnet)
- Distribución inicial: Telegram Bot API (bot propio) + Canal de WhatsApp (posteo manual o herramienta de terceros)
- Hosting del script: GitHub Actions, o Railway/Render free tier si necesita más control
- Repo: por crear (versiona el script, el prompt de análisis y el historial de reportes)

## Caso de uso real

Ana, monotributista en San Rafael, recibe el mensaje en Telegram todas las mañanas a las 8. Ve que la brecha MEP/oficial subió a 27% (la más alta desde marzo) y decide adelantar la conversión de sus ahorros en pesos a MEP antes de que siga subiendo — algo que antes tenía que buscar manualmente en 3 sitios distintos (dólar, MERVAL, riesgo país).

## Próximos pasos concretos

1. Resolver el punto legal de "recomendaciones" (punto 1 arriba) — decisión tuya, puede ser consulta rápida con contador/abogado.
1b. Solicitar acceso a la API de IOL (requiere cuenta + pedido) — es la única fuente encontrada con acciones/CEDEARs/cauciones completos, mejor arrancar el trámite ahora.
2. Armar bot de Telegram mínimo: pull diario de dolarapi.com + estadisticasbcra.com (+ IOL cuando esté aprobado), formato de mensaje fijo, publicación programada (ej. 8am).
3. Definir el resumen de "noticias/macro con análisis IA": qué fuentes de noticias se resumen (¿Ámbito, Infobae Economía, Cronista?) y qué prompt genera el análisis.
4. Crear el Canal de WhatsApp y replicar el mismo contenido de Telegram ahí.
5. Validar el formato con 2 semanas de publicación antes de replicar a los otros 3 canales (X, Instagram, email).
6. Métrica mínima de validación: suscriptores al canal + tasa de apertura/lectura (Telegram lo da nativo; Canal de WhatsApp da conteo de seguidores nativo también).

## Arquitectura V2 (futuro, no MVP): panel de control

**Decisión (2026-07-01):** esto queda documentado como arquitectura objetivo, no se construye ahora. El MVP sigue siendo el script simple (cron + Telegram/Canal de WhatsApp) para validar rápido. El panel se construye recién cuando el Despertador tenga tracción real — evita repetir el error de sumar todo de una antes de validar la hipótesis básica.

**Qué resolvería el panel cuando llegue el momento:**

- Gestión de fuentes de datos: agregar/sacar APIs o feeds sin tocar código (hoy las fuentes están hardcodeadas en el script).
- IA con contexto general de todas las fuentes activas, generando el mensaje diario completo automáticamente (hoy el análisis con Claude API ya existe en el MVP, pero acotado a las fuentes fijas definidas).
- Visibilidad operativa: logs, historial de mensajes enviados, reenvío manual si algo falla.
- Envío automático a los canales configurados, sin intervención manual una vez aprobado el flujo.

**Stack tentativo para cuando se construya** (no confirmar todavía): backend con base de datos (Supabase, coherente con el resto del holding) + frontend simple de administración (Next.js) + el mismo pipeline de Claude API del MVP, pero parametrizado por fuente en vez de hardcodeado.

**Disparador para arrancar el panel:** cuando el Despertador tenga audiencia real y agregar/sacar fuentes a mano en el código empiece a ser fricción genuina — no antes.

## Repo y arranque en Claude Code

**Repo:** `despertadorbursatil` en GitHub (creado 2026-07-01).

**Gitignore:** template de Python — correcto para este stack. El template oficial de GitHub para Python incluye `.env`, `venv/`, `__pycache__/`, etc., así que las claves (Claude API key, credenciales de IOL cuando estén) quedan afuera del repo siempre que se guarden en un archivo `.env` y no hardcodeadas en el código. Verificar una sola vez que el `.gitignore` generado efectivamente tenga la línea `.env` antes del primer commit con claves reales.

**Lo que Claude Code necesita saber para arrancar a programar** (ya documentado en este archivo y en `../CLAUDE.md`, así que no hace falta reexplicarlo en el chat de Code):

- Stack: Python + GitHub Actions (cron) + Claude API (Haiku) — ver sección "Stack técnico propuesto" arriba.
- Fuentes del MVP: dolarapi.com y estadisticasbcra.com (gratis, sin trámite). IOL API queda pendiente de aprobación de cuenta — el código debe poder arrancar sin ella (fuente opcional/pluggable, no bloqueante).
- Contenido del MVP: dólar + MERVAL/BCRA + resumen macro con IA. **Sin sección de recomendaciones** todavía (riesgo regulatorio sin resolver — ver sección de riesgos arriba).
- Canales del MVP: Telegram primero (bot con publicación programada 8am), después Canal de WhatsApp con el mismo contenido. X/Instagram/Email quedan para después de validar el formato.
- Formato del mensaje: agrupado por categoría + colores/flechas de variación + un "destacado del día" arriba — ver el mockup de referencia (sección "Inspiración de diseño").
- Panel de control con gestión de fuentes e IA generando todo automáticamente: **es V2, no construir ahora** — ver sección "Arquitectura V2".

**Primera tarea concreta para Claude Code:** armar el script Python que pega a dolarapi.com + estadisticasbcra.com, arma el mensaje con el formato definido, y lo manda al bot de Telegram. Sin panel, sin IOL, sin recomendaciones — el MVP más chico que valida la hipótesis.

## Pendiente de decidir en próxima sesión

- Fuentes de noticias/macro específicas
- Nombre comercial del Despertador (puede ir junto con el nombre del holding, o ser independiente)
- Fecha de arranque concreta del bot de Telegram
