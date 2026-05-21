export default function NotFound() {
  return (
    <main className="flex min-h-screen items-center justify-center px-6 text-center">
      <div className="glass-panel rounded-[2rem] p-10">
        <div className="text-xs uppercase tracking-[0.24em] text-slate-500">Not Found</div>
        <h1 className="mt-3 font-heading text-3xl font-semibold text-slate-950">This dashboard link is no longer available.</h1>
        <p className="mt-3 text-sm text-slate-600">
          The shared token may have been revoked, or the dashboard may have been deleted.
        </p>
      </div>
    </main>
  );
}
