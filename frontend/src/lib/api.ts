const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `API error: ${res.status}`);
  }
  return res.json();
}

// Notebooks
export const api = {
  // Notebooks
  listNotebooks: () => request<any[]>("/api/notebooks"),
  getNotebook: (id: number) => request<any>(`/api/notebooks/${id}`),
  createNotebook: (data: { name: string; description?: string; system_prompt?: string }) =>
    request<any>("/api/notebooks", { method: "POST", body: JSON.stringify(data) }),
  updateNotebook: (id: number, data: any) =>
    request<any>(`/api/notebooks/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteNotebook: (id: number) =>
    request<any>(`/api/notebooks/${id}`, { method: "DELETE" }),

  // Sources
  listSources: (notebookId: number) =>
    request<any[]>(`/api/sources?notebook_id=${notebookId}`),
  deleteSource: (id: number) =>
    request<any>(`/api/sources/${id}`, { method: "DELETE" }),

  // Upload file
  uploadFile: async (notebookId: number, file: File) => {
    const form = new FormData();
    form.append("notebook_id", String(notebookId));
    form.append("file", file);
    const res = await fetch(`${API_BASE}/api/sources/upload`, { method: "POST", body: form });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Chat
  chat: (data: { notebook_id: number; message: string; source_ids?: number[]; model_key?: string }) =>
    request<any>("/api/chat", { method: "POST", body: JSON.stringify(data) }),
  chatHistory: (notebookId: number) =>
    request<any[]>(`/api/chat/history/${notebookId}`),

  // Artifacts
  generateSlideDeck: (data: any) =>
    request<any>("/api/artifacts/slide-deck", { method: "POST", body: JSON.stringify(data) }),
  generateInfographic: (data: any) =>
    request<any>("/api/artifacts/infographic", { method: "POST", body: JSON.stringify(data) }),
  generateDataTable: (data: any) =>
    request<any>("/api/artifacts/data-table", { method: "POST", body: JSON.stringify(data) }),
  listArtifacts: (notebookId: number) =>
    request<any[]>(`/api/artifacts/${notebookId}`),

  // Models
  listModels: () => request<any[]>("/api/models"),
  createModel: (data: any) =>
    request<any>("/api/models", { method: "POST", body: JSON.stringify(data) }),
  updateModel: (id: number, data: any) =>
    request<any>(`/api/models/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteModel: (id: number) =>
    request<any>(`/api/models/${id}`, { method: "DELETE" }),
};
