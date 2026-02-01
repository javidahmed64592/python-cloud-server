import { ReactNode } from "react";

interface PreviewItemProps {
  filename: string;
  onClick: () => void;
  children: ReactNode;
}

export default function PreviewItem({
  filename,
  onClick,
  children,
}: PreviewItemProps) {
  return (
    <button
      onClick={onClick}
      className="group flex flex-col items-center gap-2 rounded-lg p-4 transition-all hover:bg-background-tertiary focus:outline-none focus:ring-2 focus:ring-neon-green"
    >
      <div className="h-24 w-24 rounded-lg border-2 border-terminal-border overflow-hidden">
        {children}
      </div>
      <span className="max-w-[120px] truncate text-sm text-text-secondary group-hover:text-neon-green transition-colors">
        {filename}
      </span>
    </button>
  );
}
