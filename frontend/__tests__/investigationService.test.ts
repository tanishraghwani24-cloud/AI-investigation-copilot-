import { CurrentStage } from "@/types";
import { listInvestigationsRequest } from "@/services/api";
import { listInvestigations } from "@/services/investigationService";

jest.mock("@/services/api", () => ({
  listInvestigationsRequest: jest.fn(),
  createInvestigationRequest: jest.fn(),
  getInvestigationRequest: jest.fn(),
}));

const investigation = (caseId: string, createdAt: string) => ({
  case_id: caseId,
  current_stage: CurrentStage.CONTEXT,
  created_at: createdAt,
  updated_at: createdAt,
  errors: [],
  case_input: { customer_profile: { customer_id: "CUST", name: "Test" }, transactions: [] },
});

describe("listInvestigations ordering", () => {
  it("sorts by created/triggered timestamp descending, newest first", async () => {
    (listInvestigationsRequest as jest.Mock).mockResolvedValue([
      investigation("CASE-OLDEST", "2026-09-01T00:00:00.000Z"),
      investigation("CASE-NEWEST", "2026-09-03T00:00:00.000Z"),
      investigation("CASE-MIDDLE", "2026-09-02T00:00:00.000Z"),
    ]);

    const result = await listInvestigations();

    expect(result.map((item) => item.case_id)).toEqual([
      "CASE-NEWEST",
      "CASE-MIDDLE",
      "CASE-OLDEST",
    ]);
  });

  it("puts a newly created investigation at the top immediately", async () => {
    (listInvestigationsRequest as jest.Mock).mockResolvedValue([
      investigation("CASE-EXISTING", "2026-09-01T00:00:00.000Z"),
      investigation("CASE-JUST-CREATED", "2026-09-04T12:00:00.000Z"),
    ]);

    const result = await listInvestigations();

    expect(result[0].case_id).toBe("CASE-JUST-CREATED");
  });
});
