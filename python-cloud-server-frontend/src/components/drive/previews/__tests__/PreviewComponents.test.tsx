import { render, screen } from "@testing-library/react";

import FolderPreview from "@/components/drive/previews/FolderPreview";
import ImagePreview from "@/components/drive/previews/ImagePreview";
import MusicPreview from "@/components/drive/previews/MusicPreview";
import TextPreview from "@/components/drive/previews/TextPreview";
import VideoPreview from "@/components/drive/previews/VideoPreview";

// Mock Next.js Image component
jest.mock("next/image", () => ({
  __esModule: true,
  default: (props: any) => {
    // eslint-disable-next-line @next/next/no-img-element, jsx-a11y/alt-text
    return <img {...props} />;
  },
}));

describe("Preview Components", () => {
  describe("ImagePreview", () => {
    it("should render image icon", () => {
      render(<ImagePreview />);
      const img = screen.getByAltText("Image file");
      expect(img).toBeInTheDocument();
      expect(img).toHaveAttribute("src", "/icons/image-icon.svg");
    });

    it("should have correct styling", () => {
      const { container } = render(<ImagePreview />);
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
    it("should render video icon", () => {
      render(<VideoPreview />);
      const img = screen.getByAltText("Video file");
      expect(img).toBeInTheDocument();
      expect(img).toHaveAttribute("src", "/icons/video-icon.svg");
    });

    it("should have neon-blue text color", () => {
      const { container } = render(<VideoPreview />);
      const iconContainer = container.querySelector(".text-neon-blue");
      expect(iconContainer).toBeInTheDocument();
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
