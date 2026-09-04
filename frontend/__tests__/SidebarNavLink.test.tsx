import { render, screen } from "@testing-library/react";
import { usePathname } from "next/navigation";
import { SidebarNavLink } from "@/components/layout/SidebarNavLink";
import { NAV_ITEMS } from "@/components/layout/navItems";

jest.mock("next/navigation", () => ({
  usePathname: jest.fn(),
}));

const mockUsePathname = usePathname as jest.Mock;

const [officerInbox, investigations, , settings] = NAV_ITEMS;

describe("SidebarNavLink active state", () => {
  it("marks the current route active", () => {
    mockUsePathname.mockReturnValue("/investigations");
    render(<SidebarNavLink item={investigations} />);

    expect(screen.getByRole("link", { name: "Investigations" })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });

  it("leaves non-matching routes inactive", () => {
    mockUsePathname.mockReturnValue("/investigations");
    render(<SidebarNavLink item={officerInbox} />);

    expect(screen.getByRole("link", { name: "Officer Inbox" })).not.toHaveAttribute(
      "aria-current",
    );
  });

  it("keeps Investigations active on a nested investigation detail route", () => {
    mockUsePathname.mockReturnValue("/investigations/CASE-104");
    render(<SidebarNavLink item={investigations} />);

    expect(screen.getByRole("link", { name: "Investigations" })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });

  it("never marks Settings active, since '#' has no real route to match", () => {
    mockUsePathname.mockReturnValue("/");
    render(<SidebarNavLink item={settings} />);

    expect(screen.getByRole("link", { name: "Settings" })).not.toHaveAttribute(
      "aria-current",
    );
  });
});
