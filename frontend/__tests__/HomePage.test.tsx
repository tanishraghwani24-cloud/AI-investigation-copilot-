import { render, screen } from "@testing-library/react";
import Home from "@/app/page";

// jsdom has no real WebGL context, so MagicRings' internal try/catch takes
// the "unsupported" branch here — this only confirms the hero still renders
// its text/button correctly with the background layer wired in, not the
// WebGL rendering itself.
describe("Home hero", () => {
  it("renders the subtitle and a working link to the Officer Inbox", () => {
    render(<Home />);

    expect(
      screen.getByText("Fraud Investigation & Decision Intelligence Platform"),
    ).toBeInTheDocument();

    // Two links share this label: the hero CTA and the closing CTA at the
    // bottom of the landing sections.
    const links = screen.getAllByRole("link", { name: "Go to Officer Inbox" });
    expect(links.length).toBeGreaterThan(0);
    for (const link of links) {
      expect(link).toHaveAttribute("href", "/officer");
    }
  });

  it("keeps the background layer non-interactive so it cannot block clicks", () => {
    const { container } = render(<Home />);
    const background = container.querySelector('[aria-hidden="true"]');

    expect(background).toHaveClass("pointer-events-none");
  });

  it("renders the landing storytelling sections below the hero", () => {
    render(<Home />);

    expect(
      screen.getByText("From Risk Signal to Defensible Decision."),
    ).toBeInTheDocument();
    expect(screen.getByText("Know who is working on what.")).toBeInTheDocument();
    expect(
      screen.getByText("Protected by design. Traceable by default."),
    ).toBeInTheDocument();
  });
});
