import Image from "next/image";

export default function VideoPreview() {
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
