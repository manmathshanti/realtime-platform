"use client";

import { useEffect, useMemo, useState } from "react";

import { getAccessToken, getSocketBaseUrl, isMockMode } from "@/lib/api";
import { mockEventStream } from "@/lib/mock-data";
import type { EventStreamItem } from "@/lib/types";

export function useLiveStream() {
  const [events, setEvents] = useState<EventStreamItem[]>(mockEventStream);
  const [status, setStatus] = useState<"mock" | "connecting" | "connected" | "offline">(
    isMockMode() ? "mock" : "connecting"
  );

  const socketUrl = useMemo(() => {
    const token = getAccessToken();
    return `${getSocketBaseUrl()}/ws/events/stream/${token ? `?token=${token}` : ""}`;
  }, []);

  useEffect(() => {
    if (isMockMode()) return;

    const socket = new WebSocket(socketUrl);
    setStatus("connecting");

    socket.onopen = () => setStatus("connected");
    socket.onclose = () => setStatus("offline");
    socket.onerror = () => setStatus("offline");
    socket.onmessage = (message) => {
      const parsed = JSON.parse(message.data) as { type: string; event?: EventStreamItem };
      if (parsed.type === "event.new" && parsed.event) {
        setEvents((current) => [parsed.event as EventStreamItem, ...current].slice(0, 12));
      }
    };

    return () => socket.close();
  }, [socketUrl]);

  return { events, status };
}
