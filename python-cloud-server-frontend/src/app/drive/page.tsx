"use client";

import { useEffect, useState } from "react";

import PreviewGrid from "@/components/drive/previews/PreviewGrid";
import { getFiles } from "@/lib/api";
import type { FileMetadata } from "@/lib/types";

export default function DrivePage() {
  const [files, setFiles] = useState<FileMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadFiles = async () => {
      try {
        setLoading(true);
        const response = await getFiles({ limit: 10000 });
        setFiles(response.files);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load files");
      } finally {
        setLoading(false);
      }
    };

    loadFiles();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-gray-500">Loading files...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto">
        <div className="border-b border-terminal-border p-6">
          <h1 className="text-3xl font-bold text-text-primary">My Drive</h1>
          <p className="mt-2 text-text-muted">
            {files.length} {files.length === 1 ? "file" : "files"}
          </p>
        </div>

        <PreviewGrid files={files} />
      </div>
    </div>
  );
}
