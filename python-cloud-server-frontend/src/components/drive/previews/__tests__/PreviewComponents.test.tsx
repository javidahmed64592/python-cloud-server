import { render, screen, waitFor } from "@testing-library/react";

import FolderPreview from "@/components/drive/previews/FolderPreview";
import ImagePreview from "@/components/drive/previews/ImagePreview";
import MusicPreview from "@/components/drive/previews/MusicPreview";
import TextPreview from "@/components/drive/previews/TextPreview";
import VideoPreview from "@/components/drive/previews/VideoPreview";
import * as api from "@/lib/api";

// Mock Next.js Image component
jest.mock("next/image", () => ({
  __esModule: true,
  default: (props: any) => {
    // eslint-disable-next-line @next/next/no-img-element, jsx-a11y/alt-text
    return <img {...props} />;
  },
}));

// Mock getThumbnail API
jest.mock("@/lib/api", () => ({
  getThumbnail: jest.fn(),
}));

const mockGetThumbnail = api.getThumbnail as jest.MockedFunction<
  typeof api.getThumbnail
>;

describe("Preview Components", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.URL.createObjectURL = jest.fn(() => "blob:mock-url");
    global.URL.revokeObjectURL = jest.fn();
  });

  describe("ImagePreview", () => {
    it("should show loading spinner initially", () => {
      mockGetThumbnail.mockImplementation(
        () => new Promise(() => {})
      );
      render(<ImagePreview filepath="test/image.png" />);
      const spinner = document.querySelector(".animate-spin");
      expect(spinner).toBeInTheDocument();
    });

    it("should render image icon on error", async () => {
      mockGetThumbnail.mockRejectedValue(new Error("Failed to load"));
      render(<ImagePreview filepath="test/image.png" />);
      await waitFor(() => {
        const img = screen.getByAltText("Image file");
        expect(img).toBeInTheDocument();
        expect(img).toHaveAttribute("src", "/icons/image-icon.svg");
      });
    });

    it("should render thumbnail when loaded successfully", async () => {
      mockGetThumbnail.mockResolvedValue("blob:mock-url");
      render(<ImagePreview filepath="test/image.png" />);
      await waitFor(() => {
        const img = screen.getByAltText("Image thumbnail");
        expect(img).toBeInTheDocument();
        expect(img).toHaveAttribute("src", "blob:mock-url");
      });
    });

    it("should have correct styling", () => {
      mockGetThumbnail.mockImplementation(
        () => new Promise(() => {})
      );
      const { container } = render(<ImagePreview filepath="test/image.png" />);
      const wrapper = container.firstChild as HTMLElement;
      expect(wrapper).toHaveClass("bg-background-secondary");
    });
  });

  describe("TextPreview", () => {
    it("should render text icon", () => {
      render(<TextPreview />);
      const img = screen.getByAltText("Text file");
      expect(img).toBeInTheDocument();
      expect(img).toHaveAttribute("src", "/icons/text-icon.svg");
    });
  });

  describe("VideoPreview", () => {
    it("should show loading spinner initially", () => {
      mockGetThumbnail.mockImplementation(
        () => new Promise(() => {})
      );
      render(<VideoPreview filepath="test/video.mp4" />);
      const spinner = document.querySelector(".animate-spin");
      expect(spinner).toBeInTheDocument();
    });

    it("should render video icon on error", async () => {
      mockGetThumbnail.mockRejectedValue(new Error("Failed to load"));
      render(<VideoPreview filepath="test/video.mp4" />);
      await waitFor(() => {
        const img = screen.getByAltText("Video file");
        expect(img).toBeInTheDocument();
        expect(img).toHaveAttribute("src", "/icons/video-icon.svg");
      });
    });

    it("should render thumbnail with play overlay when loaded successfully", async () => {
      mockGetThumbnail.mockResolvedValue("blob:mock-url");
      render(<VideoPreview filepath="test/video.mp4" />);
      await waitFor(() => {
        const thumbnail = screen.getByAltText("Video thumbnail");
        expect(thumbnail).toBeInTheDocument();
        expect(thumbnail).toHaveAttribute("src", "blob:mock-url");
        const playIcon = screen.getByAltText("Play");
        expect(playIcon).toBeInTheDocument();
      });
    });

    it("should have neon-blue text color on error state", async () => {
      mockGetThumbnail.mockRejectedValue(new Error("Failed to load"));
      const { container } = render(<VideoPreview filepath="test/video.mp4" />);
      await waitFor(() => {
        const iconContainer = container.querySelector(".text-neon-blue");
        expect(iconContainer).toBeInTheDocument();
      });
    });
  });

  describe("MusicPreview", () => {
    it("should render music icon", () => {
      render(<MusicPreview />);
      const img = screen.getByAltText("Music file");
      expect(img).toBeInTheDocument();
      expect(img).toHaveAttribute("src", "/icons/music-icon.svg");
    });

    it("should have neon-purple text color", () => {
      const { container } = render(<MusicPreview />);
      const iconContainer = container.querySelector(".text-neon-purple");
      expect(iconContainer).toBeInTheDocument();
    });
  });

  describe("FolderPreview", () => {
    it("should render folder icon", () => {
      render(<FolderPreview />);
      const img = screen.getByAltText("Folder");
      expect(img).toBeInTheDocument();
      expect(img).toHaveAttribute("src", "/icons/folder-icon.svg");
    });
  });
});
