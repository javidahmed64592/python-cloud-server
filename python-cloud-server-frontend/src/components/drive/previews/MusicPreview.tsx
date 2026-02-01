import Image from "next/image";

export default function MusicPreview() {
  return (
    <div className="flex h-full w-full items-center justify-center bg-background-secondary">
      <div className="relative h-16 w-16 text-neon-purple">
        <Image
          src="/icons/music-icon.svg"
          alt="Music file"
          fill
          className="object-contain"
          unoptimized
        />
      </div>
    </div>
  );
}
