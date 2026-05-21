"use client";

export function ApiPlayground() {
  return (
    <section className="glass-panel rounded-[2rem] bg-slate-950 p-6 text-white">
      <div className="text-xs uppercase tracking-[0.24em] text-slate-400">Integration Notes</div>
      <h2 className="mt-2 font-heading text-2xl font-semibold">Ingestion-ready by API key, webhook, or CSV</h2>
      <p className="mt-3 max-w-xl text-sm leading-6 text-slate-300">
        The backend now supports single event ingestion, batch ingestion, CSV jobs, and webhook receivers secured by source secrets.
      </p>

      <div className="mt-5 rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
        <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Single Event</div>
        <pre className="mt-3 overflow-x-auto text-xs text-sky-200">{`curl -X POST "$API/api/v1/ingest/events/" \\
  -H "X-Api-Key: <org-key>" \\
  -H "Content-Type: application/json" \\
  -d '{
    "event_name": "page_view",
    "properties": {"path": "/pricing", "plan": "growth"}
  }'`}</pre>
      </div>

      <div className="mt-4 rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
        <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Webhook Receiver</div>
        <pre className="mt-3 overflow-x-auto text-xs text-emerald-200">{`POST /api/v1/ingest/webhook/<source_uuid>/
X-Webhook-Secret: <source-secret>

{
  "events": [
    {"event_name": "deploy_completed", "properties": {"service": "billing"}},
    {"event_name": "api_error", "properties": {"status_code": 502}}
  ]
}`}</pre>
      </div>
    </section>
  );
}
