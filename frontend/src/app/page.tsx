"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

export default function Home() {
  const [notebooks, setNotebooks] = useState<any[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [sysPrompt, setSysPrompt] = useState("");

  const load = () => api.listNotebooks().then(setNotebooks).catch(console.error);

  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!name.trim()) return;
    await api.createNotebook({ name: name.trim(), description: desc, system_prompt: sysPrompt });
    setName(""); setDesc(""); setSysPrompt(""); setShowCreate(false);
    load();
  };

  const deleteNb = async (id: number) => {
    if (!confirm("Delete this notebook and all its data?")) return;
    await api.deleteNotebook(id);
    load();
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <header className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">DrPaper</h1>
          <p className="text-[var(--color-text-muted)] mt-1">Personal AI Research Assistant</p>
        </div>
        <div className="flex gap-3">
          <Link href="/settings" className="px-4 py-2 border border-[var(--color-border)] rounded-lg text-sm hover:bg-gray-50 transition-colors">
            Settings
          </Link>
          <button onClick={() => setShowCreate(!showCreate)}
            className="px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg text-sm font-medium hover:bg-[var(--color-primary-dark)] transition-colors">
            + New Notebook
          </button>
        </div>
      </header>

      {showCreate && (
        <div className="bg-white border border-[var(--color-border)] rounded-xl p-6 mb-6 shadow-sm">
          <h2 className="font-semibold mb-4">Create New Notebook</h2>
          <input className="w-full border border-[var(--color-border)] rounded-lg px-3 py-2 mb-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
            placeholder="Notebook name" value={name} onChange={e => setName(e.target.value)} />
          <input className="w-full border border-[var(--color-border)] rounded-lg px-3 py-2 mb-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
            placeholder="Description (optional)" value={desc} onChange={e => setDesc(e.target.value)} />
          <textarea className="w-full border border-[var(--color-border)] rounded-lg px-3 py-2 mb-4 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
            rows={2} placeholder="System prompt, e.g. 'You are a senior biomedical researcher...' (optional)"
            value={sysPrompt} onChange={e => setSysPrompt(e.target.value)} />
          <div className="flex gap-2">
            <button onClick={create} className="px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg text-sm font-medium hover:bg-[var(--color-primary-dark)] transition-colors">
              Create</button>
            <button onClick={() => setShowCreate(false)} className="px-4 py-2 border border-[var(--color-border)] rounded-lg text-sm hover:bg-gray-50 transition-colors">Cancel</button>
          </div>
        </div>
      )}

      <div className="grid gap-4">
        {notebooks.length === 0 && (
          <div className="text-center py-16 text-[var(--color-text-muted)]">
            <div className="text-5xl mb-4">📚</div>
            <p className="text-lg font-medium">No notebooks yet</p>
            <p className="text-sm mt-1">Create your first notebook to start researching</p>
          </div>
        )}
        {notebooks.map(nb => (
          <div key={nb.id} className="bg-white border border-[var(--color-border)] rounded-xl p-5 hover:shadow-md transition-shadow group">
            <div className="flex items-start justify-between">
              <Link href={`/notebook/${nb.id}`} className="flex-1">
                <h3 className="font-semibold text-lg hover:text-[var(--color-primary)] transition-colors">{nb.name}</h3>
                {nb.description && <p className="text-sm text-[var(--color-text-muted)] mt-1">{nb.description}</p>}
                <p className="text-xs text-[var(--color-text-muted)] mt-3">Updated: {nb.updated_at}</p>
              </Link>
              <button onClick={() => deleteNb(nb.id)}
                className="opacity-0 group-hover:opacity-100 px-3 py-1 text-xs text-red-500 hover:bg-red-50 rounded transition-all">
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
