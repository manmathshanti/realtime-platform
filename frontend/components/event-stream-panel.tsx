"use client";

import { useLiveStream } from "@/hooks/use-live-stream";

export function EventStreamPanel() {
  const { events, status } = useLiveStream();

  return (
    <section className="glass-panel rounded-[2rem] p-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs uppercase tracking-[0.24em] text-slate-500">Event Stream</div>
          <h2 className="mt-2 font-heading text-2xl font-semibold text-slate-950">Live ingestion tail</h2>
        </div>
        <span className="rounded-full bg-slate-950 px-3 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-100">
          {status}
        </span>
      </div>

      <div className="mt-5 space-y-3">
        {events.map((event, index) => (
          <article key={`${event.event_name}-${event.timestamp}-${index}`} className="rounded-[1.3rem] border border-slate-900/10 bg-white/80 p-4">
            <div className="flex items-center justify-between gap-4">
              <div className="text-sm font-semibold text-slate-900">{event.event_name}</div>
              <div className="text-xs uppercase tracking-[0.16em] text-slate-500">
                {new Date(event.timestamp).toLocaleTimeString()}
              </div>
            </div>
            <pre className="mt-3 overflow-x-auto rounded-2xl bg-slate-950 p-3 text-xs text-sky-200">
              {JSON.stringify(event.properties, null, 2)}
            </pre>
          </article>
        ))}
      </div>
    </section>
  );
}
