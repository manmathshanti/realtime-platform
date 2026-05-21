"use client";

import type { AlertHistory, AlertRule } from "@/lib/types";

type AlertFeedProps = {
  rules: AlertRule[];
  history: AlertHistory[];
  loading: boolean;
};

export function AlertFeed({ rules, history, loading }: AlertFeedProps) {
  return (
    <section className="glass-panel rounded-[2rem] p-6">
      <div className="text-xs uppercase tracking-[0.24em] text-slate-500">Alert Center</div>
      <h2 className="mt-2 font-heading text-2xl font-semibold text-slate-950">Thresholds, history, and response context</h2>

      <div className="mt-5 space-y-3">
        {loading ? (
          <div className="rounded-[1.4rem] border border-dashed border-slate-300 p-6 text-sm text-slate-500">Loading alert posture…</div>
        ) : (
          rules.map((rule) => (
            <article key={rule.uuid} className="rounded-[1.4rem] border border-slate-900/10 bg-white/80 p-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="text-base font-semibold text-slate-900">{rule.name}</h3>
                  <p className="mt-1 text-sm text-slate-600">
                    {rule.event_name} {rule.condition_operator} {rule.threshold_value} over {rule.window_minutes} minutes
                  </p>
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${
                    rule.status === "triggered"
                      ? "bg-rose-100 text-rose-700"
                      : "bg-emerald-100 text-emerald-700"
                  }`}
                >
                  {rule.status}
                </span>
              </div>
            </article>
          ))
        )}
      </div>

      <div className="mt-6 rounded-[1.5rem] bg-slate-950 p-5 text-white">
        <div className="text-sm font-semibold">Recent history</div>
        <div className="mt-4 space-y-3">
          {history.slice(0, 4).map((item) => (
            <div key={item.uuid} className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="text-sm font-medium text-sky-200">{item.rule_name}</div>
              <div className="mt-1 text-sm text-slate-300">{item.message}</div>
              <div className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-400">
                {new Date(item.created_at).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
