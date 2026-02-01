import { render, screen, waitFor } from "@testing-library/react";

import ImageDisplay from "@/components/drive/displays/ImageDisplay";
import MusicDisplay from "@/components/drive/displays/MusicDisplay";
import TextDisplay from "@/components/drive/displays/TextDisplay";
import VideoDisplay from "@/components/drive/displays/VideoDisplay";
import * as api from "@/lib/api";

jest.mock("@/lib/api");

const mockedApi = api as jest.Mocked<typeof api>;

// Mock URL.createObjectURL and URL.revokeObjectURL
global.URL.createObjectURL = jest.fn(() => "blob:mock-url");
global.URL.revokeObjectURL = jest.fn();

// Mock Blob.prototype.text
Object.defineProperty(Blob.prototype, "text", {
  value: jest.fn().mockImplementation(function (this: Blob) {
    return Promise.resolve("Hello, World!");
  }),
  writable: true,
});

describe("Display Components", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("ImageDisplay", () => {
    it("should show loading state initially", () => {
      const mockBlob = new Blob(["image data"], { type: "image/jpeg" });
      mockedApi.downloadFile.mockResolvedValue(mockBlob);

      render(<ImageDisplay filepath="test.jpg" onClose={jest.fn()} />);

      expect(screen.getByText("Loading...")).toBeInTheDocument();
    });

    it("should display image after loading", async () => {
      const mockBlob = new Blob(["image data"], { type: "image/jpeg" });
      mockedApi.downloadFile.mockResolvedValue(mockBlob);

      render(<ImageDisplay filepath="test.jpg" onClose={jest.fn()} />);

      await waitFor(() => {
        const img = screen.getByAltText("test.jpg");
        expect(img).toBeInTheDocument();
        expect(img).toHaveAttribute("src", "blob:mock-url");
      });
    });

    it("should display error message on failure", async () => {
      mockedApi.downloadFile.mockRejectedValue(new Error("Download failed"));

      render(<ImageDisplay filepath="test.jpg" onClose={jest.fn()} />);

      await waitFor(() => {
        expect(screen.getByText("Download failed")).toBeInTheDocument();
      });
    });

    it("should revoke object URL on unmount", async () => {
      const mockBlob = new Blob(["image data"], { type: "image/jpeg" });
      mockedApi.downloadFile.mockResolvedValue(mockBlob);

      const { unmount } = render(
        <ImageDisplay filepath="test.jpg" onClose={jest.fn()} />
      );

      await waitFor(() => {
        expect(screen.getByAltText("test.jpg")).toBeInTheDocument();
      });

      unmount();

      expect(global.URL.revokeObjectURL).toHaveBeenCalledWith("blob:mock-url");
    });
  });

  describe("TextDisplay", () => {
    it("should show loading state initially", () => {
      const mockBlob = new Blob(["text content"], { type: "text/plain" });
      mockedApi.downloadFile.mockResolvedValue(mockBlob);

      render(<TextDisplay filepath="test.txt" onClose={jest.fn()} />);

      expect(screen.getByText("Loading...")).toBeInTheDocument();
    });

    it("should display text content", async () => {
      const mockBlob = new Blob(["Hello, World!"], { type: "text/plain" });
      mockedApi.downloadFile.mockResolvedValue(mockBlob);

      render(<TextDisplay filepath="test.txt" onClose={jest.fn()} />);

      await waitFor(() => {
        expect(screen.getByText("Hello, World!")).toBeInTheDocument();
      });
    });

    it("should display error message on failure", async () => {
      mockedApi.downloadFile.mockRejectedValue(new Error("Download failed"));

      render(<TextDisplay filepath="test.txt" onClose={jest.fn()} />);

      await waitFor(() => {
        expect(screen.getByText("Download failed")).toBeInTheDocument();
      });
    });
  });

  describe("VideoDisplay", () => {
    it("should show loading state initially", () => {
      const mockBlob = new Blob(["video data"], { type: "video/mp4" });
      mockedApi.downloadFile.mockResolvedValue(mockBlob);

      render(<VideoDisplay filepath="test.mp4" onClose={jest.fn()} />);

      expect(screen.getByText("Loading video...")).toBeInTheDocument();
    });

    it("should display video after loading", async () => {
      const mockBlob = new Blob(["video data"], { type: "video/mp4" });
      mockedApi.downloadFile.mockResolvedValue(mockBlob);

      render(<VideoDisplay filepath="test.mp4" onClose={jest.fn()} />);

      await waitFor(() => {
        const video = screen.getByTestId("video-element");
        expect(video).toBeInTheDocument();
        expect(video).toHaveAttribute("src", "blob:mock-url");
      });
    });

    it("should display error message on failure", async () => {
      mockedApi.downloadFile.mockRejectedValue(new Error("Download failed"));

      render(<VideoDisplay filepath="test.mp4" onClose={jest.fn()} />);

      await waitFor(() => {
        expect(screen.getByText("Failed to load video")).toBeInTheDocument();
      });
    });

    it("should revoke object URL on unmount", async () => {
      const mockBlob = new Blob(["video data"], { type: "video/mp4" });
      mockedApi.downloadFile.mockResolvedValue(mockBlob);

      const { unmount } = render(
        <VideoDisplay filepath="test.mp4" onClose={jest.fn()} />
      );

      await waitFor(() => {
        expect(screen.getByTestId("video-element")).toBeInTheDocument();
      });

      unmount();

      expect(global.URL.revokeObjectURL).toHaveBeenCalledWith("blob:mock-url");
    });
  });

  describe("MusicDisplay", () => {
    it("should show loading state initially", () => {
      const mockBlob = new Blob(["audio data"], { type: "audio/mpeg" });
      mockedApi.downloadFile.mockResolvedValue(mockBlob);

      render(<MusicDisplay filepath="test.mp3" onClose={jest.fn()} />);

      expect(screen.getByText("Loading audio...")).toBeInTheDocument();
    });

    it("should display audio player after loading", async () => {
      const mockBlob = new Blob(["audio data"], { type: "audio/mpeg" });
      mockedApi.downloadFile.mockResolvedValue(mockBlob);

      render(<MusicDisplay filepath="test.mp3" onClose={jest.fn()} />);

      await waitFor(() => {
        const audio = screen.getByTestId("audio-element");
        expect(audio).toBeInTheDocument();
        expect(audio).toHaveAttribute("src", "blob:mock-url");
      });
    });

    it("should display error message on failure", async () => {
      mockedApi.downloadFile.mockRejectedValue(new Error("Download failed"));

      render(<MusicDisplay filepath="test.mp3" onClose={jest.fn()} />);

      await waitFor(() => {
        expect(screen.getByText("Failed to load audio")).toBeInTheDocument();
      });
    });

    it("should revoke object URL on unmount", async () => {
      const mockBlob = new Blob(["audio data"], { type: "audio/mpeg" });
      mockedApi.downloadFile.mockResolvedValue(mockBlob);

      const { unmount } = render(
        <MusicDisplay filepath="test.mp3" onClose={jest.fn()} />
      );

      await waitFor(() => {
        expect(screen.getByTestId("audio-element")).toBeInTheDocument();
      });

      unmount();

      expect(global.URL.revokeObjectURL).toHaveBeenCalledWith("blob:mock-url");
    });
  });
});
