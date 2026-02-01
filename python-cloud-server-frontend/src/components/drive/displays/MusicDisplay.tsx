"use client";

import { useEffect, useState } from "react";

import { downloadFile } from "@/lib/api";

interface MusicDisplayProps {
  filepath: string;
  onClose: () => void;
}

export default function MusicDisplay({ filepath, onClose }: MusicDisplayProps) {
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let objectUrl: string | null = null;

    const loadAudio = async () => {
      try {
        setLoading(true);
        setError(null);
        const blob = await downloadFile(filepath);
        objectUrl = URL.createObjectURL(blob);
        setAudioUrl(objectUrl);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load audio");
      } finally {
        setLoading(false);
      }
    };

    loadAudio();

    return () => {
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [filepath]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-90">
      <div className="relative w-full max-w-[600px] bg-background-secondary rounded-lg shadow-terminal border border-terminal-border">
        <div className="flex items-center justify-between border-b border-terminal-border p-4">
          <h2 className="text-lg font-semibold text-text-primary truncate max-w-[500px]">
            {filepath.split("/").pop()}
          </h2>
          <button
            onClick={onClose}
            className="rounded-lg p-2 hover:bg-background-tertiary transition-colors flex-shrink-0"
          >
            <span className="text-2xl text-neon-red">&times;</span>
          </button>
        </div>

        <div className="p-6">
          {loading && (
            <div className="flex items-center justify-center h-32">
              <div className="text-text-muted">Loading audio...</div>
            </div>
          )}

          {error && (
            <div className="flex items-center justify-center h-32">
              <div className="text-neon-red">Failed to load audio</div>
            </div>
          )}

          {audioUrl && !loading && !error && (
            <div className="w-full">
              <audio
                data-testid="audio-element"
                src={audioUrl}
                controls
                controlsList="nodownload"
                className="w-full"
                style={{ minHeight: "54px" }}
              >
                Your browser does not support the audio tag.
              </audio>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
