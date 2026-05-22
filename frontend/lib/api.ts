import {
  mockAlertHistory,
  mockAlertRules,
  mockDashboards,
  mockOverview,
  mockTemplates,
  mockTimeseries
} from "@/lib/mock-data";
import type { AlertHistory, AlertRule, Dashboard, DashboardTemplate, OverviewPayload, TimeSeriesPoint } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const ACCESS_TOKEN = process.env.NEXT_PUBLIC_ACCESS_TOKEN ?? "";
const ORG_SLUG = process.env.NEXT_PUBLIC_ORG_SLUG ?? "";
const USE_MOCK_DATA = (process.env.NEXT_PUBLIC_USE_MOCK_DATA ?? "true") === "true";

function normalizeAccessToken(token: string) {
  const trimmed = token.trim();
  return trimmed.split(".").length === 3 ? trimmed : "";
}

const NORMALIZED_ACCESS_TOKEN = normalizeAccessToken(ACCESS_TOKEN);
const NORMALIZED_ORG_SLUG = ORG_SLUG.trim().toLowerCase();

type ApiEnvelope<T> = {
  success: boolean;
  data: T;
  message?: string;
};

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(NORMALIZED_ACCESS_TOKEN ? { Authorization: `Bearer ${NORMALIZED_ACCESS_TOKEN}` } : {}),
      ...(NORMALIZED_ORG_SLUG ? { "X-Org-Slug": NORMALIZED_ORG_SLUG } : {}),
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`Request failed for ${path} with status ${response.status}`);
  }

  const payload = (await response.json()) as ApiEnvelope<T>;
  return payload.data;
}

async function rawFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(NORMALIZED_ACCESS_TOKEN ? { Authorization: `Bearer ${NORMALIZED_ACCESS_TOKEN}` } : {}),
      ...(NORMALIZED_ORG_SLUG ? { "X-Org-Slug": NORMALIZED_ORG_SLUG } : {}),
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`Request failed for ${path} with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function isMockMode() {
  return USE_MOCK_DATA || !NORMALIZED_ACCESS_TOKEN;
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

export function getSocketBaseUrl() {
  const explicit = process.env.NEXT_PUBLIC_WS_BASE_URL;
  if (explicit) return explicit;
  return API_BASE_URL.replace("http://", "ws://").replace("https://", "wss://");
}

export function getAccessToken() {
  return NORMALIZED_ACCESS_TOKEN;
}
