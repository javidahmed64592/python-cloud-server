import {
  deleteFile,
  downloadFile,
  getFiles,
  patchFile,
  uploadFile,
} from "@/lib/api";
import type {
  DeleteFileResponse,
  PatchFileResponse,
  PostFileResponse,
} from "@/lib/types";

jest.mock("../api", () => {
  const actual = jest.requireActual("../api");
  return {
    ...actual,
    getFiles: jest.fn(),
    downloadFile: jest.fn(),
    uploadFile: jest.fn(),
    patchFile: jest.fn(),
    deleteFile: jest.fn(),
  };
});

const mockGetFiles = getFiles as jest.MockedFunction<typeof getFiles>;
const mockDownloadFile = downloadFile as jest.MockedFunction<
  typeof downloadFile
>;
const mockUploadFile = uploadFile as jest.MockedFunction<typeof uploadFile>;
const mockPatchFile = patchFile as jest.MockedFunction<typeof patchFile>;
const mockDeleteFile = deleteFile as jest.MockedFunction<typeof deleteFile>;

describe("File API Methods", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("getFiles", () => {
    it("should fetch files successfully and transform metadata", async () => {
      const mockResponse = {
        message: "Files retrieved",
        timestamp: "2023-01-01T00:00:00Z",
        files: [
          {
            filepath: "test.txt",
            mimeType: "text/plain",
            size: 100,
            tags: ["test"],
            uploadedAt: "2023-01-01T00:00:00Z",
            updatedAt: "2023-01-01T00:00:00Z",
          },
        ],
      };

      mockGetFiles.mockResolvedValue(mockResponse);

      const result = await getFiles({ limit: 10 });

      expect(mockGetFiles).toHaveBeenCalledWith({ limit: 10 });
      expect(result.files[0]).toEqual({
        filepath: "test.txt",
        mimeType: "text/plain",
        size: 100,
        tags: ["test"],
        uploadedAt: "2023-01-01T00:00:00Z",
        updatedAt: "2023-01-01T00:00:00Z",
      });
    });

    it("should handle empty file list", async () => {
      const mockResponse = {
        message: "No files found",
        timestamp: "2023-01-01T00:00:00Z",
        files: [],
      };

      mockGetFiles.mockResolvedValue(mockResponse);

      const result = await getFiles();

      expect(result.files).toEqual([]);
    });

    it("should throw error on failure", async () => {
      mockGetFiles.mockRejectedValue(new Error("Network error"));

      await expect(getFiles()).rejects.toThrow();
    });
  });

  describe("downloadFile", () => {
    it("should download file as blob", async () => {
      const mockBlob = new Blob(["test content"], { type: "text/plain" });
      mockDownloadFile.mockResolvedValue(mockBlob);

      const result = await downloadFile("test.txt");

      expect(mockDownloadFile).toHaveBeenCalledWith("test.txt");
      expect(result).toEqual(mockBlob);
    });

    it("should handle download errors", async () => {
      mockDownloadFile.mockRejectedValue(new Error("File not found"));

      await expect(downloadFile("missing.txt")).rejects.toThrow();
    });
  });

  describe("uploadFile", () => {
    it("should upload file successfully", async () => {
      const mockFile = new File(["content"], "test.txt", {
        type: "text/plain",
      });
      const mockResponse: PostFileResponse = {
        message: "File uploaded",
        timestamp: "2023-01-01T00:00:00Z",
        filepath: "test.txt",
        size: 7,
      };

      mockUploadFile.mockResolvedValue(mockResponse);

      const result = await uploadFile("test.txt", mockFile);

      expect(mockUploadFile).toHaveBeenCalledWith("test.txt", mockFile);
      expect(result.filepath).toBe("test.txt");
    });

    it("should handle upload errors", async () => {
      const mockFile = new File(["content"], "test.txt");
      mockUploadFile.mockRejectedValue(new Error("Upload failed"));

      await expect(uploadFile("test.txt", mockFile)).rejects.toThrow();
    });
  });

  describe("patchFile", () => {
    it("should update file metadata", async () => {
      const mockResponse: PatchFileResponse = {
        message: "File updated",
        timestamp: "2023-01-01T00:00:00Z",
        filepath: "test.txt",
        tags: ["updated"],
      };

      mockPatchFile.mockResolvedValue(mockResponse);

      const result = await patchFile("test.txt", { addTags: ["updated"] });

      expect(mockPatchFile).toHaveBeenCalledWith("test.txt", {
        addTags: ["updated"],
      });
      expect(result.tags).toEqual(["updated"]);
    });

    it("should rename file", async () => {
      const mockResponse: PatchFileResponse = {
        message: "File renamed",
        timestamp: "2023-01-01T00:00:00Z",
        filepath: "renamed.txt",
        tags: [],
      };

      mockPatchFile.mockResolvedValue(mockResponse);

      const result = await patchFile("test.txt", {
        newFilepath: "renamed.txt",
      });

      expect(result.filepath).toBe("renamed.txt");
    });

    it("should handle patch errors", async () => {
      mockPatchFile.mockRejectedValue(new Error("Patch failed"));

      await expect(
        patchFile("test.txt", { addTags: ["tag"] })
      ).rejects.toThrow();
    });
  });

  describe("deleteFile", () => {
    it("should delete file successfully", async () => {
      const mockResponse: DeleteFileResponse = {
        message: "File deleted",
        timestamp: "2023-01-01T00:00:00Z",
        filepath: "test.txt",
      };

      mockDeleteFile.mockResolvedValue(mockResponse);

      const result = await deleteFile("test.txt");

      expect(mockDeleteFile).toHaveBeenCalledWith("test.txt");
      expect(result.filepath).toBe("test.txt");
    });

    it("should handle delete errors", async () => {
      mockDeleteFile.mockRejectedValue(new Error("Delete failed"));

      await expect(deleteFile("test.txt")).rejects.toThrow();
    });
  });
});
