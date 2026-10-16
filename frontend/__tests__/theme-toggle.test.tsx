import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ThemeToggle } from "@/components/ThemeToggle";
import * as nextThemes from "next-themes";

vi.mock("next-themes", () => ({
  useTheme: vi.fn(),
}));

describe("ThemeToggle Component", () => {
  const setThemeMock = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders Moon icon and offers switch to dark mode when in light theme", () => {
    vi.mocked(nextThemes.useTheme).mockReturnValue({
      theme: "light",
      resolvedTheme: "light",
      setTheme: setThemeMock,
      themes: ["light", "dark"],
      systemTheme: "light",
    });

    render(<ThemeToggle />);
    const button = screen.getByRole("button", { name: /switch to dark mode/i });
    expect(button).toBeDefined();

    fireEvent.click(button);
    expect(setThemeMock).toHaveBeenCalledWith("dark");
  });

  it("renders Sun icon and offers switch to light mode when in dark theme", () => {
    vi.mocked(nextThemes.useTheme).mockReturnValue({
      theme: "dark",
      resolvedTheme: "dark",
      setTheme: setThemeMock,
      themes: ["light", "dark"],
      systemTheme: "dark",
    });

    render(<ThemeToggle />);
    const button = screen.getByRole("button", { name: /switch to light mode/i });
    expect(button).toBeDefined();

    fireEvent.click(button);
    expect(setThemeMock).toHaveBeenCalledWith("light");
  });
});
