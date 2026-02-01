import Image from "next/image";

export default function FolderPreview() {
  return (
    <div className="flex h-full w-full items-center justify-center bg-background-secondary">
      <div className="relative h-16 w-16 text-neon-green">
        <Image
          src="/icons/folder-icon.svg"
          alt="Folder"
          fill
          className="object-contain"
          unoptimized
        />
      </div>
    </div>
  );
}
