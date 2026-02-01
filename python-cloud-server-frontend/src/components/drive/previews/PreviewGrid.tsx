"use client";

import { useState } from "react";

import type { FileMetadata } from "@/lib/types";

import FileDisplayWrapper from "../displays/FileDisplayWrapper";
import ImageDisplay from "../displays/ImageDisplay";
import MusicDisplay from "../displays/MusicDisplay";
import TextDisplay from "../displays/TextDisplay";
import VideoDisplay from "../displays/VideoDisplay";

import FolderPreview from "./FolderPreview";
import ImagePreview from "./ImagePreview";
import MusicPreview from "./MusicPreview";
import PreviewItem from "./PreviewItem";
import TextPreview from "./TextPreview";
import VideoPreview from "./VideoPreview";

interface PreviewGridProps {
  files: FileMetadata[];
  onFileClick?: (file: FileMetadata) => void;
}

interface FolderItem {
  type: "folder";
  name: string;
  path: string;
}

interface FileItem {
  type: "file";
  metadata: FileMetadata;
}

type GridItem = FolderItem | FileItem;
type FileType = "image" | "video" | "music" | "text" | "folder" | "unknown";

const getFileType = (mimeType: string | undefined): FileType => {
  if (!mimeType) return "unknown";
  if (mimeType.startsWith("image/")) return "image";
  if (mimeType.startsWith("video/")) return "video";
  if (mimeType.startsWith("audio/")) return "music";
  if (mimeType.startsWith("text/") || mimeType === "application/json")
    return "text";
  return "unknown";
};

const getPreviewComponent = (fileType: FileType) => {
  switch (fileType) {
    case "image":
      return <ImagePreview />;
    case "video":
      return <VideoPreview />;
    case "music":
      return <MusicPreview />;
    case "text":
      return <TextPreview />;
    case "folder":
      return <FolderPreview />;
    default:
      return <TextPreview />;
  }
};

const extractFolders = (
  files: FileMetadata[],
  currentPath: string
): FolderItem[] => {
  const folderSet = new Set<string>();
  const pathPrefix = currentPath ? currentPath + "/" : "";

  files.forEach(file => {
    // Only consider files that are in subdirectories relative to current path
    if (currentPath && !file.filepath.startsWith(pathPrefix)) {
      return;
    }

    const relativePath = currentPath
      ? file.filepath.slice(pathPrefix.length)
      : file.filepath;
    const parts = relativePath.split("/");

    // If there's more than one part, the first part is a folder at this level
    if (parts.length > 1 && parts[0]) {
      folderSet.add(parts[0]);
    }
  });

  return Array.from(folderSet)
    .sort((a, b) => a.localeCompare(b, undefined, { sensitivity: "base" }))
    .map(folderName => ({
      type: "folder" as const,
      name: folderName,
      path: currentPath ? `${currentPath}/${folderName}` : folderName,
    }));
};

const ITEMS_PER_PAGE = 24; // 4x6 grid

export default function PreviewGrid({ files, onFileClick }: PreviewGridProps) {
  const [selectedFile, setSelectedFile] = useState<FileMetadata | null>(null);
  const [displayType, setDisplayType] = useState<FileType | null>(null);
  const [currentPath, setCurrentPath] = useState<string>("");
  const [currentPage, setCurrentPage] = useState<number>(1);

  const handleFileClick = (file: FileMetadata) => {
    const fileType = getFileType(file.mimeType);
    setSelectedFile(file);
    setDisplayType(fileType);
    onFileClick?.(file);
  };

  const handleNavigate = (direction: "prev" | "next") => {
    if (!selectedFile) return;

    const currentIndex = filteredFiles.findIndex(
      f => f.filepath === selectedFile.filepath
    );

    if (currentIndex === -1) return;

    const newIndex = direction === "prev" ? currentIndex - 1 : currentIndex + 1;

    if (newIndex >= 0 && newIndex < filteredFiles.length) {
      const newFile = filteredFiles[newIndex];
      if (newFile) {
        const fileType = getFileType(newFile.mimeType);
        setSelectedFile(newFile);
        setDisplayType(fileType);
        onFileClick?.(newFile);
      }
    }
  };

  const handleFolderClick = (folderPath: string) => {
    setCurrentPath(folderPath);
    setCurrentPage(1); // Reset to first page when navigating folders
  };

  const handleBackClick = () => {
    const parts = currentPath.split("/").filter(Boolean);
    parts.pop();
    setCurrentPath(parts.join("/"));
    setCurrentPage(1); // Reset to first page when navigating back
  };

  const handleCloseDisplay = () => {
    setSelectedFile(null);
    setDisplayType(null);
  };

  // Filter files based on current path
  const filteredFiles = files.filter(file => {
    if (!currentPath) {
      // At root level, only show files in root (no "/" in filepath)
      return !file.filepath.includes("/");
    }
    // In a folder, show files that start with current path
    return (
      file.filepath.startsWith(currentPath + "/") &&
      file.filepath.slice(currentPath.length + 1).split("/").length === 1
    );
  });

  // Extract folders at current level
  const folders = extractFolders(files, currentPath);

  // Create grid items: folders first, then files
  const gridItems: GridItem[] = [
    ...folders.map(f => ({ ...f, type: "folder" as const })),
    ...filteredFiles.map(f => ({ type: "file" as const, metadata: f })),
  ];

  // Calculate pagination
  const totalItems = gridItems.length;
  const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const paginatedItems = gridItems.slice(startIndex, endIndex);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <>
      <div className="flex flex-col h-full overflow-hidden">
        {/* Breadcrumb navigation */}
        <div className="flex-shrink-0">
          {currentPath && (
            <div className="px-4 sm:px-6 pt-4 pb-2">
              <button
                onClick={handleBackClick}
                className="text-neon-green hover:opacity-80 transition-opacity"
              >
                ← Back
              </button>
              <div className="mt-2 text-sm text-text-muted">
                Current folder: {currentPath}
              </div>
            </div>
          )}
        </div>

        {/* Grid area */}
        <div className="flex-1 overflow-hidden px-4 sm:px-6">
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3 sm:gap-4 h-full content-start">
            {paginatedItems.map(item => {
              if (item.type === "folder") {
                return (
                  <PreviewItem
                    key={`folder-${item.path}`}
                    filename={item.name}
                    onClick={() =>
                      handleFolderClick(
                        currentPath ? `${currentPath}/${item.name}` : item.name
                      )
                    }
                  >
                    {getPreviewComponent("folder")}
                  </PreviewItem>
                );
              } else {
                const fileType = getFileType(item.metadata.mimeType);
                const filename =
                  item.metadata.filepath.split("/").pop() ||
                  item.metadata.filepath;

                return (
                  <PreviewItem
                    key={item.metadata.filepath}
                    filename={filename}
                    onClick={() => handleFileClick(item.metadata)}
                  >
                    {getPreviewComponent(fileType)}
                  </PreviewItem>
                );
              }
            })}

            {paginatedItems.length === 0 && (
              <div className="col-span-full flex items-center justify-center h-64 text-text-muted">
                No files or folders found
              </div>
            )}
          </div>
        </div>

        {/* Pagination footer */}
        <div className="flex-shrink-0 border-t border-terminal-border bg-background">
          {/* Items count */}
          <div className="text-center text-sm text-text-muted py-3">
            Showing {startIndex + 1}-{Math.min(endIndex, totalItems)} of{" "}
            {totalItems} items
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 px-4 sm:px-6 pb-4">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="px-3 sm:px-4 py-2 bg-terminal-bg border border-terminal-border text-text-primary hover:bg-terminal-border disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
              >
                Previous
              </button>

              <div className="flex gap-1">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map(
                  page => {
                    // Show first page, last page, current page, and pages around current
                    const showPage =
                      page === 1 ||
                      page === totalPages ||
                      (page >= currentPage - 1 && page <= currentPage + 1);

                    const showEllipsisBefore =
                      page === currentPage - 2 && currentPage > 3;
                    const showEllipsisAfter =
                      page === currentPage + 2 && currentPage < totalPages - 2;

                    if (
                      !showPage &&
                      !showEllipsisBefore &&
                      !showEllipsisAfter
                    ) {
                      return null;
                    }

                    if (showEllipsisBefore || showEllipsisAfter) {
                      return (
                        <span
                          key={`ellipsis-${page}`}
                          className="px-2 sm:px-3 py-2 text-text-muted text-sm"
                        >
                          ...
                        </span>
                      );
                    }

                    return (
                      <button
                        key={page}
                        onClick={() => handlePageChange(page)}
                        className={`px-3 sm:px-4 py-2 border transition-colors text-sm ${
                          page === currentPage
                            ? "bg-neon-green text-terminal-bg border-neon-green font-bold"
                            : "bg-terminal-bg border-terminal-border text-text-primary hover:bg-terminal-border"
                        }`}
                      >
                        {page}
                      </button>
                    );
                  }
                )}
              </div>

              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="px-3 sm:px-4 py-2 bg-terminal-bg border border-terminal-border text-text-primary hover:bg-terminal-border disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
              >
                Next
              </button>
            </div>
          )}
        </div>
      </div>

      {/* File Display Modals */}
      {selectedFile && (
        <FileDisplayWrapper
          onClose={handleCloseDisplay}
          onPrev={() => handleNavigate("prev")}
          onNext={() => handleNavigate("next")}
          hasPrev={
            filteredFiles.findIndex(f => f.filepath === selectedFile.filepath) >
            0
          }
          hasNext={
            filteredFiles.findIndex(f => f.filepath === selectedFile.filepath) <
            filteredFiles.length - 1
          }
        >
          {displayType === "image" && (
            <ImageDisplay
              filepath={selectedFile.filepath}
              onClose={handleCloseDisplay}
            />
          )}
          {displayType === "text" && (
            <TextDisplay
              filepath={selectedFile.filepath}
              onClose={handleCloseDisplay}
            />
          )}
          {displayType === "video" && (
            <VideoDisplay
              filepath={selectedFile.filepath}
              onClose={handleCloseDisplay}
            />
          )}
          {displayType === "music" && (
            <MusicDisplay
              filepath={selectedFile.filepath}
              onClose={handleCloseDisplay}
            />
          )}
        </FileDisplayWrapper>
      )}
    </>
  );
}
