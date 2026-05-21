import { create } from "zustand";

type WorkspaceState = {
  selectedDashboardId: string | null;
  selectedEventName: string;
  setSelectedDashboardId: (dashboardId: string) => void;
  setSelectedEventName: (eventName: string) => void;
};

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  selectedDashboardId: null,
  selectedEventName: "page_view",
  setSelectedDashboardId: (selectedDashboardId) => set({ selectedDashboardId }),
  setSelectedEventName: (selectedEventName) => set({ selectedEventName })
}));
