import {
  mockAlertHistory,
  mockAlertRules,
  mockDashboards,
  mockOverview,
  mockTemplates,
  mockTimeseries
} from "@/lib/mock-data";
import { clearStoredAuth, getStoredOrgSlug, getStoredToken, setStoredAuth } from "@/lib/auth";
import type { AlertHistory, AlertRule, Dashboard, DashboardTemplate, OverviewPayload, TimeSeriesPoint } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const USE_MOCK_DATA = (process.env.NEXT_PUBLIC_USE_MOCK_DATA ?? "true") === "true";

function normalizeToken(token: string): string {
  const trimmed = token.trim();
  return trimmed.split(".").length === 3 ? trimmed : "";
}

function getActiveToken(): string {
  const envToken = process.env.NEXT_PUBLIC_ACCESS_TOKEN ?? "";
  if (normalizeToken(envToken)) return normalizeToken(envToken);
  return normalizeToken(getStoredToken());
}

function getActiveOrgSlug(): string {
  const envSlug = (process.env.NEXT_PUBLIC_ORG_SLUG ?? "").trim().toLowerCase();
  if (envSlug) return envSlug;
  return getStoredOrgSlug().trim().toLowerCase();
}

export function isMockMode(): boolean {
  return USE_MOCK_DATA || !getActiveToken();
}

type ApiEnvelope<T> = {
  success: boolean;
  data: T;
  message?: string;
};

async function tryRefresh(): Promise<string | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/auth/refresh/`, {
      method: "POST",
      credentials: "include"
    });
    if (!res.ok) return null;
    const body = (await res.json()) as ApiEnvelope<{ access_token: string }>;
    const newToken = body.data?.access_token ?? "";
    if (normalizeToken(newToken)) {
      setStoredAuth(newToken);
      return newToken;
    }
    return null;
  } catch {
    return null;
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getActiveToken();
  const orgSlug = getActiveOrgSlug();

  const makeHeaders = (t: string) => ({
    "Content-Type": "application/json",
    ...(t ? { Authorization: `Bearer ${t}` } : {}),
    ...(orgSlug ? { "X-Org-Slug": orgSlug } : {}),
    ...(init?.headers ?? {})
  });

  let response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: makeHeaders(token),
    credentials: "include",
    cache: "no-store"
  });

  if (response.status === 401) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      response = await fetch(`${API_BASE_URL}${path}`, {
        ...init,
        headers: makeHeaders(refreshed),
        credentials: "include",
        cache: "no-store"
      });
    } else {
      clearStoredAuth();
      if (typeof window !== "undefined") window.location.href = "/login";
      throw new Error("Session expired");
    }
  }

  if (!response.ok) {
    throw new Error(`Request failed for ${path} with status ${response.status}`);
  }

  const payload = (await response.json()) as ApiEnvelope<T>;
  return payload.data;
}

async function rawFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getActiveToken();
  const orgSlug = getActiveOrgSlug();

  const makeHeaders = (t: string) => ({
    ...(t ? { Authorization: `Bearer ${t}` } : {}),
    ...(orgSlug ? { "X-Org-Slug": orgSlug } : {}),
    ...(init?.headers ?? {})
  });

  let response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: makeHeaders(token),
    credentials: "include",
    cache: "no-store"
  });

  if (response.status === 401) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      response = await fetch(`${API_BASE_URL}${path}`, {
        ...init,
        headers: makeHeaders(refreshed),
        credentials: "include",
        cache: "no-store"
      });
    } else {
      clearStoredAuth();
      if (typeof window !== "undefined") window.location.href = "/login";
      throw new Error("Session expired");
    }
  }

  if (!response.ok) {
    throw new Error(`Request failed for ${path} with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function getOverview(): Promise<OverviewPayload> {
  if (isMockMode()) return mockOverview;
  return apiFetch<OverviewPayload>("/api/v1/dashboards/overview/");
}

export async function getDashboards(): Promise<Dashboard[]> {
  if (isMockMode()) return mockDashboards;
  return apiFetch<Dashboard[]>("/api/v1/dashboards/");
}

export async function getTemplates(): Promise<DashboardTemplate[]> {
  if (isMockMode()) return mockTemplates;
  return apiFetch<DashboardTemplate[]>("/api/v1/dashboards/templates/");
}

export async function getAlertRules(): Promise<AlertRule[]> {
  if (isMockMode()) return mockAlertRules;
  return apiFetch<AlertRule[]>("/api/v1/alerts/rules/");
}

export async function getAlertHistory(): Promise<AlertHistory[]> {
  if (isMockMode()) return mockAlertHistory;
  const payload = await rawFetch<{ results: AlertHistory[] }>("/api/v1/alerts/history/");
  return payload.results;
}

export async function getTimeseries(eventName = "page_view"): Promise<TimeSeriesPoint[]> {
  if (isMockMode()) return mockTimeseries;
  return apiFetch<TimeSeriesPoint[]>(`/api/v1/ingest/query/timeseries/?event_name=${encodeURIComponent(eventName)}&interval=hour`);
}

export async function getPublicDashboard(token: string): Promise<(Dashboard & { widgets: Array<{ uuid: string; title: string; widget_type: string }> }) | null> {
  try {
    return await apiFetch(`/api/v1/dashboards/public/${token}/`);
  } catch {
    return null;
  }
}

export function getSocketBaseUrl(): string {
  const explicit = process.env.NEXT_PUBLIC_WS_BASE_URL;
  if (explicit) return explicit;
  return API_BASE_URL.replace("http://", "ws://").replace("https://", "wss://");
}

export function getAccessToken(): string {
  return getActiveToken();
}

export function getApiBaseUrl(): string {
  return API_BASE_URL;
}
