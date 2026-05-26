"use client";

interface Props {
  citation: any;
  onClose: () => void;
}

const ICON_MAP: Record<string, string> = {
  flask: "🧪", chart: "📊", brain: "🧠", dna: "🧬", pill: "💊",
  microscope: "🔬", target: "🎯", lightbulb: "💡", document: "📄", beaker: "⚗️",
};

export default function CitationSidebar({ citation, onClose }: Props) {
  if (!citation) return null;

  return (
    <aside className="w-80 bg-white border-l border-[var(--color-border)] flex flex-col shrink-0 overflow-hidden">
      <div className="p-3 border-b border-[var(--color-border)] flex items-center justify-between">
        <span className="text-xs font-semibold text-[var(--color-text-muted)] uppercase">Reference [{citation.index}]</span>
        <button onClick={onClose} className="text-[var(--color-text-muted)] hover:text-[var(--color-text)] text-sm">×</button>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        <div className="mb-3">
          <p className="text-xs text-[var(--color-text-muted)]">Source</p>
          <p className="text-sm font-medium">{citation.filename}</p>
        </div>
        {citation.page && (
          <div className="mb-3">
            <p className="text-xs text-[var(--color-text-muted)]">Page</p>
            <p className="text-sm">{citation.page}</p>
          </div>
        )}
        <div>
          <p className="text-xs text-[var(--color-text-muted)] mb-1">Content</p>
          <div className="bg-gray-50 rounded-lg p-3 text-sm leading-relaxed whitespace-pre-wrap citation-flash">
            {citation.text}
          </div>
        </div>
      </div>
    </aside>
  );
}
