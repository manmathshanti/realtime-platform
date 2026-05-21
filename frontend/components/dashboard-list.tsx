"use client";

import type { Dashboard } from "@/lib/types";

type DashboardListProps = {
  dashboards: Dashboard[];
  loading: boolean;
  search: string;
  selectedDashboardId: string | null;
  onSearchChange: (value: string) => void;
  onSelectDashboard: (dashboardId: string) => void;
};

export function DashboardList({
  dashboards,
  loading,
  search,
  selectedDashboardId,
  onSearchChange,
  onSelectDashboard
}: DashboardListProps) {
  return (
    <section className="glass-panel rounded-[2rem] p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="text-xs uppercase tracking-[0.24em] text-slate-500">Dashboards</div>
          <h2 className="mt-2 font-heading text-2xl font-semibold text-slate-950">Executive, product, and ops boards</h2>
        </div>
        <input
          className="rounded-full border border-slate-900/10 bg-white/80 px-4 py-3 text-sm outline-none ring-0 placeholder:text-slate-400"
          placeholder="Search dashboards"
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
        />
      </div>

      <div className="mt-5 grid gap-4">
        {loading ? (
          <div className="rounded-[1.5rem] border border-dashed border-slate-300 p-6 text-sm text-slate-500">Loading dashboards…</div>
        ) : (
          dashboards.map((dashboard) => (
            <button
              key={dashboard.uuid}
              className={`rounded-[1.5rem] border p-5 text-left transition ${
                selectedDashboardId === dashboard.uuid
                  ? "border-slate-950 bg-slate-950 text-white"
                  : "border-slate-900/10 bg-white/80 text-slate-900 hover:border-slate-300"
              }`}
              onClick={() => onSelectDashboard(dashboard.uuid)}
            >
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h3 className="text-lg font-semibold">{dashboard.name}</h3>
                  <p className={`mt-2 text-sm ${selectedDashboardId === dashboard.uuid ? "text-slate-300" : "text-slate-600"}`}>
                    {dashboard.description}
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-semibold">{dashboard.widget_count}</div>
                  <div className={`text-xs uppercase tracking-[0.18em] ${selectedDashboardId === dashboard.uuid ? "text-slate-400" : "text-slate-500"}`}>
                    widgets
                  </div>
                </div>
              </div>
              <div className={`mt-4 flex items-center gap-3 text-xs uppercase tracking-[0.2em] ${selectedDashboardId === dashboard.uuid ? "text-sky-200" : "text-slate-500"}`}>
                <span>{dashboard.refresh_interval || "manual"}s refresh</span>
                <span>{dashboard.is_public ? "public share enabled" : "team-only access"}</span>
              </div>
            </button>
          ))
        )}
      </div>
    </section>
  );
}
