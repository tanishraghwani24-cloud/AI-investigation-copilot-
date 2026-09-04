import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { OfficerDashboard } from "@/components/officer/OfficerDashboard";
import {
  getMockBankCustomer,
  getMockBankTransactions,
  investigateAlertRequest,
  listAlertsRequest,
  listPresenceRequest,
} from "@/services/api";

const push = jest.fn();

// Mutable so individual tests can switch between signed-in and unconfigured.
let mockAuth = {
  investigator: {
    user_id: "11111111-1111-1111-1111-111111111111",
    full_name: "Rahul Sharma",
    email: "rahul.sharma@hollabank.com",
    initial: "R",
  },
  loading: false,
  authConfigured: true,
  signIn: jest.fn(),
  signOut: jest.fn(),
};

jest.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));
jest.mock("@/services/api", () => ({
  listAlertsRequest: jest.fn(),
  investigateAlertRequest: jest.fn(),
  getMockBankCustomer: jest.fn(),
  getMockBankTransactions: jest.fn(),
  listPresenceRequest: jest.fn(),
}));
jest.mock("@/components/auth/InvestigatorProvider", () => ({
  useInvestigator: () => mockAuth,
}));

const alert = (id: string, extra: Record<string, unknown> = {}) => ({
  alert_id: id,
  transaction_id: `TXN-SIM-${id.slice(-4)}`,
  account_id: "ACC-MOCK-001",
  customer_id: "CUST-MOCK-001",
  customer_name: "Test Customer",
  reason: "Large transaction of 48,000.00 (WIRE) detected.",
  severity: "HIGH",
  risk_score: 0.48,
  status: "OPEN",
  case_id: null,
  amount: 48000,
  currency: "USD",
  transaction_type: "WIRE",
  created_at: "2026-09-04T10:00:00Z",
  ...extra,
});

describe("Officer Inbox", () => {
  beforeEach(() => {
    jest.resetAllMocks();
    (listAlertsRequest as jest.Mock).mockResolvedValue([alert("ALERT-0001")]);
    (getMockBankCustomer as jest.Mock).mockResolvedValue({
      first_name: "Test", last_name: "Customer", risk_rating: "HIGH",
    });
    (getMockBankTransactions as jest.Mock).mockResolvedValue([]);
    (listPresenceRequest as jest.Mock).mockResolvedValue([]);
    mockAuth = { ...mockAuth, authConfigured: true };
  });

  afterEach(() => jest.useRealTimers());

  it("shows alerts served by the backend", async () => {
    render(<OfficerDashboard />);

    expect(await screen.findByText("ALERT-0001", { exact: false })).toBeInTheDocument();
    expect(screen.getByText(/Large transaction/)).toBeInTheDocument();
    expect(listAlertsRequest).toHaveBeenCalledWith("OPEN");
  });

  it("gives every actionable alert an Investigate action", async () => {
    (listAlertsRequest as jest.Mock).mockResolvedValue([
      alert("ALERT-0001"), alert("ALERT-0002"),
    ]);
    render(<OfficerDashboard />);

    await waitFor(() =>
      expect(screen.getAllByRole("button", { name: /investigate/i })).toHaveLength(2),
    );
  });

  it("polls so newly generated alerts appear without a manual refresh", async () => {
    jest.useFakeTimers();
    (listAlertsRequest as jest.Mock)
      .mockResolvedValueOnce([alert("ALERT-0001")])
      .mockResolvedValue([alert("ALERT-0002"), alert("ALERT-0001")]);

    render(<OfficerDashboard />);
    await waitFor(() => expect(listAlertsRequest).toHaveBeenCalledTimes(1));

    await act(async () => {
      jest.advanceTimersByTime(10_000);
    });

    await waitFor(() => expect(listAlertsRequest).toHaveBeenCalledTimes(2));
    expect(screen.getByText("ALERT-0002", { exact: false })).toBeInTheDocument();
  });

  it("escalates the clicked alert and opens the resulting case", async () => {
    (investigateAlertRequest as jest.Mock).mockResolvedValue({
      alert_id: "ALERT-0001", case_id: "CASE-ALERT-0001", created: true,
    });
    render(<OfficerDashboard />);
    fireEvent.click(await screen.findByRole("button", { name: /investigate/i }));

    await waitFor(() => expect(push).toHaveBeenCalledWith("/investigations/CASE-ALERT-0001"));
    expect(investigateAlertRequest).toHaveBeenCalledWith("ALERT-0001");
  });

  it("removes the alert from the actionable queue once escalated", async () => {
    (investigateAlertRequest as jest.Mock).mockResolvedValue({
      alert_id: "ALERT-0001", case_id: "CASE-ALERT-0001", created: true,
    });
    render(<OfficerDashboard />);
    fireEvent.click(await screen.findByRole("button", { name: /investigate/i }));

    await waitFor(() => expect(screen.getByText("No open alerts.")).toBeInTheDocument());
  });

  it("shows a loading state and blocks double submission while starting", async () => {
    let resolve: (value: unknown) => void = () => {};
    (investigateAlertRequest as jest.Mock).mockReturnValue(
      new Promise((r) => {
        resolve = r;
      }),
    );
    render(<OfficerDashboard />);
    fireEvent.click(await screen.findByRole("button", { name: /investigate/i }));

    await waitFor(() =>
      expect(screen.getByRole("button", { name: /starting/i })).toBeDisabled(),
    );
    resolve({ alert_id: "ALERT-0001", case_id: "CASE-ALERT-0001", created: true });
  });

  it("keeps the alert in the queue when escalation fails", async () => {
    (investigateAlertRequest as jest.Mock).mockRejectedValue(new Error("Backend unavailable"));
    render(<OfficerDashboard />);
    fireEvent.click(await screen.findByRole("button", { name: /investigate/i }));

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent("Backend unavailable"),
    );
    expect(push).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: /investigate/i })).toBeEnabled();
  });

  it("renders an empty inbox without error", async () => {
    (listAlertsRequest as jest.Mock).mockResolvedValue([]);
    render(<OfficerDashboard />);

    expect(await screen.findByText("No open alerts.")).toBeInTheDocument();
  });

  it("orders the queue HIGH before MEDIUM before LOW regardless of API order", async () => {
    (listAlertsRequest as jest.Mock).mockResolvedValue([
      alert("ALERT-LOW", { severity: "LOW", created_at: "2026-09-04T12:00:00Z" }),
      alert("ALERT-HIGH", { severity: "HIGH", created_at: "2026-09-04T09:00:00Z" }),
      alert("ALERT-MEDIUM", { severity: "MEDIUM", created_at: "2026-09-04T10:00:00Z" }),
    ]);
    render(<OfficerDashboard />);

    const ids = await screen.findAllByText(/^ALERT-/, { exact: false });
    expect(ids.map((el) => el.textContent)).toEqual([
      expect.stringContaining("ALERT-HIGH"),
      expect.stringContaining("ALERT-MEDIUM"),
      expect.stringContaining("ALERT-LOW"),
    ]);
  });

  it("breaks a severity tie by showing the newest alert first", async () => {
    (listAlertsRequest as jest.Mock).mockResolvedValue([
      alert("ALERT-OLDER", { severity: "HIGH", created_at: "2026-09-04T08:00:00Z" }),
      alert("ALERT-NEWER", { severity: "HIGH", created_at: "2026-09-04T09:30:00Z" }),
    ]);
    render(<OfficerDashboard />);

    const ids = await screen.findAllByText(/^ALERT-/, { exact: false });
    expect(ids.map((el) => el.textContent)).toEqual([
      expect.stringContaining("ALERT-NEWER"),
      expect.stringContaining("ALERT-OLDER"),
    ]);
  });

  it("re-sorts by severity when a new alert arrives on poll", async () => {
    jest.useFakeTimers();
    (listAlertsRequest as jest.Mock)
      .mockResolvedValueOnce([alert("ALERT-MEDIUM", { severity: "MEDIUM" })])
      .mockResolvedValue([
        alert("ALERT-MEDIUM", { severity: "MEDIUM" }),
        alert("ALERT-HIGH", { severity: "HIGH", created_at: "2026-09-04T11:00:00Z" }),
      ]);

    render(<OfficerDashboard />);
    await waitFor(() => expect(listAlertsRequest).toHaveBeenCalledTimes(1));

    await act(async () => {
      jest.advanceTimersByTime(10_000);
    });
    await waitFor(() => expect(listAlertsRequest).toHaveBeenCalledTimes(2));

    const ids = await screen.findAllByText(/^ALERT-/, { exact: false });
    expect(ids.map((el) => el.textContent)).toEqual([
      expect.stringContaining("ALERT-HIGH"),
      expect.stringContaining("ALERT-MEDIUM"),
    ]);
  });

  describe("collaboration presence", () => {
    const rahul = {
      user_id: "11111111-1111-1111-1111-111111111111",
      full_name: "Rahul Sharma",
      email: "rahul.sharma@hollabank.com",
      initial: "R",
    };

    it("shows the avatar of the investigator working a case", async () => {
      (listAlertsRequest as jest.Mock).mockImplementation((status: string) =>
        Promise.resolve(
          status === "INVESTIGATING"
            ? [alert("ALERT-BUSY", { status: "INVESTIGATING", case_id: "CASE-ALERT-BUSY" })]
            : [],
        ),
      );
      (listPresenceRequest as jest.Mock).mockResolvedValue([
        { case_id: "CASE-ALERT-BUSY", investigators: [rahul] },
      ]);

      render(<OfficerDashboard />);

      const avatar = await screen.findByRole("img", { name: /Rahul Sharma/ });
      expect(avatar).toHaveTextContent("R");
      expect(avatar).toHaveAttribute(
        "title", "Rahul Sharma is currently working on this case",
      );
    });

    it("does not offer Investigate on a case someone already picked up", async () => {
      (listAlertsRequest as jest.Mock).mockImplementation((status: string) =>
        Promise.resolve(
          status === "INVESTIGATING"
            ? [alert("ALERT-BUSY", { status: "INVESTIGATING", case_id: "CASE-ALERT-BUSY" })]
            : [],
        ),
      );
      (listPresenceRequest as jest.Mock).mockResolvedValue([
        { case_id: "CASE-ALERT-BUSY", investigators: [rahul] },
      ]);

      render(<OfficerDashboard />);

      await waitFor(() =>
        expect(screen.getByText("Investigation in progress")).toBeInTheDocument(),
      );
      expect(screen.queryByRole("button", { name: /^investigate$/i })).not.toBeInTheDocument();
    });

    it("shows no avatar on an alert nobody is working", async () => {
      render(<OfficerDashboard />);

      await screen.findByRole("button", { name: /investigate/i });
      expect(screen.queryByRole("img", { name: /Rahul Sharma/ })).not.toBeInTheDocument();
    });

    it("keeps the queue working when presence cannot be loaded", async () => {
      (listPresenceRequest as jest.Mock).mockRejectedValue(new Error("offline"));

      render(<OfficerDashboard />);

      expect(await screen.findByRole("button", { name: /investigate/i })).toBeInTheDocument();
    });

    it("does not request presence when auth is not configured", async () => {
      mockAuth = { ...mockAuth, authConfigured: false };

      render(<OfficerDashboard />);

      await screen.findByRole("button", { name: /investigate/i });
      expect(listPresenceRequest).not.toHaveBeenCalled();
    });
  });
});
