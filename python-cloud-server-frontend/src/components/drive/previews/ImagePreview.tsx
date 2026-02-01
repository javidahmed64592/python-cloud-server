"use client";

import Image from "next/image";
import { useEffect, useState } from "react";

import { getThumbnail } from "@/lib/api";

interface ImagePreviewProps {
  filepath: string;
}

export default function ImagePreview({ filepath }: ImagePreviewProps) {
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
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-neon-green border-t-transparent" />
      </div>
    );
  }

  if (error || !thumbnailUrl) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-background-secondary">
        <div className="relative h-16 w-16 text-neon-green">
          <Image
            src="/icons/image-icon.svg"
            alt="Image file"
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
        alt="Image thumbnail"
        fill
        className="object-cover"
        unoptimized
      />
    </div>
  );
}
