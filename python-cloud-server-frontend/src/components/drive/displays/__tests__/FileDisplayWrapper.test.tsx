import { fireEvent, render, screen } from "@testing-library/react";

import FileDisplayWrapper from "@/components/drive/displays/FileDisplayWrapper";

describe("FileDisplayWrapper", () => {
  const mockOnClose = jest.fn();
  const mockOnPrev = jest.fn();
  const mockOnNext = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should render children", () => {
    render(
      <FileDisplayWrapper onClose={mockOnClose}>
        <div data-testid="child">Test Content</div>
      </FileDisplayWrapper>
    );

    expect(screen.getByTestId("child")).toBeInTheDocument();
  });

  it("should show prev button when hasPrev is true", () => {
    render(
      <FileDisplayWrapper
        onClose={mockOnClose}
        onPrev={mockOnPrev}
        hasPrev={true}
      >
        <div>Content</div>
      </FileDisplayWrapper>
    );

    const prevButton = screen.getByLabelText("Previous file");
    expect(prevButton).toBeInTheDocument();
  });

  it("should show next button when hasNext is true", () => {
    render(
      <FileDisplayWrapper
        onClose={mockOnClose}
        onNext={mockOnNext}
        hasNext={true}
      >
        <div>Content</div>
      </FileDisplayWrapper>
    );

    const nextButton = screen.getByLabelText("Next file");
    expect(nextButton).toBeInTheDocument();
  });

  it("should not show prev button when hasPrev is false", () => {
    render(
      <FileDisplayWrapper onClose={mockOnClose} hasPrev={false}>
        <div>Content</div>
      </FileDisplayWrapper>
    );

    expect(screen.queryByLabelText("Previous file")).not.toBeInTheDocument();
  });

  it("should not show next button when hasNext is false", () => {
    render(
      <FileDisplayWrapper onClose={mockOnClose} hasNext={false}>
        <div>Content</div>
      </FileDisplayWrapper>
    );

    expect(screen.queryByLabelText("Next file")).not.toBeInTheDocument();
  });

  it("should call onPrev when prev button clicked", () => {
    render(
      <FileDisplayWrapper
        onClose={mockOnClose}
        onPrev={mockOnPrev}
        hasPrev={true}
      >
        <div>Content</div>
      </FileDisplayWrapper>
    );

    const prevButton = screen.getByLabelText("Previous file");
    fireEvent.click(prevButton);

    expect(mockOnPrev).toHaveBeenCalledTimes(1);
  });

  it("should call onNext when next button clicked", () => {
    render(
      <FileDisplayWrapper
        onClose={mockOnClose}
        onNext={mockOnNext}
        hasNext={true}
      >
        <div>Content</div>
      </FileDisplayWrapper>
    );

    const nextButton = screen.getByLabelText("Next file");
    fireEvent.click(nextButton);

    expect(mockOnNext).toHaveBeenCalledTimes(1);
  });

  it("should handle keyboard navigation - ArrowLeft", () => {
    render(
      <FileDisplayWrapper
        onClose={mockOnClose}
        onPrev={mockOnPrev}
        hasPrev={true}
      >
        <div>Content</div>
      </FileDisplayWrapper>
    );

    fireEvent.keyDown(window, { key: "ArrowLeft" });

    expect(mockOnPrev).toHaveBeenCalledTimes(1);
  });

  it("should handle keyboard navigation - ArrowRight", () => {
    render(
      <FileDisplayWrapper
        onClose={mockOnClose}
        onNext={mockOnNext}
        hasNext={true}
      >
        <div>Content</div>
      </FileDisplayWrapper>
    );

    fireEvent.keyDown(window, { key: "ArrowRight" });

    expect(mockOnNext).toHaveBeenCalledTimes(1);
  });

  it("should handle keyboard navigation - Escape", () => {
    render(
      <FileDisplayWrapper onClose={mockOnClose}>
        <div>Content</div>
      </FileDisplayWrapper>
    );

    fireEvent.keyDown(window, { key: "Escape" });

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("should not call onPrev on ArrowLeft if hasPrev is false", () => {
    render(
      <FileDisplayWrapper
        onClose={mockOnClose}
        onPrev={mockOnPrev}
        hasPrev={false}
      >
        <div>Content</div>
      </FileDisplayWrapper>
    );

    fireEvent.keyDown(window, { key: "ArrowLeft" });

    expect(mockOnPrev).not.toHaveBeenCalled();
  });

  it("should not call onNext on ArrowRight if hasNext is false", () => {
    render(
      <FileDisplayWrapper
        onClose={mockOnClose}
        onNext={mockOnNext}
        hasNext={false}
      >
        <div>Content</div>
      </FileDisplayWrapper>
    );

    fireEvent.keyDown(window, { key: "ArrowRight" });

    expect(mockOnNext).not.toHaveBeenCalled();
  });

  it("should have correct button styling", () => {
    render(
      <FileDisplayWrapper
        onClose={mockOnClose}
        onPrev={mockOnPrev}
        onNext={mockOnNext}
        hasPrev={true}
        hasNext={true}
      >
        <div>Content</div>
      </FileDisplayWrapper>
    );

    const prevButton = screen.getByLabelText("Previous file");
    const nextButton = screen.getByLabelText("Next file");

    expect(prevButton).toHaveClass("rounded-full");
    expect(prevButton).toHaveClass("bg-background-secondary");
    expect(nextButton).toHaveClass("border-terminal-border");
  });
});
