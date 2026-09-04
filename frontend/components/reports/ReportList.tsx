"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Download, FileText } from "lucide-react";
import { RiskScoreBadge } from "@/components/investigations/RiskScoreBadge";
import { listReports } from "@/services/reportService";
import type { ReportListItem } from "@/services/reportService";

const formatDate = (value: string) => new Date(value).toLocaleString();

export function ReportList() {
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadingCaseId, setDownloadingCaseId] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const loadReports = useCallback(async () => {
    setError(null);
    try {
      setReports(await listReports());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load reports.");
    } finally {
      setLoading(false);
    }
  }, []);

  const downloadReport = useCallback(async (caseId: string) => {
    setDownloadError(null);
    setDownloadingCaseId(caseId);
    try {
      const response = await fetch(
        `/api/proxy/investigations/${encodeURIComponent(caseId)}/report/download.pdf`,
      );
      if (!response.ok || !response.headers.get("content-type")?.includes("application/pdf")) {
        throw new Error("The PDF report is unavailable. Please try again after the investigation completes.");
      }

      const url = URL.createObjectURL(await response.blob());
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${caseId}-report.pdf`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    } catch (reason) {
      setDownloadError(reason instanceof Error ? reason.message : "Unable to download the PDF report.");
    } finally {
      setDownloadingCaseId(null);
    }
  }, []);

  useEffect(() => {
    const initialLoad = window.setTimeout(() => void loadReports(), 0);
    const interval = window.setInterval(() => void loadReports(), 10_000);
    return () => {
      window.clearTimeout(initialLoad);
      window.clearInterval(interval);
    };
  }, [loadReports]);

  if (loading) {
    return <p className="text-sm text-gray-500">Loading completed investigation reports…</p>;
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 px-6 py-8 text-center">
        <h1 className="text-lg font-semibold text-red-800">Unable to load reports</h1>
        <p className="mt-2 text-sm text-red-700">{error}</p>
        <button type="button" onClick={() => void loadReports()} className="mt-4 rounded-md bg-red-700 px-3 py-2 text-sm font-medium text-white hover:bg-red-800">Retry</button>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
        <p className="mt-1 text-sm text-gray-500">Completed investigation reports update automatically.</p>
        {downloadError && <p role="alert" className="mt-2 text-sm text-red-600">{downloadError}</p>}
      </div>

      {reports.length === 0 ? (
        <div className="rounded-xl border border-gray-200 bg-white px-6 py-12 text-center shadow-sm">
          <FileText className="mx-auto h-8 w-8 text-gray-400" />
          <h2 className="mt-3 text-sm font-semibold text-gray-900">No completed reports yet</h2>
          <p className="mt-1 text-sm text-gray-500">Reports appear here when an investigation reaches DONE.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
          <table className="w-full text-left text-sm">
            <thead><tr className="border-b border-gray-200 bg-gray-50/80">
              <th className="px-6 py-3 font-semibold text-gray-600">Case ID</th><th className="px-6 py-3 font-semibold text-gray-600">Customer</th><th className="px-6 py-3 font-semibold text-gray-600">Risk score</th><th className="px-6 py-3 font-semibold text-gray-600">Recommendation</th><th className="px-6 py-3 font-semibold text-gray-600">Created</th><th className="px-6 py-3 font-semibold text-gray-600">Updated</th><th className="px-6 py-3 text-right font-semibold text-gray-600"><span className="sr-only">Download</span></th>
            </tr></thead>
            <tbody className="divide-y divide-gray-100">
              {reports.map((report) => (
                <tr key={report.caseId} className="transition-colors hover:bg-blue-50/50">
                  <td className="px-6 py-4 font-medium"><Link href={`/investigations/${encodeURIComponent(report.caseId)}`} className="text-blue-600 hover:text-blue-800">{report.caseId}</Link></td>
                  <td className="px-6 py-4 text-gray-900">{report.customerName}</td>
                  <td className="px-6 py-4"><RiskScoreBadge score={report.riskScore} /></td>
                  <td className="px-6 py-4 text-gray-700">{report.recommendation ?? "No recommendation"}</td>
                  <td className="px-6 py-4 text-gray-500">{formatDate(report.createdAt)}</td>
                  <td className="px-6 py-4 text-gray-500">{formatDate(report.updatedAt)}</td>
                  <td className="px-6 py-4 text-right"><button type="button" onClick={() => void downloadReport(report.caseId)} disabled={downloadingCaseId === report.caseId} className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"><Download className="h-4 w-4" />{downloadingCaseId === report.caseId ? "Downloading…" : "Download"}</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
