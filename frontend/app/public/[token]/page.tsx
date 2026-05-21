import { notFound } from "next/navigation";

import { getPublicDashboard } from "@/lib/api";

type PublicDashboardPageProps = {
  params: {
    token: string;
  };
};

export default async function PublicDashboardPage({ params }: PublicDashboardPageProps) {
  const dashboard = await getPublicDashboard(params.token);

  if (!dashboard) {
    notFound();
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(56,189,248,0.16),_transparent_35%),linear-gradient(180deg,#09111f_0%,#0f172a_55%,#111827_100%)] px-6 py-12 text-white">
      <div className="mx-auto max-w-5xl">
        <span className="inline-flex rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs uppercase tracking-[0.24em] text-sky-200">
          Shared Dashboard
        </span>
        <h1 className="mt-5 font-heading text-4xl font-semibold">{dashboard.name}</h1>
        <p className="mt-3 max-w-2xl text-sm text-slate-300">{dashboard.description || "Public read-only dashboard view."}</p>

        <section className="mt-10 grid gap-4 md:grid-cols-2">
          {dashboard.widgets.map((widget) => (
            <article key={widget.uuid} className="rounded-3xl border border-white/10 bg-white/6 p-6 backdrop-blur">
              <div className="text-xs uppercase tracking-[0.22em] text-slate-400">{widget.widget_type.replaceAll("_", " ")}</div>
              <h2 className="mt-3 text-xl font-semibold text-white">{widget.title}</h2>
              <p className="mt-3 text-sm text-slate-300">
                This shared view exposes the widget definition and can be paired with the authenticated API for live data execution.
              </p>
            </article>
          ))}
        </section>
      </div>
    </main>
  );
}
