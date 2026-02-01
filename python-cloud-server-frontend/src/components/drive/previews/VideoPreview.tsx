"use client";

import Image from "next/image";
import { useEffect, useState } from "react";

import { getThumbnail } from "@/lib/api";

interface VideoPreviewProps {
  filepath: string;
}

export default function VideoPreview({ filepath }: VideoPreviewProps) {
  const [thumbnailUrl, setThumbnailUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let isMounted = true;
    let currentUrl: string | null = null;

    const loadThumbnail = async () => {
      try {
        setLoading(true);
        setError(false);
        const url = await getThumbnail(filepath);
        if (isMounted) {
          currentUrl = url;
          setThumbnailUrl(url);
          setLoading(false);
        } else {
          // If unmounted before setting state, revoke immediately
          URL.revokeObjectURL(url);
        }
      } catch {
        if (isMounted) {
          setError(true);
          setLoading(false);
        }
      }
    };

    loadThumbnail();

    return () => {
      isMounted = false;
      if (currentUrl) {
        URL.revokeObjectURL(currentUrl);
      }
    };
  }, [filepath]);

  if (loading) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-background-secondary">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-neon-blue border-t-transparent" />
      </div>
    );
  }

  if (error || !thumbnailUrl) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-background-secondary">
        <div className="relative h-16 w-16 text-neon-blue">
          <Image
            src="/icons/video-icon.svg"
            alt="Video file"
            fill
            className="object-contain"
            unoptimized
          />
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex h-full w-full items-center justify-center bg-background-secondary">
      <Image
        src={thumbnailUrl}
        alt="Video thumbnail"
        fill
        className="object-cover"
        unoptimized
      />
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="rounded-full bg-black/50 p-3">
          <div className="relative h-8 w-8 text-white">
            <Image
              src="/icons/video-icon.svg"
              alt="Play"
              fill
              className="object-contain"
              unoptimized
            />
          </div>
        </div>
      </div>
    </div>
  );
}
