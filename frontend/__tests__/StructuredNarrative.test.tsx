import { render, screen } from "@testing-library/react";
import {
  StructuredNarrative,
  parseNarrative,
} from "@/components/reports/StructuredNarrative";
import { ReportViewer } from "@/components/ReportViewer";
import { AgentStatus } from "@/types";

/**
 * The backend already emits the narrative as light Markdown. Rendering it in a
 * single <p> collapsed every newline into one wall of text; these tests pin
 * that the existing structure is restored without altering the content.
 */

// Shaped exactly like the real backend narrative (## headings, 0/2/4 indents).
const NARRATIVE = [
  "## Final synthesis",
  "This report consolidates the available case material for case CASE-X.",
  "",
  "## Case information",
  "- Case ID: CASE-X",
  "- Transactions:",
  "  - TXN-001: 48000 USD; WIRE",
  "  - TXN-002: 52500 USD; WIRE",
  "",
  "## Compliance and evidence traceability",
  "- BSA-1020.320",
  "  - Regulation: Suspicious Activity Reporting",
  "    - Violation status: NOT ESTABLISHED",
].join("\n");

describe("parseNarrative", () => {
  it("splits headings, paragraphs and lists instead of one blob", () => {
    const blocks = parseNarrative(NARRATIVE);

    expect(blocks.filter((b) => b.kind === "heading").map((b) => b.text)).toEqual([
      "Final synthesis",
      "Case information",
      "Compliance and evidence traceability",
    ]);
    expect(blocks.some((b) => b.kind === "paragraph")).toBe(true);
    expect(blocks.some((b) => b.kind === "list")).toBe(true);
  });

  it("nests bullets by their indent depth", () => {
    const blocks = parseNarrative(NARRATIVE);
    const caseList = blocks.filter((b) => b.kind === "list")[0];
    if (caseList.kind !== "list") throw new Error("expected a list block");

    const transactions = caseList.items.find((i) => i.text === "Transactions:");
    expect(transactions?.children.map((c) => c.text)).toEqual([
      "TXN-001: 48000 USD; WIRE",
      "TXN-002: 52500 USD; WIRE",
    ]);
  });

  it("nests a third level under its parent", () => {
    const blocks = parseNarrative(NARRATIVE);
    const complianceList = blocks.filter((b) => b.kind === "list")[1];
    if (complianceList.kind !== "list") throw new Error("expected a list block");

    const regulation = complianceList.items[0].children[0];
    expect(regulation.text).toBe("Regulation: Suspicious Activity Reporting");
    expect(regulation.children[0].text).toBe("Violation status: NOT ESTABLISHED");
  });

  it("keeps every line of the source narrative", () => {
    const blocks = parseNarrative(NARRATIVE);
    const collect = (items: { text: string; children: never[] | { text: string; children: unknown[] }[] }[]): string[] =>
      items.flatMap((i) => [i.text, ...collect(i.children as never)]);
    const rendered = blocks.flatMap((b) =>
      b.kind === "list" ? collect(b.items as never) : [b.text],
    );

    const sourceLines = NARRATIVE.split("\n")
      .filter((l) => l.trim())
      .map((l) => l.replace(/^\s*(#{1,6}\s+|[-*]\s+)/, "").trim());
    expect(rendered).toEqual(sourceLines);
  });

  it("renders an unrecognised line verbatim rather than dropping it", () => {
    const blocks = parseNarrative("Just a plain sentence with a colon: here.");

    expect(blocks).toEqual([
      { kind: "paragraph", text: "Just a plain sentence with a colon: here." },
    ]);
  });

  it("handles an empty narrative", () => {
    expect(parseNarrative("")).toEqual([]);
  });
});

describe("StructuredNarrative rendering", () => {
  it("renders headings as elements, not inline text", () => {
    render(<StructuredNarrative narrative={NARRATIVE} />);

    expect(screen.getByText("Final synthesis").tagName).toBe("H5");
    expect(screen.getByText("Case information").tagName).toBe("H5");
  });

  it("renders bullets as real list items", () => {
    const { container } = render(<StructuredNarrative narrative={NARRATIVE} />);

    expect(container.querySelectorAll("li").length).toBeGreaterThanOrEqual(6);
    expect(container.querySelectorAll("ul").length).toBeGreaterThanOrEqual(3);
  });
});

describe("ReportViewer", () => {
  const report = {
    status: AgentStatus.COMPLETED,
    executive_summary: "Summary of the case.",
    detailed_narrative: NARRATIVE,
    generated_at: "2026-09-04T10:00:00Z",
  };

  it("renders the narrative structured rather than as one paragraph", () => {
    const { container } = render(<ReportViewer caseId="CASE-X" report={report} />);

    expect(screen.getByTestId("structured-narrative")).toBeInTheDocument();
    expect(container.querySelectorAll("li").length).toBeGreaterThan(0);
    expect(screen.getByText("Summary of the case.")).toBeInTheDocument();
  });

  it("still offers the download link unchanged", () => {
    render(<ReportViewer caseId="CASE-X" report={report} />);

    expect(screen.getByRole("link", { name: /download report/i })).toHaveAttribute(
      "href",
      "/api/proxy/investigations/CASE-X/report/download",
    );
  });

  it("shows the empty state when there is no report", () => {
    render(<ReportViewer caseId="CASE-X" report={null} />);

    expect(screen.getByText("No report available")).toBeInTheDocument();
    expect(screen.queryByTestId("structured-narrative")).not.toBeInTheDocument();
  });
});
