import type {
  AlertHistory,
  AlertRule,
  Dashboard,
  DashboardTemplate,
  EventStreamItem,
  OverviewPayload,
  TimeSeriesPoint
} from "@/lib/types";

export const mockOverview: OverviewPayload = {
  organization: {
    uuid: "demo-org",
    name: "Northstar Commerce",
    slug: "northstar-commerce"
  },
  kpis: {
    total_events: 128430,
    events_last_24h: 9214,
    dashboards: 6,
    active_alerts: 3
  },
  top_events: [
    { event_name: "page_view", count: 3890 },
    { event_name: "checkout_started", count: 1480 },
    { event_name: "order_completed", count: 617 },
    { event_name: "signup_clicked", count: 584 },
    { event_name: "api_error", count: 49 }
  ],
  recent_alerts: [
    {
      uuid: "alert-1",
      rule_name: "Checkout errors",
      triggered_value: 12,
      message: 'Alert "Checkout errors": api_error count was 12 in the last 10 minutes.',
      created_at: new Date().toISOString()
    }
  ]
};

export const mockDashboards: Dashboard[] = [
  {
    uuid: "db-1",
    name: "Revenue Pulse",
    description: "Executive-ready revenue, conversion, and checkout telemetry.",
    is_public: true,
    refresh_interval: 30,
    widget_count: 4
  },
  {
    uuid: "db-2",
    name: "Product Journey",
    description: "Activation funnels, feature clicks, and retention events.",
    is_public: false,
    refresh_interval: 60,
    widget_count: 5
  },
  {
    uuid: "db-3",
    name: "Platform Health",
    description: "Latency spikes, API errors, and deployment impact.",
    is_public: false,
    refresh_interval: 30,
    widget_count: 3
  }
];

export const mockTemplates: DashboardTemplate[] = [
  {
    id: "web-analytics",
    name: "Web Analytics",
    description: "Acquisition, page views, and engagement velocity.",
    widgets: ["line_chart", "bar_chart", "kpi_card", "table"]
  },
  {
    id: "sales-pipeline",
    name: "Sales Pipeline",
    description: "Lead flow, funnel conversion, and revenue checkpoints.",
    widgets: ["bar_chart", "pie_chart", "kpi_card"]
  },
  {
    id: "devops-health",
    name: "DevOps Health",
    description: "Deploys, incidents, and recovery signals in one board.",
    widgets: ["line_chart", "table", "kpi_card"]
  }
];

export const mockTimeseries: TimeSeriesPoint[] = Array.from({ length: 12 }, (_, index) => ({
  bucket: new Date(Date.now() - (11 - index) * 60 * 60 * 1000).toISOString(),
  count: 380 + index * 42 + (index % 3) * 18,
  value: 380 + index * 42 + (index % 3) * 18
}));

export const mockAlertRules: AlertRule[] = [
  {
    uuid: "rule-1",
    name: "Error rate spike",
    event_name: "api_error",
    threshold_value: 10,
    condition_operator: "gt",
    window_minutes: 10,
    status: "triggered"
  },
  {
    uuid: "rule-2",
    name: "Checkout slowdown",
    event_name: "checkout_started",
    threshold_value: 300,
    condition_operator: "lt",
    window_minutes: 30,
    status: "active"
  }
];

export const mockAlertHistory: AlertHistory[] = [
  {
    uuid: "history-1",
    rule_name: "Error rate spike",
    triggered_value: 14,
    message: "API errors crossed the threshold for 10 minutes.",
    created_at: new Date().toISOString(),
    resolved_at: null
  },
  {
    uuid: "history-2",
    rule_name: "Checkout slowdown",
    triggered_value: 250,
    message: "Checkout starts dropped below the expected threshold.",
    created_at: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    resolved_at: new Date(Date.now() - 1000 * 60 * 20).toISOString()
  }
];

export const mockEventStream: EventStreamItem[] = [
  {
    id: 1,
    event_name: "page_view",
    properties: { path: "/pricing", session_id: "sess_1001" },
    timestamp: new Date().toISOString()
  },
  {
    id: 2,
    event_name: "checkout_started",
    properties: { cart_value: 119.99, country: "US" },
    timestamp: new Date(Date.now() - 1000 * 60).toISOString()
  },
  {
    id: 3,
    event_name: "api_error",
    properties: { service: "billing", status_code: 502 },
    timestamp: new Date(Date.now() - 1000 * 60 * 2).toISOString()
  }
];
