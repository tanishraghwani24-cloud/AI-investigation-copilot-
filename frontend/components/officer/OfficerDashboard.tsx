"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, Inbox, Loader2, ShieldAlert } from "lucide-react";
import {
  getMockBankCustomer,
  getMockBankTransactions,
  investigateAlertRequest,
  listAlertsRequest,
  type BankAlert,
} from "@/services/api";

/**
 * Officer Inbox: a live queue of fraud alerts raised by the Mock Bank.
 *
 * Alerts come from the backend simulator, not from this component — the inbox
 * only polls and escalates. "Investigate" hands the alert to the backend, which
 * creates the case tied to that alert and starts the pipeline; the alert's
 * status change is likewise backend state, so a handled alert stays handled
 * across a reload.
 */

const POLL_INTERVAL_MS = 10_000;

interface MockCustomer {
  first_name?: string;
  last_name?: string;
  risk_rating?: string;
  occupation?: string;
}

interface MockTransaction {
  transaction_id: string;
  timestamp: string;
  transaction_type: string;
  description: string;
  amount: number;
}

const SEVERITY_STYLES: Record<string, string> = {
  HIGH: "bg-red-50 text-red-700 ring-red-200",
  MEDIUM: "bg-amber-50 text-amber-700 ring-amber-200",
  LOW: "bg-gray-100 text-gray-600 ring-gray-200",
};

// Priority order for the inbox queue: HIGH before MEDIUM before LOW. Anything
// outside this set (unexpected severity values) sorts last rather than erroring.
const SEVERITY_RANK: Record<string, number> = { HIGH: 0, MEDIUM: 1, LOW: 2 };

/**
 * Order the queue by severity as reported by the alert API (never
 * recalculated here), HIGH first; alerts of equal severity are then ordered
 * newest-first by creation time.
 */
function sortAlertsBySeverity(list: BankAlert[]): BankAlert[] {
  return [...list].sort((a, b) => {
    const rankDiff = (SEVERITY_RANK[a.severity] ?? 99) - (SEVERITY_RANK[b.severity] ?? 99);
    if (rankDiff !== 0) return rankDiff;
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });
}

function SeverityBadge({ severity }: { severity: string }) {
  const style = SEVERITY_STYLES[severity] ?? SEVERITY_STYLES.LOW;
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${style}`}>
      {severity}
    </span>
  );
}

function formatAmount(amount?: number | null, currency?: string | null) {
  if (amount == null) return null;
  return `${amount.toLocaleString(undefined, { minimumFractionDigits: 2 })} ${currency ?? "USD"}`;
}

export function OfficerDashboard() {
  const router = useRouter();
  const [alerts, setAlerts] = useState<BankAlert[]>([]);
  const [selected, setSelected] = useState<BankAlert | null>(null);
  const [customer, setCustomer] = useState<MockCustomer | null>(null);
  const [transactions, setTransactions] = useState<MockTransaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [investigatingId, setInvestigatingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadAlerts = useCallback(async () => {
    try {
      setAlerts(sortAlertsBySeverity(await listAlertsRequest("OPEN")));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load alerts");
    }
  }, []);

  // Poll so newly simulated alerts arrive without the officer reloading.
  useEffect(() => {
    // Initial fetch on mount; the same pattern the investigations list uses.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadAlerts();
    const timer = setInterval(() => void loadAlerts(), POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [loadAlerts]);

  const selectAlert = useCallback(async (alert: BankAlert) => {
    setSelected(alert);
    setLoading(true);
    setError(null);
    try {
      const [custData, txnsData] = await Promise.all([
        alert.customer_id ? getMockBankCustomer(alert.customer_id) : Promise.resolve(null),
        getMockBankTransactions(alert.account_id),
      ]);
      setCustomer(custData as MockCustomer | null);
      setTransactions((txnsData as MockTransaction[]).slice(-10).reverse());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load account data");
    } finally {
      setLoading(false);
    }
  }, []);

  const investigate = async (alert: BankAlert) => {
    setInvestigatingId(alert.alert_id);
    setError(null);
    try {
      const result = await investigateAlertRequest(alert.alert_id);
      // The backend has marked the alert INVESTIGATING; drop it from the
      // actionable queue immediately rather than waiting for the next poll.
      setAlerts((current) => current.filter((a) => a.alert_id !== alert.alert_id));
      router.push(`/investigations/${result.case_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to start investigation");
      setInvestigatingId(null);
    }
  };

  return (
    <div className="flex h-full gap-6">
      {/* Alert queue */}
      <div className="flex w-1/3 flex-col overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-gray-200 bg-gray-50 p-4">
          <h2 className="text-lg font-semibold text-gray-800">Incoming Alerts</h2>
          <span className="rounded-full bg-gray-200 px-2 py-0.5 text-xs font-medium text-gray-700">
            {alerts.length}
          </span>
        </div>

        <div className="flex-1 overflow-y-auto p-2" data-testid="alert-queue">
          {alerts.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center p-6 text-center text-gray-500">
              <Inbox className="mb-3 h-10 w-10 text-gray-300" />
              <p className="text-sm">No open alerts.</p>
              <p className="mt-1 text-xs text-gray-400">
                New alerts appear here automatically as the bank detects them.
              </p>
            </div>
          ) : (
            alerts.map((alert) => (
              <div
                key={alert.alert_id}
                className={`mb-2 rounded-lg border p-4 transition-colors ${
                  selected?.alert_id === alert.alert_id
                    ? "border-blue-200 bg-blue-50 ring-1 ring-blue-500"
                    : "border-gray-200 bg-white hover:bg-gray-50"
                }`}
              >
                <button
                  type="button"
                  onClick={() => void selectAlert(alert)}
                  className="w-full text-left"
                >
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-medium text-gray-900">
                      {alert.customer_name ?? alert.account_id}
                    </h3>
                    <SeverityBadge severity={alert.severity} />
                  </div>
                  <p className="mt-1 line-clamp-2 text-sm text-gray-600">{alert.reason}</p>
                  <p className="mt-1 text-xs text-gray-400">
                    {alert.alert_id}
                    {formatAmount(alert.amount, alert.currency)
                      ? ` · ${formatAmount(alert.amount, alert.currency)}`
                      : ""}
                  </p>
                </button>

                <button
                  type="button"
                  onClick={() => void investigate(alert)}
                  disabled={investigatingId !== null}
                  className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-red-600 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {investigatingId === alert.alert_id ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                      Starting…
                    </>
                  ) : (
                    <>
                      <ShieldAlert className="h-4 w-4" aria-hidden="true" />
                      Investigate
                    </>
                  )}
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Alert detail */}
      <div className="flex flex-1 flex-col overflow-y-auto rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        {error && (
          <div role="alert" className="mb-4 rounded-lg bg-red-50 p-4 text-red-600">
            {error}
          </div>
        )}

        {selected ? (
          loading ? (
            <div className="animate-pulse space-y-4">
              <div className="h-8 w-1/3 rounded bg-gray-200" />
              <div className="h-32 rounded bg-gray-100" />
              <div className="h-64 rounded bg-gray-100" />
            </div>
          ) : (
            <>
              <div className="mb-6">
                <div className="flex items-center gap-2 text-sm font-medium text-red-600">
                  <AlertTriangle className="h-4 w-4" />
                  {selected.alert_id}
                </div>
                <h1 className="mt-1 text-2xl font-bold text-gray-900">
                  {customer?.first_name} {customer?.last_name}
                </h1>
                <p className="mt-1 text-gray-500">
                  Risk Rating: <span className="font-medium">{customer?.risk_rating}</span>
                  {customer?.occupation ? ` | ${customer.occupation}` : ""}
                </p>
                <p className="mt-3 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800">
                  {selected.reason}
                </p>
                <p className="mt-2 text-xs text-gray-400">
                  Triggering transaction: {selected.transaction_id}
                </p>
              </div>

              <div className="mb-6">
                <h2 className="mb-4 text-lg font-semibold text-gray-800">Recent Transactions</h2>
                <div className="overflow-x-auto rounded-lg border border-gray-200">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 font-medium text-gray-600">Date</th>
                        <th className="px-4 py-3 font-medium text-gray-600">Type</th>
                        <th className="px-4 py-3 font-medium text-gray-600">Description</th>
                        <th className="px-4 py-3 text-right font-medium text-gray-600">Amount</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {transactions.map((txn) => (
                        <tr
                          key={txn.transaction_id}
                          className={
                            txn.transaction_id === selected.transaction_id ? "bg-amber-50" : ""
                          }
                        >
                          <td className="px-4 py-3 text-gray-500">
                            {new Date(txn.timestamp).toLocaleDateString()}
                          </td>
                          <td className="px-4 py-3 text-gray-900">{txn.transaction_type}</td>
                          <td className="px-4 py-3 text-gray-900">{txn.description}</td>
                          <td className="px-4 py-3 text-right font-medium text-gray-900">
                            ${txn.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                          </td>
                        </tr>
                      ))}
                      {transactions.length === 0 && (
                        <tr>
                          <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                            No transactions found
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )
        ) : (
          <div className="flex h-full flex-col items-center justify-center text-gray-500">
            <Inbox className="mb-4 h-16 w-16 text-gray-300" />
            <p className="text-lg">Select an alert to view details</p>
          </div>
        )}
      </div>
    </div>
  );
}
