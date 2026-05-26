"use client";
import { useState } from "react";
import { api } from "@/lib/api";

const ICON_MAP: Record<string, string> = {
  flask: "🧪", chart: "📊", brain: "🧠", dna: "🧬", pill: "💊",
  microscope: "🔬", target: "🎯", lightbulb: "💡", document: "📄", beaker: "⚗️",
};

interface Props {
  notebookId: number;
  selectedSources: Set<number>;
}

export default function ArtifactPanel({ notebookId, selectedSources }: Props) {
  const [mode, setMode] = useState<"slide" | "infographic" | "table" | null>(null);
  const [instruction, setInstruction] = useState("");
  const [chartType, setChartType] = useState<"bento_grid" | "timeline" | "comparison">("bento_grid");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const sourceIds = selectedSources.size > 0 ? Array.from(selectedSources) : [];

  const generate = async () => {
    setLoading(true);
    setResult(null);
    try {
      if (mode === "slide") {
        const r = await api.generateSlideDeck({ notebook_id: notebookId, source_ids: sourceIds, instruction });
        setResult({ type: "slide", data: r });
      } else if (mode === "infographic") {
        const r = await api.generateInfographic({ notebook_id: notebookId, source_ids: sourceIds, chart_type: chartType, instruction });
        setResult({ type: "infographic", data: r });
      } else if (mode === "table") {
        const r = await api.generateDataTable({ notebook_id: notebookId, source_ids: sourceIds, instruction });
        setResult({ type: "table", data: r });
      }
    } catch (e: any) {
      alert(`Error: ${e.message}`);
    }
    setLoading(false);
  };

  if (!mode) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-lg font-semibold mb-2">Visual Artifacts Studio</h2>
          <p className="text-sm text-[var(--color-text-muted)] mb-6">Turn your sources into visual artifacts</p>
          <div className="grid grid-cols-3 gap-4 max-w-lg mx-auto">
            {([
              { id: "slide", icon: "📽️", title: "Slide Deck", desc: "Generate presentation outlines from sources" },
              { id: "infographic", icon: "🎨", title: "Infographic", desc: "Bento Grid, Timeline, Comparison charts" },
              { id: "table", icon: "📋", title: "Data Table", desc: "Cross-document data extraction matrix" },
            ] as const).map(item => (
              <button key={item.id} onClick={() => setMode(item.id)}
                className="bg-white border border-[var(--color-border)] rounded-xl p-4 hover:border-[var(--color-primary)] hover:shadow-md transition-all text-center">
                <div className="text-2xl mb-2">{item.icon}</div>
                <p className="text-sm font-medium">{item.title}</p>
                <p className="text-[10px] text-[var(--color-text-muted)] mt-1">{item.desc}</p>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-3xl mx-auto">
        <button onClick={() => { setMode(null); setResult(null); }}
          className="text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text)] mb-4">← Back</button>

        <h2 className="text-lg font-semibold mb-4">
          {mode === "slide" ? "Slide Deck Generator" : mode === "infographic" ? "Infographic Generator" : "Data Table Generator"}
        </h2>

        <div className="bg-white border border-[var(--color-border)] rounded-xl p-4 mb-6">
          {mode === "infographic" && (
            <div className="mb-3">
              <label className="text-xs font-medium text-[var(--color-text-muted)]">Chart Type</label>
              <select className="w-full border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm mt-1"
                value={chartType} onChange={e => setChartType(e.target.value as any)}>
                <option value="bento_grid">Bento Grid - Key insight cards</option>
                <option value="timeline">Timeline - Chronological flow</option>
                <option value="comparison">Comparison - Side-by-side comparison</option>
              </select>
            </div>
          )}
          <label className="text-xs font-medium text-[var(--color-text-muted)]">Instructions (optional)</label>
          <textarea className="w-full border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm mt-1"
            rows={2} placeholder="e.g. Focus on methodology comparison between the 3 studies..."
            value={instruction} onChange={e => setInstruction(e.target.value)} />
          <button onClick={generate} disabled={loading}
            className="mt-3 px-5 py-2 bg-[var(--color-primary)] text-white rounded-lg text-sm font-medium hover:bg-[var(--color-primary-dark)] disabled:opacity-50 transition-colors">
            {loading ? "Generating..." : "Generate"}
          </button>
        </div>

        {result && result.type === "slide" && <SlideResult data={result.data} />}
        {result && result.type === "infographic" && <InfographicResult data={result.data} />}
        {result && result.type === "table" && <TableResult data={result.data} />}
      </div>
    </div>
  );
}

function SlideResult({ data }: { data: any }) {
  return (
    <div className="space-y-3">
      <h3 className="font-semibold text-base">{data.title}</h3>
      {data.slides?.map((slide: any, i: number) => (
        <div key={i} className="bg-white border border-[var(--color-border)] rounded-xl p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <span className="w-6 h-6 rounded-full bg-[var(--color-primary)] text-white text-xs flex items-center justify-center">{i + 1}</span>
            <h4 className="font-semibold text-sm">{slide.title}</h4>
          </div>
          <ul className="space-y-1 ml-8">
            {slide.bullet_points?.map((bp: string, j: number) => (
              <li key={j} className="text-sm text-[var(--color-text-muted)] list-disc">{bp}</li>
            ))}
          </ul>
          {slide.notes && <p className="ml-8 mt-2 text-xs text-[var(--color-text-muted)] italic">Notes: {slide.notes}</p>}
        </div>
      ))}
    </div>
  );
}

function InfographicResult({ data }: { data: any }) {
  const gridCols = data.chart_type === "comparison" ? "grid-cols-2" : "grid-cols-1 sm:grid-cols-2";
  return (
    <div>
      <h3 className="font-semibold text-base mb-3">{data.title}</h3>
      <div className={`grid ${gridCols} gap-3`}>
        {data.nodes?.map((node: any) => (
          <div key={node.id} className="bg-white border border-[var(--color-border)] rounded-xl p-4 shadow-sm"
            style={node.color ? { borderLeftColor: node.color, borderLeftWidth: "3px" } : {}}>
            <div className="flex items-center gap-2 mb-2">
              {node.icon && <span>{ICON_MAP[node.icon] || "📌"}</span>}
              <h4 className="font-semibold text-sm">{node.title}</h4>
            </div>
            <p className="text-sm text-[var(--color-text-muted)]">{node.content}</p>
            {node.connections?.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {node.connections.map((c: string) => (
                  <span key={c} className="text-[10px] px-2 py-0.5 bg-gray-100 rounded-full text-[var(--color-text-muted)]">→ {c}</span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function TableResult({ data }: { data: any }) {
  return (
    <div className="bg-white border border-[var(--color-border)] rounded-xl overflow-hidden shadow-sm">
      <h3 className="font-semibold text-base p-4 border-b border-[var(--color-border)]">{data.title}</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50">
              {data.columns?.map((col: string, i: number) => (
                <th key={i} className="text-left px-4 py-2 font-medium text-xs text-[var(--color-text-muted)] border-b border-[var(--color-border)]">{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.rows?.map((row: string[], i: number) => (
              <tr key={i} className="hover:bg-gray-50 transition-colors">
                {row.map((cell, j) => (
                  <td key={j} className="px-4 py-2 border-b border-gray-100">{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
