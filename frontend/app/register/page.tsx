"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { getApiBaseUrl } from "@/lib/api";
import { setStoredAuth } from "@/lib/auth";

type FormState = "idle" | "loading" | "error";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "", first_name: "", last_name: "", org_name: "" });
  const [state, setState] = useState<FormState>("idle");
  const [errorMsg, setErrorMsg] = useState("");

  function update(field: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement>) => setForm((prev) => ({ ...prev, [field]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setState("loading");
    setErrorMsg("");

    try {
      const res = await fetch(`${getApiBaseUrl()}/api/v1/auth/register/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(form)
      });

      const body = await res.json();

      if (!res.ok) {
        setErrorMsg(body?.message ?? body?.errors?.[0]?.message ?? "Registration failed.");
        setState("error");
        return;
      }

      const token: string = body?.data?.access_token ?? "";
      if (!token) {
        setErrorMsg("Invalid response from server.");
        setState("error");
        return;
      }

      setStoredAuth(token);
      router.push("/");
      router.refresh();
    } catch {
      setErrorMsg("Could not reach the server. Make sure the backend is running.");
      setState("error");
    }
  }

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-12">
      <div className="noise pointer-events-none absolute inset-0" />

      <div className="glass-panel shadow-panel relative w-full max-w-md rounded-3xl px-8 py-10">
        <div className="mb-8 text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-slate-900/10 bg-white/70 px-4 py-1.5 text-xs font-medium uppercase tracking-[0.28em] text-slate-500">
            <span className="inline-flex size-1.5 rounded-full bg-emerald-500" />
            Realtime Platform
          </div>
          <h1 className="font-heading mt-5 text-3xl font-semibold tracking-tight text-slate-950">
            Create account
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            Set up your workspace to get started.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-slate-600 uppercase tracking-wide">First name</label>
              <input
                type="text"
                required
                value={form.first_name}
                onChange={update("first_name")}
                className="w-full rounded-xl border border-slate-900/10 bg-white/80 px-4 py-2.5 text-sm text-slate-900 outline-none placeholder:text-slate-400 focus:border-sky-400 focus:ring-2 focus:ring-sky-400/20 transition"
                placeholder="Jane"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-slate-600 uppercase tracking-wide">Last name</label>
              <input
                type="text"
                value={form.last_name}
                onChange={update("last_name")}
                className="w-full rounded-xl border border-slate-900/10 bg-white/80 px-4 py-2.5 text-sm text-slate-900 outline-none placeholder:text-slate-400 focus:border-sky-400 focus:ring-2 focus:ring-sky-400/20 transition"
                placeholder="Doe"
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-slate-600 uppercase tracking-wide">Organisation name</label>
            <input
              type="text"
              required
              value={form.org_name}
              onChange={update("org_name")}
              className="w-full rounded-xl border border-slate-900/10 bg-white/80 px-4 py-2.5 text-sm text-slate-900 outline-none placeholder:text-slate-400 focus:border-sky-400 focus:ring-2 focus:ring-sky-400/20 transition"
              placeholder="Acme Corp"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-slate-600 uppercase tracking-wide">Email</label>
            <input
              type="email"
              autoComplete="email"
              required
              value={form.email}
              onChange={update("email")}
              className="w-full rounded-xl border border-slate-900/10 bg-white/80 px-4 py-2.5 text-sm text-slate-900 outline-none placeholder:text-slate-400 focus:border-sky-400 focus:ring-2 focus:ring-sky-400/20 transition"
              placeholder="you@example.com"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-slate-600 uppercase tracking-wide">Password</label>
            <input
              type="password"
              autoComplete="new-password"
              required
              value={form.password}
              onChange={update("password")}
              className="w-full rounded-xl border border-slate-900/10 bg-white/80 px-4 py-2.5 text-sm text-slate-900 outline-none placeholder:text-slate-400 focus:border-sky-400 focus:ring-2 focus:ring-sky-400/20 transition"
              placeholder="Min. 8 chars, must include a digit"
            />
          </div>

          {state === "error" && (
            <p className="rounded-xl bg-rose-50 border border-rose-200 px-4 py-2.5 text-sm text-rose-600">
              {errorMsg}
            </p>
          )}

          <button
            type="submit"
            disabled={state === "loading"}
            className="mt-2 w-full rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {state === "loading" ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-slate-400">
          Already have an account?{" "}
          <a href="/login" className="font-medium text-sky-600 hover:underline">
            Sign in
          </a>
        </p>
      </div>
    </main>
  );
}
