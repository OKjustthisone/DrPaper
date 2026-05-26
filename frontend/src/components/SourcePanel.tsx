"use client";
import { useRef, useState } from "react";

interface Props {
  sources: any[];
  selectedSources: Set<number>;
  onToggle: (id: number) => void;
  onUpload: (file: File) => Promise<void>;
  onDelete: (id: number) => void;
}

export default function SourcePanel({ sources, selectedSources, onToggle, onUpload, onDelete }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try { await onUpload(file); } catch (err) { alert("Upload failed"); }
    setUploading(false);
    if (fileRef.current) fileRef.current.value = "";
  };

  const selectAll = () => sources.forEach(s => onToggle(s.id));
  const deselectAll = () => selectedSources.forEach(id => onToggle(id));

  return (
    <aside className="w-64 bg-white border-r border-[var(--color-border)] flex flex-col shrink-0">
      <div className="p-3 border-b border-[var(--color-border)]">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Sources</span>
          <div className="flex gap-1">
            <button onClick={selectAll} className="text-xs text-[var(--color-primary)] hover:underline">All</button>
            <button onClick={deselectAll} className="text-xs text-[var(--color-text-muted)] hover:underline">None</button>
          </div>
        </div>
        <label className={`flex items-center justify-center gap-1 px-3 py-2 border-2 border-dashed rounded-lg text-xs cursor-pointer transition-colors
          ${uploading ? "border-[var(--color-primary)] bg-blue-50" : "border-[var(--color-border)] hover:border-[var(--color-primary)] hover:bg-gray-50"}`}>
          <span>{uploading ? "Uploading..." : "+ Upload File"}</span>
          <input ref={fileRef} type="file" className="hidden" accept=".pdf,.docx,.md,.txt,.csv,.xlsx,.png,.jpg,.jpeg"
            onChange={handleFile} disabled={uploading} />
        </label>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {sources.length === 0 && (
          <p className="text-xs text-[var(--color-text-muted)] text-center py-8">No sources yet. Upload PDF, DOCX, CSV, etc.</p>
        )}
        {sources.map(s => (
          <div key={s.id} className={`flex items-center gap-2 p-2 rounded-lg mb-1 cursor-pointer transition-colors group
            ${selectedSources.has(s.id) ? "bg-blue-50" : "hover:bg-gray-50"}`}>
            <input type="checkbox" checked={selectedSources.has(s.id)}
              onChange={() => onToggle(s.id)} className="shrink-0" />
            <div className="flex-1 min-w-0" onClick={() => onToggle(s.id)}>
              <p className="text-xs truncate font-medium">{s.filename}</p>
              <p className="text-[10px] text-[var(--color-text-muted)]">
                {s.file_type} · {s.chunk_count} chunks · {s.status}
              </p>
            </div>
            <button onClick={() => onDelete(s.id)}
              className="opacity-0 group-hover:opacity-100 text-[10px] text-red-400 hover:text-red-600 shrink-0 transition-opacity">
              ×
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
}
