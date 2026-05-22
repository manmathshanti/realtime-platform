export type KpiSummary = {
  total_events: number;
  events_last_24h: number;
  dashboards: number;
  active_alerts: number;
};

export type OverviewPayload = {
  organization: {
    uuid: string;
    name: string;
    slug: string;
  };
  kpis: KpiSummary;
  top_events: Array<{ event_name: string; count: number }>;
  recent_alerts: Array<{
    uuid: string;
    rule_name: string;
    triggered_value: number;
    message: string;
    created_at: string;
  }>;
};

export type Dashboard = {
  uuid: string;
  name: string;
  description: string;
  is_public: boolean;
  refresh_interval: number;
  widget_count: number;
  widgets?: Widget[];
};

export type Widget = {
  uuid: string;
  title: string;
  widget_type: string;
  position_x: number;
  position_y: number;
  width: number;
  height: number;
};

export type DashboardTemplate = {
  id: string;
  name: string;
  description: string;
  widgets: string[];
};

export type TimeSeriesPoint = {
  bucket: string;
  count?: number;
  value?: number;
};

export type AlertRule = {
  uuid: string;
  name: string;
  event_name: string;
  threshold_value: number;
  condition_operator: string;
  window_minutes: number;
  status: string;
};

export type AlertHistory = {
  uuid: string;
  rule_name: string;
  triggered_value: number;
  message: string;
  created_at: string;
  resolved_at?: string | null;
};

export type EventStreamItem = {
  id?: number;
  event_name: string;
  properties: Record<string, unknown>;
  timestamp: string;
};
