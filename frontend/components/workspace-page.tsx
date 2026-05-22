"use client";

import { useQuery } from "@tanstack/react-query";
import { startTransition, useDeferredValue, useMemo, useState } from "react";

import { AlertFeed } from "@/components/alert-feed";
import { ApiPlayground } from "@/components/api-playground";
import { DashboardList } from "@/components/dashboard-list";
import { EventStreamPanel } from "@/components/event-stream-panel";
import { TemplateStrip } from "@/components/template-strip";
import { TimeSeriesPanel } from "@/components/time-series-panel";
import { getAlertHistory, getAlertRules, getDashboards, getOverview, getTemplates, getTimeseries, isMockMode } from "@/lib/api";
import { useWorkspaceStore } from "@/stores/workspace-store";

const kpiMeta = [
  { key: "total_events", label: "Total Events", tone: "text-sky-500" },
  { key: "events_last_24h", label: "Last 24h", tone: "text-emerald-500" },
  { key: "dashboards", label: "Dashboards", tone: "text-amber-500" },
  { key: "active_alerts", label: "Active Alerts", tone: "text-rose-500" }
] as const;

export function WorkspacePage() {
  const [search, setSearch] = useState("");
  const selectedEventName = useWorkspaceStore((state) => state.selectedEventName);
  const setSelectedEventName = useWorkspaceStore((state) => state.setSelectedEventName);
  const selectedDashboardId = useWorkspaceStore((state) => state.selectedDashboardId);
  const setSelectedDashboardId = useWorkspaceStore((state) => state.setSelectedDashboardId);
  const deferredSearch = useDeferredValue(search);

  const overviewQuery = useQuery({ queryKey: ["overview"], queryFn: getOverview });
  const dashboardsQuery = useQuery({ queryKey: ["dashboards"], queryFn: getDashboards });
  const templatesQuery = useQuery({ queryKey: ["templates"], queryFn: getTemplates });
  const alertRulesQuery = useQuery({ queryKey: ["alert-rules"], queryFn: getAlertRules });
  const alertHistoryQuery = useQuery({ queryKey: ["alert-history"], queryFn: getAlertHistory });
  const timeSeriesQuery = useQuery({
    queryKey: ["timeseries", selectedEventName],
    queryFn: () => getTimeseries(selectedEventName)
  });

  const dashboards = dashboardsQuery.data ?? [];
  const overview = overviewQuery.data;
  const filteredDashboards = useMemo(
    () =>
      dashboards.filter((dashboard) =>
        `${dashboard.name} ${dashboard.description}`.toLowerCase().includes(deferredSearch.toLowerCase())
      ),
    [dashboards, deferredSearch]
  );
  const recentAlert = overview?.recent_alerts?.[0];

  return (
    <main className="relative overflow-hidden px-4 pb-16 pt-4 sm:px-6 lg:px-8">
      <div className="noise pointer-events-none absolute inset-0" />
      <section className="relative mx-auto max-w-7xl">
        <div className="glass-panel mesh-card overflow-hidden rounded-[2rem] px-6 py-7 sm:px-8">
          <div className="flex flex-col gap-8 lg:grid lg:grid-cols-[1.25fr_0.75fr] lg:items-stretch">
            <div className="max-w-3xl">
              <div className="inline-flex items-center gap-3 rounded-full border border-slate-900/10 bg-white/70 px-4 py-2 text-xs font-medium uppercase tracking-[0.28em] text-slate-600">
                <span className={`pulse-dot inline-flex size-2 rounded-full ${isMockMode() ? "bg-amber-500 text-amber-400" : "bg-emerald-500 text-emerald-400"}`} />
                {isMockMode() ? "Mock workspace mode" : "Live workspace mode"}
              </div>
              <h1 className="mt-5 font-heading text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
                A unified command center for product, revenue, and platform signals.
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600">
                Monitor incoming events, shape dashboard narratives, and respond to alert conditions from a workspace designed for operating teams.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <div className="rounded-full border border-slate-900/10 bg-white/75 px-4 py-2 text-sm text-slate-700">
                  Org: <span className="font-semibold text-slate-950">{overview?.organization.name ?? "Loading"}</span>
                </div>
                <div className="rounded-full border border-slate-900/10 bg-white/75 px-4 py-2 text-sm text-slate-700">
                  Priority focus: <span className="font-semibold text-slate-950">{recentAlert?.rule_name ?? "Traffic stability"}</span>
                </div>
              </div>
            </div>

            <div className="grid gap-3 rounded-[1.75rem] bg-[linear-gradient(135deg,#0f172a_0%,#172554_100%)] px-5 py-5 text-slate-50 shadow-panel">
              <div>
                <div className="text-xs uppercase tracking-[0.24em] text-sky-200/75">Operational note</div>
                <div className="mt-2 text-lg font-semibold">
                  {recentAlert?.message ?? "No high-severity anomaly is dominating the workspace right now."}
                </div>
              </div>
              <div>
                <div className="text-xs uppercase tracking-[0.24em] text-sky-200/75">Most active event</div>
                <div className="mt-2 text-lg font-semibold text-sky-300">
                  {overview?.top_events?.[0]?.event_name ?? "page_view"}
                </div>
                <div className="mt-1 text-sm text-slate-300">
                  {overview?.top_events?.[0]?.count ?? "--"} events in the current comparison window
                </div>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4 sm:col-span-2">
                <div className="text-xs uppercase tracking-[0.24em] text-slate-400">Executive snapshot</div>
                <div className="mt-3 grid gap-3 sm:grid-cols-3">
                  <div>
                    <div className="text-2xl font-semibold text-white">{overview?.kpis.total_events ?? "--"}</div>
                    <div className="text-xs uppercase tracking-[0.18em] text-slate-400">events tracked</div>
                  </div>
                  <div>
                    <div className="text-2xl font-semibold text-white">{overview?.kpis.events_last_24h ?? "--"}</div>
                    <div className="text-xs uppercase tracking-[0.18em] text-slate-400">24h volume</div>
                  </div>
                  <div>
                    <div className="text-2xl font-semibold text-white">{overview?.kpis.active_alerts ?? "--"}</div>
                    <div className="text-xs uppercase tracking-[0.18em] text-slate-400">active rules</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {kpiMeta.map((item) => (
              <article key={item.key} className="rounded-[1.5rem] border border-slate-900/10 bg-white/85 p-5 shadow-[0_20px_50px_rgba(15,23,42,0.05)]">
                <div className="text-xs uppercase tracking-[0.22em] text-slate-500">{item.label}</div>
                <div className={`mt-3 text-3xl font-semibold ${item.tone}`}>
                  {overview?.kpis[item.key] ?? "--"}
                </div>
              </article>
            ))}
          </div>
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-[1.25fr_0.85fr]">
          <TimeSeriesPanel
            data={timeSeriesQuery.data ?? []}
            topEvents={overviewQuery.data?.top_events ?? []}
            loading={timeSeriesQuery.isLoading}
            selectedEventName={selectedEventName}
            onSelectEvent={(eventName) => {
              startTransition(() => setSelectedEventName(eventName));
            }}
          />
          <AlertFeed
            rules={alertRulesQuery.data ?? []}
            history={alertHistoryQuery.data ?? []}
            loading={alertRulesQuery.isLoading || alertHistoryQuery.isLoading}
          />
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
          <DashboardList
            dashboards={filteredDashboards}
            loading={dashboardsQuery.isLoading}
            search={search}
            selectedDashboardId={selectedDashboardId}
            onSearchChange={setSearch}
            onSelectDashboard={(dashboardId) => {
              startTransition(() => setSelectedDashboardId(dashboardId));
            }}
          />
          <EventStreamPanel />
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_1fr]">
          <TemplateStrip templates={templatesQuery.data ?? []} loading={templatesQuery.isLoading} />
          <ApiPlayground />
        </div>
      </section>
    </main>
  );
}
