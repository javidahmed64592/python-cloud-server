import { fireEvent, render, screen } from "@testing-library/react";

import PreviewItem from "@/components/drive/previews/PreviewItem";

describe("PreviewItem", () => {
  const mockOnClick = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should render filename and children", () => {
    render(
      <PreviewItem filename="test.txt" onClick={mockOnClick}>
        <div data-testid="child-content">Preview Content</div>
      </PreviewItem>
    );

    expect(screen.getByText("test.txt")).toBeInTheDocument();
    expect(screen.getByTestId("child-content")).toBeInTheDocument();
  });

  it("should call onClick when clicked", () => {
    render(
      <PreviewItem filename="test.txt" onClick={mockOnClick}>
        <div>Content</div>
      </PreviewItem>
    );

    const button = screen.getByRole("button");
    fireEvent.click(button);

    expect(mockOnClick).toHaveBeenCalledTimes(1);
  });

  it("should truncate long filenames", () => {
    const longFilename = "very_long_filename_that_should_be_truncated.txt";
    const { container } = render(
      <PreviewItem filename={longFilename} onClick={mockOnClick}>
        <div>Content</div>
      </PreviewItem>
    );

    const filenameElement = container.querySelector(".truncate");
    expect(filenameElement).toBeInTheDocument();
    expect(filenameElement).toHaveTextContent(longFilename);
  });

  it("should have correct styling classes", () => {
    const { container } = render(
      <PreviewItem filename="test.txt" onClick={mockOnClick}>
        <div>Content</div>
      </PreviewItem>
    );

    const button = screen.getByRole("button");
    expect(button).toHaveClass("group");
    expect(button).toHaveClass("hover:bg-background-tertiary");

    const iconContainer = container.querySelector(".h-24.w-24");
    expect(iconContainer).toBeInTheDocument();
  });

  it("should be keyboard accessible", () => {
    render(
      <PreviewItem filename="test.txt" onClick={mockOnClick}>
        <div>Content</div>
      </PreviewItem>
    );

    const button = screen.getByRole("button");
    button.focus();
    expect(button).toHaveFocus();
  });
});
