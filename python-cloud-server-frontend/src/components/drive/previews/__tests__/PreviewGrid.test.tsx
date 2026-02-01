import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import PreviewGrid from "@/components/drive/previews/PreviewGrid";
import type { FileMetadata } from "@/lib/types";

// Mock child components
jest.mock("@/components/drive/previews/PreviewItem", () => ({
  __esModule: true,
  default: ({
    filename,
    onClick,
    children,
  }: {
    filename: string;
    onClick: () => void;
    children: React.ReactNode;
  }) => (
    <button onClick={onClick} data-testid={`preview-${filename}`}>
      {filename}
      {children}
    </button>
  ),
}));

jest.mock("@/components/drive/previews/ImagePreview", () => ({
  __esModule: true,
  default: () => <div>ImagePreview</div>,
}));

jest.mock("@/components/drive/previews/TextPreview", () => ({
  __esModule: true,
  default: () => <div>TextPreview</div>,
}));

jest.mock("@/components/drive/previews/VideoPreview", () => ({
  __esModule: true,
  default: () => <div>VideoPreview</div>,
}));

jest.mock("@/components/drive/previews/MusicPreview", () => ({
  __esModule: true,
  default: () => <div>MusicPreview</div>,
}));

jest.mock("@/components/drive/previews/FolderPreview", () => ({
  __esModule: true,
  default: () => <div>FolderPreview</div>,
}));

jest.mock("@/components/drive/displays/FileDisplayWrapper", () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="file-display-wrapper">{children}</div>
  ),
}));

jest.mock("@/components/drive/displays/ImageDisplay", () => ({
  __esModule: true,
  default: ({ filepath }: { filepath: string }) => (
    <div data-testid="image-display">{filepath}</div>
  ),
}));

jest.mock("@/components/drive/displays/TextDisplay", () => ({
  __esModule: true,
  default: ({ filepath }: { filepath: string }) => (
    <div data-testid="text-display">{filepath}</div>
  ),
}));

jest.mock("@/components/drive/displays/VideoDisplay", () => ({
  __esModule: true,
  default: ({ filepath }: { filepath: string }) => (
    <div data-testid="video-display">{filepath}</div>
  ),
}));

jest.mock("@/components/drive/displays/MusicDisplay", () => ({
  __esModule: true,
  default: ({ filepath }: { filepath: string }) => (
    <div data-testid="music-display">{filepath}</div>
  ),
}));

describe("PreviewGrid", () => {
  const mockFiles: FileMetadata[] = [
    {
      filepath: "image.jpg",
      mimeType: "image/jpeg",
      size: 1024,
      tags: [],
      uploadedAt: "2023-01-01T00:00:00Z",
      updatedAt: "2023-01-01T00:00:00Z",
    },
    {
      filepath: "document.txt",
      mimeType: "text/plain",
      size: 512,
      tags: [],
      uploadedAt: "2023-01-01T00:00:00Z",
      updatedAt: "2023-01-01T00:00:00Z",
    },
    {
      filepath: "folder/nested.jpg",
      mimeType: "image/jpeg",
      size: 2048,
      tags: [],
      uploadedAt: "2023-01-01T00:00:00Z",
      updatedAt: "2023-01-01T00:00:00Z",
    },
  ];

  it("should render files at root level", () => {
    render(<PreviewGrid files={mockFiles} />);

    expect(screen.getByTestId("preview-image.jpg")).toBeInTheDocument();
    expect(screen.getByTestId("preview-document.txt")).toBeInTheDocument();
  });

  it("should render folders", () => {
    render(<PreviewGrid files={mockFiles} />);

    expect(screen.getByTestId("preview-folder")).toBeInTheDocument();
  });

  it("should display empty state when no files", () => {
    render(<PreviewGrid files={[]} />);

    expect(
      screen.getByText("No files or folders found")
    ).toBeInTheDocument();
  });

  it("should navigate into folder when clicked", () => {
    render(<PreviewGrid files={mockFiles} />);

    const folderButton = screen.getByTestId("preview-folder");
    fireEvent.click(folderButton);

    // Should show back button
    expect(screen.getByText("← Back")).toBeInTheDocument();
    expect(screen.getByText("Current folder: folder")).toBeInTheDocument();
  });

  it("should navigate back from folder", () => {
    render(<PreviewGrid files={mockFiles} />);

    // Navigate into folder
    const folderButton = screen.getByTestId("preview-folder");
    fireEvent.click(folderButton);

    // Navigate back
    const backButton = screen.getByText("← Back");
    fireEvent.click(backButton);

    // Should be at root again
    expect(screen.queryByText("Current folder:")).not.toBeInTheDocument();
  });

  it("should open image display when image clicked", async () => {
    render(<PreviewGrid files={mockFiles} />);

    const imageButton = screen.getByTestId("preview-image.jpg");
    fireEvent.click(imageButton);

    await waitFor(() => {
      expect(screen.getByTestId("image-display")).toBeInTheDocument();
      expect(screen.getByTestId("image-display")).toHaveTextContent(
        "image.jpg"
      );
    });
  });

  it("should call onFileClick callback", () => {
    const mockOnFileClick = jest.fn();
    render(<PreviewGrid files={mockFiles} onFileClick={mockOnFileClick} />);

    const imageButton = screen.getByTestId("preview-image.jpg");
    fireEvent.click(imageButton);

    expect(mockOnFileClick).toHaveBeenCalledWith(
      expect.objectContaining({
        filepath: "image.jpg",
      })
    );
  });

  it("should filter files correctly when in folder", () => {
    render(<PreviewGrid files={mockFiles} />);

    // Navigate into folder
    const folderButton = screen.getByTestId("preview-folder");
    fireEvent.click(folderButton);

    // Should show nested file
    expect(screen.getByTestId("preview-nested.jpg")).toBeInTheDocument();

    // Should not show root files
    expect(
      screen.queryByTestId("preview-image.jpg")
    ).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("preview-document.txt")
    ).not.toBeInTheDocument();
  });

  it("should correctly identify file types", () => {
    const filesWithTypes: FileMetadata[] = [
      {
        filepath: "image.png",
        mimeType: "image/png",
        size: 1024,
        tags: [],
        uploadedAt: "2023-01-01T00:00:00Z",
        updatedAt: "2023-01-01T00:00:00Z",
      },
      {
        filepath: "video.mp4",
        mimeType: "video/mp4",
        size: 1024,
        tags: [],
        uploadedAt: "2023-01-01T00:00:00Z",
        updatedAt: "2023-01-01T00:00:00Z",
      },
      {
        filepath: "audio.mp3",
        mimeType: "audio/mpeg",
        size: 1024,
        tags: [],
        uploadedAt: "2023-01-01T00:00:00Z",
        updatedAt: "2023-01-01T00:00:00Z",
      },
    ];

    render(<PreviewGrid files={filesWithTypes} />);

    expect(screen.getByTestId("preview-image.png")).toBeInTheDocument();
    expect(screen.getByTestId("preview-video.mp4")).toBeInTheDocument();
    expect(screen.getByTestId("preview-audio.mp3")).toBeInTheDocument();
  });
});
