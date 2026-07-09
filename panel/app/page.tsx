import { getEnvios, supabaseConfigurado, type Envio } from "@/lib/supabase";

export const dynamic = "force-dynamic";

function formatearFecha(iso: string): string {
  return new Intl.DateTimeFormat("es-AR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "America/Argentina/Buenos_Aires",
  }).format(new Date(iso));
}

// El mensaje se guarda con tags HTML de Telegram (<b>, <i>). Para el preview los sacamos.
function sinTags(html: string | null): string {
  if (!html) return "";
  return html.replace(/<[^>]+>/g, "");
}

function Tarjeta({ envio }: { envio: Envio }) {
  const anomalias = envio.anomalias ?? [];
  // Qué tanda del día fue este envío (Pre-apertura, Cierre, Efemérides, ...). Viaja dentro
  // del jsonb `datos`; los envíos anteriores a los 6 mensajes diarios no lo tienen.
  const momento = typeof envio.datos?.momento === "string" ? envio.datos.momento : null;
  return (
    <article className="card">
      <div className="card-head">
        <span className="when">{formatearFecha(envio.enviado_at)}</span>
        <span className={`badge ${envio.estado}`}>{envio.estado}</span>
        {momento && <span className="badge canal">{momento}</span>}
        <span className="badge canal">{envio.canal}</span>
      </div>

      {anomalias.length > 0 && (
        <div className="anomalias">
          {anomalias.map((a, i) => (
            <div className="anomalia" key={i}>
              ⚠️ <b>{a.campo}</b> — {a.motivo} (dato al {a.fecha_dato})
            </div>
          ))}
        </div>
      )}

      {envio.error && <div className="anomalia">❌ {envio.error}</div>}

      <pre className="preview">{sinTags(envio.mensaje)}</pre>
    </article>
  );
}

function EstadoVacio({ sinConfig }: { sinConfig: boolean }) {
  return (
    <div className="empty">
      {sinConfig ? (
        <>
          <h2>Falta configurar Supabase</h2>
          <p>
            Definí <code>SUPABASE_URL</code> y <code>SUPABASE_SERVICE_ROLE_KEY</code> en{" "}
            <code>.env.local</code> para ver el historial de envíos.
          </p>
        </>
      ) : (
        <>
          <h2>Todavía no hay envíos registrados</h2>
          <p>La próxima corrida del reporte va a aparecer acá.</p>
        </>
      )}
    </div>
  );
}

export default async function Page() {
  const configurado = supabaseConfigurado();
  const envios = configurado ? await getEnvios() : [];

  return (
    <main className="wrap">
      <header className="top">
        <div>
          <h1>Historial de envíos</h1>
          <div className="sub">Despertador Bursátil · panel de administración</div>
        </div>
        {envios.length > 0 && (
          <span className="count">{envios.length} envíos</span>
        )}
      </header>

      {envios.length === 0 ? (
        <EstadoVacio sinConfig={!configurado} />
      ) : (
        envios.map((envio) => <Tarjeta key={envio.id} envio={envio} />)
      )}
    </main>
  );
}
