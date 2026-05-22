"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { GoogleLogin } from "@react-oauth/google";
import { getApiBaseUrl } from "@/lib/api";
import { setStoredAuth } from "@/lib/auth";

type LoginState = "idle" | "loading" | "error";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [state, setState] = useState<LoginState>("idle");
  const [errorMsg, setErrorMsg] = useState("");

  const hasGoogle = Boolean(process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setState("loading");
    setErrorMsg("");

    try {
      const res = await fetch(`${getApiBaseUrl()}/api/v1/auth/login/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password })
      });

      const body = await res.json();

      if (!res.ok) {
        setErrorMsg(body?.message ?? body?.errors?.[0]?.message ?? "Login failed. Check your credentials.");
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

  async function handleGoogleSuccess(credential: string) {
    setState("loading");
    setErrorMsg("");

    try {
      const res = await fetch(`${getApiBaseUrl()}/api/v1/auth/google/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ credential })
      });

      const body = await res.json();

      if (!res.ok) {
        setErrorMsg(body?.message ?? "Google sign-in failed.");
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
      setErrorMsg("Could not reach the server.");
      setState("error");
    }
  }

  function handleMockMode() {
    router.push("/");
  }

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden px-4">
      <div className="noise pointer-events-none absolute inset-0" />

      <div className="glass-panel shadow-panel relative w-full max-w-md rounded-3xl px-8 py-10">
        <div className="mb-8 text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-slate-900/10 bg-white/70 px-4 py-1.5 text-xs font-medium uppercase tracking-[0.28em] text-slate-500">
            <span className="inline-flex size-1.5 rounded-full bg-sky-500" />
            Realtime Platform
          </div>
          <h1 className="font-heading mt-5 text-3xl font-semibold tracking-tight text-slate-950">
            Sign in
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            Enter your credentials to access the workspace.
          </p>
        </div>

        {hasGoogle && (
          <div className="mb-5 flex justify-center">
            <GoogleLogin
              onSuccess={(res) => {
                if (res.credential) handleGoogleSuccess(res.credential);
              }}
              onError={() => {
                setErrorMsg("Google sign-in failed. Please try again.");
                setState("error");
              }}
              text="signin_with"
              shape="pill"
              theme="outline"
              size="large"
            />
          </div>
        )}

        {hasGoogle && (
          <div className="mb-5 flex items-center gap-3">
            <div className="h-px flex-1 bg-slate-900/8" />
            <span className="text-xs text-slate-400">or sign in with email</span>
            <div className="h-px flex-1 bg-slate-900/8" />
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="email" className="text-xs font-medium text-slate-600 uppercase tracking-wide">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-xl border border-slate-900/10 bg-white/80 px-4 py-2.5 text-sm text-slate-900 outline-none placeholder:text-slate-400 focus:border-sky-400 focus:ring-2 focus:ring-sky-400/20 transition"
              placeholder="you@example.com"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="password" className="text-xs font-medium text-slate-600 uppercase tracking-wide">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-xl border border-slate-900/10 bg-white/80 px-4 py-2.5 text-sm text-slate-900 outline-none placeholder:text-slate-400 focus:border-sky-400 focus:ring-2 focus:ring-sky-400/20 transition"
              placeholder="••••••••"
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
            {state === "loading" ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <div className="mt-6 flex items-center gap-3">
          <div className="h-px flex-1 bg-slate-900/8" />
          <span className="text-xs text-slate-400">or</span>
          <div className="h-px flex-1 bg-slate-900/8" />
        </div>

        <button
          onClick={handleMockMode}
          className="mt-4 w-full rounded-xl border border-slate-900/10 bg-white/60 px-4 py-2.5 text-sm font-medium text-slate-600 transition hover:bg-white/80"
        >
          Continue with mock data
        </button>

        <p className="mt-6 text-center text-xs text-slate-400">
          No account?{" "}
          <a href="/register" className="font-medium text-sky-600 hover:underline">
            Register
          </a>
        </p>
      </div>
    </main>
  );
}
