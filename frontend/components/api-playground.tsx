"use client";

export function ApiPlayground() {
  return (
    <section className="glass-panel rounded-[2rem] bg-slate-950 p-6 text-white">
      <div className="text-xs uppercase tracking-[0.24em] text-slate-400">Operator Notes</div>
      <h2 className="mt-2 font-heading text-2xl font-semibold">Capture signals consistently across every ingestion path</h2>
      <p className="mt-3 max-w-xl text-sm leading-6 text-slate-300">
        Teams can stream individual events, push batched telemetry, or onboard historical records without changing how downstream dashboards and alerts behave.
      </p>

      <div className="mt-5 rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
        <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Direct Event Capture</div>
        <pre className="mt-3 overflow-x-auto text-xs text-sky-200">{`curl -X POST "$API/api/v1/ingest/events/" \\
  -H "X-Api-Key: <org-key>" \\
  -H "Content-Type: application/json" \\
  -d '{
    "event_name": "page_view",
    "properties": {"path": "/pricing", "plan": "growth"}
  }'`}</pre>
      </div>

      <div className="mt-4 rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
        <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Webhook Intake</div>
        <pre className="mt-3 overflow-x-auto text-xs text-emerald-200">{`POST /api/v1/ingest/webhook/<source_uuid>/
X-Webhook-Secret: <source-secret>

{
  "events": [
    {"event_name": "deploy_completed", "properties": {"service": "billing"}},
    {"event_name": "api_error", "properties": {"status_code": 502}}
  ]
}`}</pre>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <div className="rounded-[1.25rem] border border-white/10 bg-white/5 p-4">
          <div className="text-xs uppercase tracking-[0.18em] text-slate-400">API Events</div>
          <p className="mt-2 text-sm text-slate-300">Best for app instrumentation and controlled producer traffic.</p>
        </div>
        <div className="rounded-[1.25rem] border border-white/10 bg-white/5 p-4">
          <div className="text-xs uppercase tracking-[0.18em] text-slate-400">CSV Imports</div>
          <p className="mt-2 text-sm text-slate-300">Useful for backfilling historical records and offline data drops.</p>
        </div>
        <div className="rounded-[1.25rem] border border-white/10 bg-white/5 p-4">
          <div className="text-xs uppercase tracking-[0.18em] text-slate-400">Webhooks</div>
          <p className="mt-2 text-sm text-slate-300">Ideal for third-party systems that emit operational or commercial events.</p>
        </div>
      </div>
    </section>
  );
}
