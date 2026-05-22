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

      setStoredAuth(token, body?.data?.organization?.slug);
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

      setStoredAuth(token, body?.data?.organization?.slug);
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
          <div className="mb-5 rounded-2xl border border-slate-900/10 bg-white/70 px-4 py-4">
            <div className="mb-3 flex items-center justify-center gap-2 text-sm font-medium text-slate-700">
              <svg aria-hidden="true" viewBox="0 0 24 24" className="h-5 w-5">
                <path
                  fill="#EA4335"
                  d="M12 10.2v3.9h5.5c-.2 1.3-1.5 3.9-5.5 3.9-3.3 0-6-2.7-6-6s2.7-6 6-6c1.9 0 3.1.8 3.8 1.5l2.6-2.5C16.8 3.5 14.6 2.5 12 2.5 6.8 2.5 2.5 6.8 2.5 12S6.8 21.5 12 21.5c6.9 0 9.1-4.8 9.1-7.3 0-.5-.1-.9-.1-1.2H12Z"
                />
                <path
                  fill="#34A853"
                  d="M2.5 7.6 5.7 10c.9-2.7 3.4-4.6 6.3-4.6 1.9 0 3.1.8 3.8 1.5l2.6-2.5C16.8 3.5 14.6 2.5 12 2.5 8.3 2.5 5.1 4.6 3.5 7.6Z"
                />
                <path
                  fill="#FBBC05"
                  d="M12 21.5c2.5 0 4.6-.8 6.2-2.3l-3-2.4c-.8.6-1.9 1.1-3.2 1.1-3.9 0-5.2-2.5-5.5-3.8l-3.2 2.5c1.6 3.1 4.8 4.9 8.7 4.9Z"
                />
                <path
                  fill="#4285F4"
                  d="M3.5 16.4 6.7 14c-.2-.5-.3-1.2-.3-2s.1-1.4.3-2L3.5 7.6C2.8 8.9 2.5 10.4 2.5 12s.3 3.1 1 4.4Z"
                />
              </svg>
              <span>Continue with Google</span>
            </div>
            <div className="flex justify-center">
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
