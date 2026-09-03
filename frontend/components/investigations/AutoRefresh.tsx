"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { CurrentStage } from "@/types";

interface AutoRefreshProps {
  currentStage: CurrentStage;
  hasErrors: boolean;
  intervalMs?: number;
}

export function AutoRefresh({ currentStage, hasErrors, intervalMs = 2500 }: AutoRefreshProps) {
  const router = useRouter();

  useEffect(() => {
    // Stop polling if the investigation is finished or has errors
    if (currentStage === CurrentStage.DONE || hasErrors) {
      return;
    }

    const intervalId = setInterval(() => {
      router.refresh();
    }, intervalMs);

    // Cleanup interval on unmount
    return () => clearInterval(intervalId);
  }, [currentStage, hasErrors, intervalMs, router]);

  return null;
}
