"use client";

import { useEffect, useState } from "react";

import { downloadFile } from "@/lib/api";

interface TextDisplayProps {
  filepath: string;
  onClose: () => void;
}

export default function TextDisplay({ filepath, onClose }: TextDisplayProps) {
  const [textContent, setTextContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadText = async () => {
      try {
        setLoading(true);
        const blob = await downloadFile(filepath);
        const text = await blob.text();
        setTextContent(text);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load text");
      } finally {
        setLoading(false);
      }
    };

    loadText();
  }, [filepath]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-90">
      <div className="relative max-h-[90vh] max-w-[90vw] w-[800px] bg-background-secondary rounded-lg shadow-terminal border border-terminal-border">
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

        <div className="p-6 overflow-auto max-h-[calc(90vh-80px)]">
          {loading && (
            <div className="flex items-center justify-center h-64">
              <div className="text-text-muted">Loading...</div>
            </div>
          )}

          {error && (
            <div className="flex items-center justify-center h-64">
              <div className="text-neon-red">{error}</div>
            </div>
          )}

          {textContent && !loading && !error && (
            <pre className="whitespace-pre-wrap font-mono text-sm text-text-secondary">
              {textContent}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
