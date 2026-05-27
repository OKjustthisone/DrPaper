"use client";
import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import SourcePanel from "@/components/SourcePanel";
import SearchPanel from "@/components/SearchPanel";
import ChatPanel from "@/components/ChatPanel";
import ArtifactPanel from "@/components/ArtifactPanel";
import CitationSidebar from "@/components/CitationSidebar";

export default function NotebookPage() {
  const params = useParams();
  const router = useRouter();
  const notebookId = Number(params.id);

  const [notebook, setNotebook] = useState<any>(null);
  const [sources, setSources] = useState<any[]>([]);
  const [selectedSources, setSelectedSources] = useState<Set<number>>(new Set());
  const [activeTab, setActiveTab] = useState<"chat" | "artifacts">("chat");
  const [activeCitation, setActiveCitation] = useState<any>(null);
  const [showSearch, setShowSearch] = useState(false);

  const loadNotebook = () => api.getNotebook(notebookId).then(setNotebook).catch(() => router.push("/"));
  const loadSources = () => api.listSources(notebookId).then(setSources);

  useEffect(() => { loadNotebook(); loadSources(); }, [notebookId]);

  const handleSourceUpload = async (file: File) => {
    await api.uploadFile(notebookId, file);
    loadSources();
  };

  const handleDeleteSource = async (id: number) => {
    await api.deleteSource(id);
    setSelectedSources(prev => { const next = new Set(prev); next.delete(id); return next; });
    loadSources();
  };

  const toggleSource = (id: number) => {
    setSelectedSources(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const handleCitationClick = (citation: any) => {
    setActiveCitation(citation);
  };

  if (!notebook) return <div className="flex items-center justify-center h-screen text-[var(--color-text-muted)]">Loading...</div>;

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="h-12 bg-white border-b border-[var(--color-border)] flex items-center px-4 shrink-0 z-10">
        <button onClick={() => router.push("/")} className="text-[var(--color-text-muted)] hover:text-[var(--color-text)] mr-3 text-sm">
          ← Back
        </button>
        <h1 className="font-semibold text-sm truncate">{notebook.name}</h1>
        <span className="text-xs text-[var(--color-text-muted)] ml-3">{sources.length} sources</span>
        <div className="ml-auto flex items-center gap-1">
          <button onClick={() => setActiveTab("chat")}
            className={`px-3 py-1 text-xs rounded-md transition-colors ${activeTab === "chat" ? "bg-[var(--color-primary)] text-white" : "hover:bg-gray-100"}`}>
            Chat
          </button>
          <button onClick={() => setActiveTab("artifacts")}
            className={`px-3 py-1 text-xs rounded-md transition-colors ${activeTab === "artifacts" ? "bg-[var(--color-primary)] text-white" : "hover:bg-gray-100"}`}>
            Artifacts
          </button>
        </div>
      </header>

      {/* Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Sources or Search */}
        {showSearch ? (
          <SearchPanel
            notebookId={notebookId}
            onImport={() => { loadSources(); }}
            onClose={() => setShowSearch(false)}
          />
        ) : (
          <SourcePanel
            sources={sources}
            selectedSources={selectedSources}
            onToggle={toggleSource}
            onUpload={handleSourceUpload}
            onDelete={handleDeleteSource}
            onSearchOpen={() => setShowSearch(true)}
          />
        )}

        {/* Center: Chat or Artifacts */}
        <div className="flex-1 flex flex-col min-w-0">
          {activeTab === "chat" ? (
            <ChatPanel
              notebookId={notebookId}
              selectedSources={selectedSources}
              systemPrompt={notebook.system_prompt}
              onCitationClick={handleCitationClick}
            />
          ) : (
            <ArtifactPanel
              notebookId={notebookId}
              selectedSources={selectedSources}
            />
          )}
        </div>

        {/* Right: Citation Sidebar */}
        {activeCitation && (
          <CitationSidebar
            citation={activeCitation}
            onClose={() => setActiveCitation(null)}
          />
        )}
      </div>
    </div>
  );
}
