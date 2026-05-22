"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { WorkspacePage } from "@/components/workspace-page";
import { isMockMode } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    if (!isMockMode()) return;
    // In mock mode, no token is needed — render workspace with mock data.
    // When NEXT_PUBLIC_USE_MOCK_DATA is explicitly false and there's no token,
    // redirect to login so the user can authenticate.
    const mockEnvExplicit = process.env.NEXT_PUBLIC_USE_MOCK_DATA;
    if (mockEnvExplicit === "false") {
      router.replace("/login");
    }
  }, [router]);

  return <WorkspacePage />;
}
