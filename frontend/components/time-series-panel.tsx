"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import type { TimeSeriesPoint } from "@/lib/types";

type TimeSeriesPanelProps = {
  data: TimeSeriesPoint[];
  topEvents: Array<{ event_name: string; count: number }>;
  loading: boolean;
  selectedEventName: string;
  onSelectEvent: (eventName: string) => void;
};

export function TimeSeriesPanel({
  data,
  topEvents,
  loading,
  selectedEventName,
  onSelectEvent
}: TimeSeriesPanelProps) {
  return (
    <section className="glass-panel rounded-[2rem] p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="text-xs uppercase tracking-[0.24em] text-slate-500">Live Metric Story</div>
          <h2 className="mt-2 font-heading text-2xl font-semibold text-slate-950">Telemetry that reads like a control tower</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            Switch event families and track how traffic, product behavior, and operations evolve over time.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {topEvents.map((event) => (
            <button
              key={event.event_name}
              className={`rounded-full px-4 py-2 text-sm transition ${
                selectedEventName === event.event_name
                  ? "bg-slate-950 text-white"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
              onClick={() => onSelectEvent(event.event_name)}
            >
              {event.event_name}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-[1.45fr_0.95fr]">
        <div className="rounded-[1.5rem] border border-slate-900/10 bg-white/85 p-4">
          <div className="mb-3 text-sm font-medium text-slate-700">{selectedEventName} over time</div>
          <div className="h-72">
            {loading ? (
              <div className="flex h-full items-center justify-center text-sm text-slate-500">Loading trend data…</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                  <CartesianGrid strokeDasharray="4 4" stroke="#dbe2ea" />
                  <XAxis dataKey="bucket" tickFormatter={(value) => new Date(value).getHours().toString().padStart(2, "0")} stroke="#64748b" />
                  <YAxis stroke="#64748b" />
                  <Tooltip />
                  <Line type="monotone" dataKey="value" stroke="#0f172a" strokeWidth={3} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="rounded-[1.5rem] border border-slate-900/10 bg-slate-950 p-4 text-white">
          <div className="mb-3 text-sm font-medium text-slate-200">Top event mix</div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topEvents}>
                <CartesianGrid strokeDasharray="4 4" stroke="#263244" />
                <XAxis dataKey="event_name" stroke="#cbd5e1" />
                <YAxis stroke="#cbd5e1" />
                <Tooltip />
                <Bar dataKey="count" fill="#38bdf8" radius={[10, 10, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </section>
  );
}
