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

// Mock window.scrollTo
global.scrollTo = jest.fn();

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

  // Helper function to generate large file sets for pagination testing
  const generateMockFiles = (count: number): FileMetadata[] => {
    return Array.from({ length: count }, (_, i) => ({
      filepath: `file${i}.jpg`,
      mimeType: "image/jpeg",
      size: 1024,
      tags: [],
      uploadedAt: "2023-01-01T00:00:00Z",
      updatedAt: "2023-01-01T00:00:00Z",
    }));
  };

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

    expect(screen.getByText("No files or folders found")).toBeInTheDocument();
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
    expect(screen.queryByTestId("preview-image.jpg")).not.toBeInTheDocument();
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

  describe("Pagination", () => {
    it("should display pagination controls when more than 24 items", () => {
      const manyFiles = generateMockFiles(30);
      render(<PreviewGrid files={manyFiles} />);

      expect(screen.getByText("Previous")).toBeInTheDocument();
      expect(screen.getByText("Next")).toBeInTheDocument();
      expect(screen.getByText("1")).toBeInTheDocument();
      expect(screen.getByText("2")).toBeInTheDocument();
    });

    it("should not display pagination when 24 or fewer items", () => {
      const fewFiles = generateMockFiles(20);
      render(<PreviewGrid files={fewFiles} />);

      expect(screen.queryByText("Previous")).not.toBeInTheDocument();
      expect(screen.queryByText("Next")).not.toBeInTheDocument();
    });

    it("should display correct items count", () => {
      const manyFiles = generateMockFiles(30);
      render(<PreviewGrid files={manyFiles} />);

      expect(screen.getByText("Showing 1-24 of 30 items")).toBeInTheDocument();
    });

    it("should navigate to next page", () => {
      const manyFiles = generateMockFiles(30);
      render(<PreviewGrid files={manyFiles} />);

      // Click next button
      const nextButton = screen.getByText("Next");
      fireEvent.click(nextButton);

      // Should show items 25-30
      expect(screen.getByText("Showing 25-30 of 30 items")).toBeInTheDocument();
      expect(screen.getByTestId("preview-file24.jpg")).toBeInTheDocument();
    });

    it("should navigate to previous page", () => {
      const manyFiles = generateMockFiles(30);
      render(<PreviewGrid files={manyFiles} />);

      // Go to page 2
      const nextButton = screen.getByText("Next");
      fireEvent.click(nextButton);

      // Go back to page 1
      const prevButton = screen.getByText("Previous");
      fireEvent.click(prevButton);

      expect(screen.getByText("Showing 1-24 of 30 items")).toBeInTheDocument();
      expect(screen.getByTestId("preview-file0.jpg")).toBeInTheDocument();
    });

    it("should disable Previous button on first page", () => {
      const manyFiles = generateMockFiles(30);
      render(<PreviewGrid files={manyFiles} />);

      const prevButton = screen.getByText("Previous");
      expect(prevButton).toBeDisabled();
    });

    it("should disable Next button on last page", () => {
      const manyFiles = generateMockFiles(30);
      render(<PreviewGrid files={manyFiles} />);

      // Go to last page
      const nextButton = screen.getByText("Next");
      fireEvent.click(nextButton);

      expect(nextButton).toBeDisabled();
    });

    it("should highlight current page number", () => {
      const manyFiles = generateMockFiles(30);
      render(<PreviewGrid files={manyFiles} />);

      const page1Button = screen.getByText("1");
      expect(page1Button).toHaveClass("bg-neon-green");

      // Navigate to page 2
      const nextButton = screen.getByText("Next");
      fireEvent.click(nextButton);

      const page2Button = screen.getByText("2");
      expect(page2Button).toHaveClass("bg-neon-green");
    });

    it("should reset to page 1 when navigating into folder", async () => {
      // Create a file that would be on page 2, then a folder with content
      const filesWithFolders = [
        ...generateMockFiles(25), // This creates 25 files, so we need page 2
        {
          filepath: "testfolder/file.jpg",
          mimeType: "image/jpeg",
          size: 1024,
          tags: [],
          uploadedAt: "2023-01-01T00:00:00Z",
          updatedAt: "2023-01-01T00:00:00Z",
        },
      ];

      render(<PreviewGrid files={filesWithFolders} />);

      // Folder 'testfolder' will be on first page (folders are rendered before files)
      const folderButton = screen.getByTestId("preview-testfolder");

      // Navigate into folder (this should work immediately)
      fireEvent.click(folderButton);

      // Should show only the file inside the folder
      await waitFor(() => {
        expect(screen.getByText("Showing 1-1 of 1 items")).toBeInTheDocument();
        expect(
          screen.getByText("Current folder: testfolder")
        ).toBeInTheDocument();
      });
    });

    it("should reset to page 1 when navigating back from folder", () => {
      const manyFiles = generateMockFiles(30);
      const filesWithFolders = [
        ...manyFiles,
        {
          filepath: "folder/file.jpg",
          mimeType: "image/jpeg",
          size: 1024,
          tags: [],
          uploadedAt: "2023-01-01T00:00:00Z",
          updatedAt: "2023-01-01T00:00:00Z",
        },
      ];

      render(<PreviewGrid files={filesWithFolders} />);

      // Navigate into folder
      const folderButton = screen.getByTestId("preview-folder");
      fireEvent.click(folderButton);

      // Navigate back
      const backButton = screen.getByText("← Back");
      fireEvent.click(backButton);

      // Should be on page 1
      expect(screen.getByText("Showing 1-24 of 31 items")).toBeInTheDocument();
    });

    it("should display 24 items per page (4x6 grid)", () => {
      const manyFiles = generateMockFiles(50);
      render(<PreviewGrid files={manyFiles} />);

      // Count rendered preview items
      const previewItems = screen.getAllByTestId(/preview-file/);
      expect(previewItems).toHaveLength(24);
    });
  });
});
