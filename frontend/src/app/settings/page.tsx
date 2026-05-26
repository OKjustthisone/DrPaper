"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const [models, setModels] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ provider: "google", model_name: "", display_name: "", api_key: "", base_url: "" });

  const load = () => api.listModels().then(setModels).catch(console.error);
  useEffect(() => { load(); }, []);

  const addModel = async () => {
    if (!form.model_name) return;
    await api.createModel(form);
    setForm({ provider: "google", model_name: "", display_name: "", api_key: "", base_url: "" });
    setShowForm(false);
    load();
  };

  const toggleActive = async (m: any) => {
    await api.updateModel(m.id, { is_active: !m.is_active });
    load();
  };

  const deleteModel = async (id: number) => {
    await api.deleteModel(id);
    load();
  };

  const providers = [
    { value: "google", label: "Google Gemini" },
    { value: "openai", label: "OpenAI" },
    { value: "anthropic", label: "Anthropic Claude" },
    { value: "deepseek", label: "DeepSeek" },
    { value: "ollama", label: "Ollama / Local" },
  ];

  return (
    <div className="max-w-3xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Model Hub</h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">Configure AI models for DrPaper</p>
        </div>
        <div className="flex gap-2">
          <Link href="/" className="px-4 py-2 border border-[var(--color-border)] rounded-lg text-sm hover:bg-gray-50 transition-colors">Back</Link>
          <button onClick={() => setShowForm(!showForm)}
            className="px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg text-sm font-medium hover:bg-[var(--color-primary-dark)] transition-colors">
            + Add Model
          </button>
        </div>
      </div>

      {showForm && (
        <div className="bg-white border border-[var(--color-border)] rounded-xl p-6 mb-6 shadow-sm">
          <h2 className="font-semibold mb-4">Add Model</h2>
          <div className="grid gap-3">
            <select className="border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm" value={form.provider}
              onChange={e => setForm({ ...form, provider: e.target.value })}>
              {providers.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
            </select>
            <input className="border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm" placeholder="Model name (e.g. gemini-2.5-flash)"
              value={form.model_name} onChange={e => setForm({ ...form, model_name: e.target.value })} />
            <input className="border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm" placeholder="Display name (optional)"
              value={form.display_name} onChange={e => setForm({ ...form, display_name: e.target.value })} />
            <input className="border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm" placeholder="API Key"
              type="password" value={form.api_key} onChange={e => setForm({ ...form, api_key: e.target.value })} />
            <input className="border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm" placeholder="Base URL (for local/Ollama: http://localhost:11434/v1)"
              value={form.base_url} onChange={e => setForm({ ...form, base_url: e.target.value })} />
          </div>
          <div className="flex gap-2 mt-4">
            <button onClick={addModel} className="px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg text-sm">Add</button>
            <button onClick={() => setShowForm(false)} className="px-4 py-2 border rounded-lg text-sm">Cancel</button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {models.map(m => (
          <div key={m.id} className="bg-white border border-[var(--color-border)] rounded-xl p-4 flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm">{m.display_name || m.model_name}</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-[var(--color-text-muted)]">{m.provider}</span>
              </div>
              <p className="text-xs text-[var(--color-text-muted)] mt-1">{m.model_name}</p>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={() => toggleActive(m)}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  m.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-400"
                }`}>
                {m.is_active ? "Active" : "Inactive"}
              </button>
              <button onClick={() => deleteModel(m.id)} className="px-2 py-1 text-xs text-red-400 hover:text-red-600">Delete</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
