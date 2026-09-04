import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import LoginPage from "@/app/login/page";
import { useInvestigator } from "@/components/auth/InvestigatorProvider";

const push = jest.fn();
const replace = jest.fn();
const refresh = jest.fn();
const signInWithOfficerId = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push, replace, refresh }),
  useSearchParams: () => new URLSearchParams(mockSearch),
}));
jest.mock("@/components/auth/InvestigatorProvider", () => ({
  useInvestigator: jest.fn(),
}));

let mockSearch = "";

describe("Officer ID login", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearch = "";
    (useInvestigator as jest.Mock).mockReturnValue({
      signInWithOfficerId,
      authConfigured: true,
    });
  });

  it("asks for an Officer ID, not an email address", () => {
    render(<LoginPage />);

    expect(screen.getByLabelText("Officer ID")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("OFF-001")).toBeInTheDocument();
    expect(screen.queryByLabelText("Email")).not.toBeInTheDocument();
  });

  it("never shows an internal email address anywhere on the form", () => {
    const { container } = render(<LoginPage />);

    expect(container.textContent).not.toMatch(/@/);
    expect(container.querySelector('input[type="email"]')).toBeNull();
  });

  it("signs in with the Officer ID and password", async () => {
    signInWithOfficerId.mockResolvedValue(undefined);
    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("Officer ID"), { target: { value: "OFF-004" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "secret" } });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() =>
      expect(signInWithOfficerId).toHaveBeenCalledWith("OFF-004", "secret"),
    );
  });

  it("lands on the Officer Box after a successful sign-in", async () => {
    signInWithOfficerId.mockResolvedValue(undefined);
    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("Officer ID"), { target: { value: "OFF-004" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "secret" } });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/officer"));
    // Server Components must re-render against the new session cookies.
    expect(refresh).toHaveBeenCalled();
  });

  it("returns the officer to where the gate intercepted them", async () => {
    mockSearch = "next=%2Finvestigations";
    signInWithOfficerId.mockResolvedValue(undefined);
    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("Officer ID"), { target: { value: "OFF-004" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "secret" } });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/investigations"));
  });

  it("shows a failure without revealing which field was wrong", async () => {
    signInWithOfficerId.mockRejectedValue(new Error("Invalid Officer ID or password."));
    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("Officer ID"), { target: { value: "OFF-999" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "nope" } });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent("Invalid Officer ID or password."),
    );
    expect(replace).not.toHaveBeenCalled();
  });

  it("says so when sign-in is not configured", () => {
    (useInvestigator as jest.Mock).mockReturnValue({
      signInWithOfficerId,
      authConfigured: false,
    });

    render(<LoginPage />);

    expect(screen.getByRole("alert")).toHaveTextContent(/not configured/i);
    expect(screen.queryByLabelText("Officer ID")).not.toBeInTheDocument();
  });
});
