"use client";
import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface PaperResult {
  id: string;
  title: string;
  authors: string;
  abstract: string;
  year: string;
  source: string;
  url: string;
  full_text_url: string;
  doi: string;
  journal: string;
}

interface Props {
  notebookId: number;
  onImport: () => void;
  onClose: () => void;
}

const SOURCES = [
  { key: "pmc", label: "PubMed Central", icon: "🏥" },
  { key: "openalex", label: "OpenAlex", icon: "📖" },
  { key: "arxiv", label: "arXiv", icon: "📐" },
];

export default function SearchPanel({ notebookId, onImport, onClose }: Props) {
  const [query, setQuery] = useState("");
  const [selectedSources, setSelectedSources] = useState<Set<string>>(new Set(["pmc", "openalex", "arxiv"]));
  const [results, setResults] = useState<PaperResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState<Set<string>>(new Set());

  const toggleSource = (key: string) => {
    setSelectedSources(prev => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  };

  const search = async () => {
    if (!query.trim() || selectedSources.size === 0) return;
    setLoading(true);
    try {
      const sources = Array.from(selectedSources).join(",");
      const res = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(query)}&sources=${sources}&limit=15`);
      if (!res.ok) throw new Error("Search failed");
      const data = await res.json();
      setResults(data.results || []);
    } catch (e: any) {
      alert(`Search error: ${e.message}`);
    }
    setLoading(false);
  };

  const importPaper = async (paper: PaperResult) => {
    setImporting(prev => new Set(prev).add(paper.id));
    try {
      const res = await fetch(`${API_BASE}/api/search/import`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notebook_id: notebookId, paper_id: paper.id, title: paper.title }),
      });
      if (!res.ok) throw new Error("Import failed");
      onImport();
    } catch (e: any) {
      alert(`Import error: ${e.message}`);
    }
    setImporting(prev => { const next = new Set(prev); next.delete(paper.id); return next; });
  };

  return (
    <div className="flex-1 flex flex-col bg-white border-r border-[var(--color-border)] overflow-hidden min-w-0">
      {/* Header */}
      <div className="p-3 border-b border-[var(--color-border)] flex items-center justify-between">
        <span className="text-xs font-semibold uppercase text-[var(--color-text-muted)]">Search Literature</span>
        <button onClick={onClose} className="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)]">× Close</button>
      </div>

      {/* Search bar */}
      <div className="p-3 border-b border-[var(--color-border)]">
        <div className="flex gap-1 mb-2">
          {SOURCES.map(s => (
            <button key={s.key} onClick={() => toggleSource(s.key)}
              className={`text-[10px] px-2 py-1 rounded-full transition-colors ${
                selectedSources.has(s.key) ? "bg-[var(--color-primary)] text-white" : "bg-gray-100 text-[var(--color-text-muted)]"
              }`}>
              {s.icon} {s.label}
            </button>
          ))}
        </div>
        <div className="flex gap-1">
          <input className="flex-1 border border-[var(--color-border)] rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
            placeholder="Search papers..."
            value={query} onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === "Enter" && search()} />
          <button onClick={search} disabled={loading}
            className="px-3 py-1.5 bg-[var(--color-primary)] text-white rounded-lg text-xs font-medium hover:bg-[var(--color-primary-dark)] disabled:opacity-50">
            {loading ? "..." : "Search"}
          </button>
        </div>
      </div>

      {/* Results */}
      <div className="flex-1 overflow-y-auto">
        {results.length === 0 && !loading && (
          <p className="text-xs text-[var(--color-text-muted)] text-center py-8">
            Search across PMC, OpenAlex, and arXiv to find papers
          </p>
        )}
        {results.map(paper => (
          <div key={paper.id} className="p-3 border-b border-gray-100 hover:bg-gray-50 transition-colors">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <a href={paper.url} target="_blank" rel="noreferrer"
                  className="text-xs font-medium hover:text-[var(--color-primary)] transition-colors line-clamp-2">
                  {paper.title}
                </a>
                <p className="text-[10px] text-[var(--color-text-muted)] mt-1">
                  {paper.authors && `${paper.authors} · `}
                  {paper.journal && `${paper.journal} · `}
                  {paper.year}
                  <span className="ml-1 px-1 py-0.5 rounded bg-gray-100 text-[9px] uppercase">{paper.source}</span>
                </p>
                {paper.abstract && (
                  <p className="text-[10px] text-[var(--color-text-muted)] mt-1 line-clamp-3 leading-relaxed">
                    {paper.abstract}
                  </p>
                )}
              </div>
              <button onClick={() => importPaper(paper)}
                disabled={importing.has(paper.id)}
                className="shrink-0 px-2 py-1 bg-green-50 text-green-700 rounded text-[10px] font-medium hover:bg-green-100 disabled:opacity-50 transition-colors">
                {importing.has(paper.id) ? "..." : "Import"}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
