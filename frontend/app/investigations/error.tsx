"use client";

import { useEffect } from "react";
import { AlertTriangle, RefreshCcw, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function InvestigationsError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center py-20 px-4 text-center">
      <AlertTriangle className="mb-4 h-12 w-12 text-amber-500" />
      <h2 className="text-xl font-bold text-gray-900 dark:text-white">Unable to load investigation</h2>
      <p className="mt-2 text-sm text-gray-500 max-w-md dark:text-gray-400">
        {error.message || "An unexpected error occurred while fetching the investigation data."}
      </p>
      <div className="mt-6 flex flex-wrap gap-4 items-center justify-center">
        <button
          onClick={() => reset()}
          className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
        >
          <RefreshCcw className="h-4 w-4" /> Retry
        </button>
        <Link
          href="/investigations"
          className="flex items-center gap-2 rounded-md border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-800/60"
        >
          <ArrowLeft className="h-4 w-4" /> Back to List
        </Link>
      </div>
    </div>
  );
}
