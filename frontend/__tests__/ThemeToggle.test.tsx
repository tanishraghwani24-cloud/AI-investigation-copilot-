import { fireEvent, render, screen } from "@testing-library/react";
import { THEME_STORAGE_KEY, ThemeToggle } from "@/components/ui/ThemeToggle";

describe("ThemeToggle", () => {
  beforeEach(() => {
    document.documentElement.classList.remove("dark");
    window.localStorage.clear();
  });

  it("turns dark mode on and off by toggling the class Tailwind keys off", () => {
    render(<ThemeToggle />);
    const button = screen.getByRole("button", { name: /toggle dark mode/i });

    fireEvent.click(button);
    expect(document.documentElement).toHaveClass("dark");

    fireEvent.click(button);
    expect(document.documentElement).not.toHaveClass("dark");
  });

  it("persists the choice so a reload keeps the theme", () => {
    render(<ThemeToggle />);
    const button = screen.getByRole("button", { name: /toggle dark mode/i });

    fireEvent.click(button);
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe("dark");

    fireEvent.click(button);
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe("light");
  });

  it("still switches the theme when storage is unavailable", () => {
    const setItem = jest
      .spyOn(Storage.prototype, "setItem")
      .mockImplementation(() => {
        throw new Error("storage disabled");
      });

    render(<ThemeToggle />);
    fireEvent.click(screen.getByRole("button", { name: /toggle dark mode/i }));

    expect(document.documentElement).toHaveClass("dark");
    setItem.mockRestore();
  });
});
