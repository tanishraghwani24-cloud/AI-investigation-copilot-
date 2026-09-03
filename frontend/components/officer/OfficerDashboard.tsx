"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { getMockBankTransactions, getMockBankCustomer, runInvestigationRequest } from "@/services/api";
import { createInvestigation } from "@/services/investigationService";

const KNOWN_ACCOUNTS = [
  { id: "ACC-MOCK-001", customerId: "CUST-MOCK-001", name: "High Risk Activity" },
  { id: "ACC-MOCK-002", customerId: "CUST-MOCK-002", name: "Routine Threshold Alert" },
  { id: "ACC-MOCK-003", customerId: "CUST-MOCK-003", name: "Incomplete KYC Alert" },
];

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

export function OfficerDashboard() {
  const router = useRouter();
  const [selectedAccount, setSelectedAccount] = useState<string | null>(null);
  const [customer, setCustomer] = useState<MockCustomer | null>(null);
  const [transactions, setTransactions] = useState<MockTransaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAccountDetails = useCallback(async (accountId: string, customerId: string) => {
    setSelectedAccount(accountId);
    setLoading(true);
    setError(null);
    try {
      const [custData, txnsData] = await Promise.all([
        getMockBankCustomer(customerId),
        getMockBankTransactions(accountId),
      ]);
      setCustomer(custData as MockCustomer);
      const txnsArray = txnsData as MockTransaction[];
      setTransactions(txnsArray.slice(-10)); // Show last 10 transactions
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Failed to load account data";
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleTriggerInvestigation = async () => {
    if (!selectedAccount) return;
    setCreating(true);
    setError(null);
    try {
      const state = await createInvestigation(selectedAccount);
      await runInvestigationRequest(state.case_id);
      router.push(`/investigations/${state.case_id}`);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Failed to trigger investigation";
      setError(errorMsg);
      setCreating(false);
    }
  };

  return (
    <div className="flex h-full gap-6">
      {/* Sidebar / Alert List */}
      <div className="w-1/3 flex flex-col bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <h2 className="text-lg font-semibold text-gray-800">Incoming Alerts</h2>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {KNOWN_ACCOUNTS.map((acc) => (
            <button
              key={acc.id}
              onClick={() => loadAccountDetails(acc.id, acc.customerId)}
              className={`w-full text-left p-4 mb-2 rounded-lg border transition-colors ${
                selectedAccount === acc.id
                  ? "bg-blue-50 border-blue-200 ring-1 ring-blue-500"
                  : "bg-white border-gray-200 hover:bg-gray-50"
              }`}
            >
              <h3 className="font-medium text-gray-900">{acc.name}</h3>
              <p className="text-sm text-gray-500 mt-1">{acc.id}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Main Panel / Account Details */}
      <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-200 p-6 overflow-y-auto flex flex-col">
        {selectedAccount ? (
          loading ? (
            <div className="animate-pulse space-y-4">
              <div className="h-8 bg-gray-200 rounded w-1/3"></div>
              <div className="h-32 bg-gray-100 rounded"></div>
              <div className="h-64 bg-gray-100 rounded"></div>
            </div>
          ) : error ? (
            <div className="text-red-600 bg-red-50 p-4 rounded-lg">{error}</div>
          ) : (
            <>
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">
                    {customer?.first_name} {customer?.last_name}
                  </h1>
                  <p className="text-gray-500 mt-1">
                    Risk Rating: <span className="font-medium">{customer?.risk_rating}</span> | {customer?.occupation}
                  </p>
                </div>
                <button
                  onClick={handleTriggerInvestigation}
                  disabled={creating}
                  className="px-6 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
                >
                  {creating ? "Triggering..." : "Trigger Investigation"}
                </button>
              </div>

              <div className="mb-6">
                <h2 className="text-lg font-semibold text-gray-800 mb-4">Recent Transactions</h2>
                <div className="overflow-x-auto rounded-lg border border-gray-200">
                  <table className="w-full text-sm text-left">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 font-medium text-gray-600">Date</th>
                        <th className="px-4 py-3 font-medium text-gray-600">Type</th>
                        <th className="px-4 py-3 font-medium text-gray-600">Description</th>
                        <th className="px-4 py-3 font-medium text-gray-600 text-right">Amount</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {transactions.map((txn) => (
                        <tr key={txn.transaction_id}>
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
          <div className="h-full flex flex-col items-center justify-center text-gray-500">
            <svg className="w-16 h-16 mb-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            <p className="text-lg">Select an alert to view details</p>
          </div>
        )}
      </div>
    </div>
  );
}
