"use client";

import Image from "next/image";
import { useEffect, useState } from "react";

import { downloadFile } from "@/lib/api";

interface ImageDisplayProps {
  filepath: string;
  onClose: () => void;
}

export default function ImageDisplay({ filepath, onClose }: ImageDisplayProps) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let objectUrl: string | null = null;

    const loadImage = async () => {
      try {
        setLoading(true);
        setError(null);
        const blob = await downloadFile(filepath);
        objectUrl = URL.createObjectURL(blob);
        setImageUrl(objectUrl);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load image");
      } finally {
        setLoading(false);
      }
    };

    loadImage();

    return () => {
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [filepath]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-90">
      <div className="relative max-h-[90vh] max-w-[90vw] bg-background-secondary rounded-lg shadow-terminal border border-terminal-border">
        <div className="flex items-center justify-between border-b border-terminal-border p-4">
          <h2 className="text-lg font-semibold text-text-primary truncate">
            {filepath.split("/").pop()}
          </h2>
          <button
            onClick={onClose}
            className="rounded-lg p-2 hover:bg-background-tertiary transition-colors"
          >
            <span className="text-2xl text-neon-red">&times;</span>
          </button>
        </div>

        <div className="p-6">
          {loading && (
            <div className="flex items-center justify-center h-64 w-96">
              <div className="text-text-muted">Loading...</div>
            </div>
          )}

          {error && (
            <div className="flex items-center justify-center h-64 w-96">
              <div className="text-neon-red">{error}</div>
            </div>
          )}

          {imageUrl && !loading && !error && (
            <div className="relative flex items-center justify-center">
              <Image
                src={imageUrl}
                alt={filepath}
                width={1920}
                height={1080}
                className="max-h-[70vh] max-w-full object-contain h-auto w-auto"
                unoptimized
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
