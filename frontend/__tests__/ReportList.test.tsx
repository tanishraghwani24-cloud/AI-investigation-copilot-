import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { ReportList } from "@/components/reports/ReportList";
import { listReports } from "@/services/reportService";

jest.mock("@/services/reportService", () => ({ listReports: jest.fn() }));

describe("ReportList downloads", () => {
  beforeEach(() => {
    jest.resetAllMocks();
    (listReports as jest.Mock).mockResolvedValue([{
      caseId: "CASE-PDF-001", customerName: "Ada Lovelace", riskScore: 0.9,
      recommendation: "BLOCK", createdAt: "2026-09-01T10:00:00Z", updatedAt: "2026-09-01T10:00:00Z",
    }]);
    URL.createObjectURL = jest.fn(() => "blob:report");
    URL.revokeObjectURL = jest.fn();
    jest.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
  });

  afterEach(() => jest.restoreAllMocks());

  it("downloads only a validated PDF response from the protected proxy path", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ "content-type": "application/pdf" }),
      blob: async () => new Blob(["%PDF-1.4"]),
    });
    render(<ReportList />);
    const button = await screen.findByRole("button", { name: "Download" });

    fireEvent.click(button);

    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(
      "/api/proxy/investigations/CASE-PDF-001/report/download.pdf",
    ));
    expect(URL.createObjectURL).toHaveBeenCalled();
  });

  it("does not download an error JSON response", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      headers: new Headers({ "content-type": "application/json" }),
    });
    render(<ReportList />);
    fireEvent.click(await screen.findByRole("button", { name: "Download" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("PDF report is unavailable");
    expect(URL.createObjectURL).not.toHaveBeenCalled();
  });
});
