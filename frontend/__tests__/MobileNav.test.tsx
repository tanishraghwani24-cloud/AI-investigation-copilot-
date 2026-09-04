import { fireEvent, render, screen } from "@testing-library/react";
import { MobileNav } from "@/components/layout/MobileNav";
import { NAV_ITEMS } from "@/components/layout/navItems";

describe("MobileNav", () => {
  it("keeps the drawer closed until the hamburger is pressed", () => {
    render(<MobileNav />);

    expect(screen.queryByRole("link", { name: "Officer Inbox" })).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: /open navigation menu/i }));

    expect(screen.getByRole("link", { name: "Officer Inbox" })).toBeInTheDocument();
  });

  it("offers the same destinations as the desktop sidebar", () => {
    render(<MobileNav />);
    fireEvent.click(screen.getByRole("button", { name: /open navigation menu/i }));

    for (const item of NAV_ITEMS) {
      expect(screen.getByRole("link", { name: item.label })).toHaveAttribute(
        "href",
        item.href,
      );
    }
  });

  it("closes again when a destination is chosen", () => {
    render(<MobileNav />);
    fireEvent.click(screen.getByRole("button", { name: /open navigation menu/i }));

    fireEvent.click(screen.getByRole("link", { name: "Reports" }));

    expect(screen.queryByRole("link", { name: "Reports" })).toBeNull();
  });
});
