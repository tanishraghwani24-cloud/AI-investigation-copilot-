import { render, screen, waitFor } from "@testing-library/react";
import {
  InvestigatorAvatar,
  InvestigatorAvatarGroup,
} from "@/components/investigators/InvestigatorAvatar";
import { initialOf } from "@/components/auth/InvestigatorProvider";
import { InvestigationList } from "@/components/investigations/InvestigationList";
import { listInvestigations } from "@/services/investigationService";
import { listAssignmentsRequest } from "@/services/api";
import type { Investigator } from "@/types";

jest.mock("@/services/investigationService", () => ({ listInvestigations: jest.fn() }));
jest.mock("@/services/api", () => ({ listAssignmentsRequest: jest.fn() }));
const signedIn = {
  user_id: "11111111-1111-1111-1111-111111111111",
  full_name: "Rahul Sharma",
  email: "rahul.sharma@hollabank.com",
  initial: "R",
};

// Mutable so tests can reproduce the moment before a session has resolved.
let mockAuth: {
  investigator: typeof signedIn | null;
  loading: boolean;
  authConfigured: boolean;
} = { investigator: signedIn, loading: false, authConfigured: true };

jest.mock("@/components/auth/InvestigatorProvider", () => ({
  ...jest.requireActual("@/components/auth/InvestigatorProvider"),
  useInvestigator: () => ({ ...mockAuth, signIn: jest.fn(), signOut: jest.fn() }),
}));

const rahul: Investigator = {
  user_id: "11111111-1111-1111-1111-111111111111",
  full_name: "Rahul Sharma",
  email: "rahul.sharma@hollabank.com",
  initial: "R",
};
const priya: Investigator = {
  user_id: "22222222-2222-2222-2222-222222222222",
  full_name: "Priya Nair",
  email: "priya.nair@hollabank.com",
  initial: "P",
};

describe("initialOf", () => {
  it("derives the initial from the name rather than hardcoding it", () => {
    expect(initialOf("Rahul Sharma")).toBe("R");
    expect(initialOf("priya nair")).toBe("P");
    expect(initialOf("daniel okafor")).toBe("D");
  });

  it("falls back safely for a missing name", () => {
    expect(initialOf(undefined)).toBe("?");
    expect(initialOf("   ")).toBe("?");
  });
});

describe("InvestigatorAvatar", () => {
  it("renders the investigator's initial", () => {
    render(<InvestigatorAvatar investigator={rahul} />);

    expect(screen.getByRole("img", { name: /Rahul Sharma/ })).toHaveTextContent("R");
  });

  it("carries the full name in the hover tooltip", () => {
    // The tooltip is revealed by a CSS :hover rule, which jsdom does not
    // evaluate; what is testable is that the element exists with the right
    // text, and that the native title gives the same name on hover.
    render(<InvestigatorAvatar investigator={rahul} context="is currently working on this case" />);

    expect(screen.getByRole("tooltip")).toHaveTextContent(
      "Rahul Sharma is currently working on this case",
    );
    expect(screen.getByRole("img", { name: /Rahul Sharma/ })).toHaveAttribute(
      "title", "Rahul Sharma is currently working on this case",
    );
  });

  it("exposes the name to assistive tech and native hover", () => {
    render(<InvestigatorAvatar investigator={priya} />);

    const avatar = screen.getByRole("img", { name: "Priya Nair" });
    expect(avatar).toHaveAttribute("title", "Priya Nair");
  });

  it("gives different investigators different initials", () => {
    render(
      <>
        <InvestigatorAvatar investigator={rahul} />
        <InvestigatorAvatar investigator={priya} />
      </>,
    );

    expect(screen.getByRole("img", { name: "Rahul Sharma" })).toHaveTextContent("R");
    expect(screen.getByRole("img", { name: "Priya Nair" })).toHaveTextContent("P");
  });
});

describe("InvestigatorAvatarGroup", () => {
  it("renders nothing when nobody is present", () => {
    const { container } = render(<InvestigatorAvatarGroup investigators={[]} />);

    expect(container).toBeEmptyDOMElement();
  });

  it("renders a fallback when one is supplied", () => {
    render(<InvestigatorAvatarGroup investigators={[]} fallback={<span>Unassigned</span>} />);

    expect(screen.getByText("Unassigned")).toBeInTheDocument();
  });

  it("supports several investigators for future multi-presence", () => {
    render(<InvestigatorAvatarGroup investigators={[rahul, priya]} />);

    expect(screen.getByRole("img", { name: "Rahul Sharma" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Priya Nair" })).toBeInTheDocument();
  });
});

describe("Investigations page investigator column", () => {
  const investigation = (caseId: string) => ({
    case_id: caseId,
    customer_name: "Test Customer",
    current_stage: "DONE",
    risk_score: 0.8,
    created_at: "2026-09-04T10:00:00Z",
    alert_reason: "Large transaction",
  });

  beforeEach(() => {
    jest.resetAllMocks();
    mockAuth = { investigator: signedIn, loading: false, authConfigured: true };
    (listInvestigations as jest.Mock).mockResolvedValue([investigation("CASE-102")]);
    (listAssignmentsRequest as jest.Mock).mockResolvedValue([
      { case_id: "CASE-102", investigator: rahul },
    ]);
  });

  it("adds an Investigator column without disturbing the existing ones", async () => {
    render(<InvestigationList />);

    await waitFor(() => expect(screen.getByText("Investigator")).toBeInTheDocument());
    for (const heading of ["Investigation ID", "Customer Name", "Status", "Risk Score", "Created Date"]) {
      expect(screen.getByText(heading)).toBeInTheDocument();
    }
    expect(screen.getByText("CASE-102")).toBeInTheDocument();
  });

  it("shows the historical investigator who handled the case", async () => {
    render(<InvestigationList />);

    const avatar = await screen.findByRole("img", { name: /Rahul Sharma/ });
    expect(avatar).toHaveTextContent("R");
    expect(avatar).toHaveAttribute("title", "Rahul Sharma handled this investigation");
  });

  it("shows different investigators for different cases", async () => {
    (listInvestigations as jest.Mock).mockResolvedValue([
      investigation("CASE-102"), investigation("CASE-103"),
    ]);
    (listAssignmentsRequest as jest.Mock).mockResolvedValue([
      { case_id: "CASE-102", investigator: rahul },
      { case_id: "CASE-103", investigator: priya },
    ]);
    render(<InvestigationList />);

    expect(await screen.findByRole("img", { name: /Rahul Sharma/ })).toHaveTextContent("R");
    expect(screen.getByRole("img", { name: /Priya Nair/ })).toHaveTextContent("P");
  });

  it("shows legacy cases as Unassigned rather than inventing an investigator", async () => {
    (listAssignmentsRequest as jest.Mock).mockResolvedValue([
      { case_id: "CASE-102", investigator: null },
    ]);
    render(<InvestigationList />);

    await waitFor(() => expect(screen.getByText("Unassigned")).toBeInTheDocument());
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("still renders the table when attribution cannot be loaded", async () => {
    (listAssignmentsRequest as jest.Mock).mockRejectedValue(new Error("offline"));
    render(<InvestigationList />);

    await waitFor(() => expect(screen.getByText("CASE-102")).toBeInTheDocument());
    expect(screen.getByText("Unassigned")).toBeInTheDocument();
  });
});

describe("attribution fetch timing", () => {
  const investigation = {
    case_id: "CASE-102", customer_name: "Test Customer", current_stage: "DONE",
    risk_score: 0.8, created_at: "2026-09-04T10:00:00Z", alert_reason: "Large transaction",
  };

  beforeEach(() => {
    jest.resetAllMocks();
    (listInvestigations as jest.Mock).mockResolvedValue([investigation]);
    (listAssignmentsRequest as jest.Mock).mockResolvedValue([
      { case_id: "CASE-102", investigator: rahul },
    ]);
  });

  it("does not request attribution before the session has resolved", async () => {
    // Firing early sent an unauthenticated request, which 401d and left every
    // case reading "Unassigned" with no retry.
    mockAuth = { investigator: null, loading: true, authConfigured: true };

    render(<InvestigationList />);

    await waitFor(() => expect(screen.getByText("CASE-102")).toBeInTheDocument());
    expect(listAssignmentsRequest).not.toHaveBeenCalled();
  });

  it("does not request attribution when nobody is signed in", async () => {
    mockAuth = { investigator: null, loading: false, authConfigured: true };

    render(<InvestigationList />);

    await waitFor(() => expect(screen.getByText("CASE-102")).toBeInTheDocument());
    expect(listAssignmentsRequest).not.toHaveBeenCalled();
    expect(screen.getByText("Unassigned")).toBeInTheDocument();
  });

  it("fetches attribution once the investigator is available", async () => {
    mockAuth = { investigator: signedIn, loading: false, authConfigured: true };

    render(<InvestigationList />);

    expect(await screen.findByRole("img", { name: /Rahul Sharma/ })).toHaveTextContent("R");
    expect(listAssignmentsRequest).toHaveBeenCalledTimes(1);
  });
});
