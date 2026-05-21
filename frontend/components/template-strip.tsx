"use client";

import type { DashboardTemplate } from "@/lib/types";

export function TemplateStrip({
  templates,
  loading
}: {
  templates: DashboardTemplate[];
  loading: boolean;
}) {
  return (
    <section className="glass-panel rounded-[2rem] p-6">
      <div className="text-xs uppercase tracking-[0.24em] text-slate-500">Templates</div>
      <h2 className="mt-2 font-heading text-2xl font-semibold text-slate-950">Starter boards with a real point of view</h2>
      <div className="mt-5 grid gap-4 md:grid-cols-3">
        {(loading ? [] : templates).map((template) => (
          <article key={template.id} className="rounded-[1.5rem] border border-slate-900/10 bg-white/80 p-5">
            <div className="text-xs uppercase tracking-[0.2em] text-slate-500">{template.id.replaceAll("-", " ")}</div>
            <h3 className="mt-3 text-lg font-semibold text-slate-900">{template.name}</h3>
            <p className="mt-2 text-sm text-slate-600">{template.description}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {template.widgets.map((widget) => (
                <span key={widget} className="rounded-full bg-slate-100 px-3 py-1 text-xs uppercase tracking-[0.18em] text-slate-600">
                  {widget.replaceAll("_", " ")}
                </span>
              ))}
            </div>
          </article>
        ))}
        {loading && <div className="rounded-[1.5rem] border border-dashed border-slate-300 p-6 text-sm text-slate-500">Loading templates…</div>}
      </div>
    </section>
  );
}
