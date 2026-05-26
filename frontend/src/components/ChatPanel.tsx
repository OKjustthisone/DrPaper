"use client";
import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: any[];
}

interface Props {
  notebookId: number;
  selectedSources: Set<number>;
  systemPrompt: string;
  onCitationClick: (citation: any) => void;
}

function CitationMarker({ num, citation, onClick }: { num: number; citation: any; onClick: () => void }) {
  return (
    <button onClick={onClick}
      className="inline-flex items-center justify-center w-5 h-5 text-[10px] font-bold bg-blue-100 text-blue-700 rounded-full mx-0.5 hover:bg-blue-200 transition-colors align-middle">
      {num}
    </button>
  );
}

function MessageBubble({ msg, onCitationClick }: { msg: Message; onCitationClick: (c: any) => void }) {
  const renderContent = (text: string, citations: any[]) => {
    if (!citations || citations.length === 0) return <p className="text-sm whitespace-pre-wrap">{text}</p>;

    const parts = text.split(/(\[\d+\])/g);
    return (
      <p className="text-sm whitespace-pre-wrap">
        {parts.map((part, i) => {
          const m = part.match(/\[(\d+)\]/);
          if (m) {
            const idx = parseInt(m[1]);
            const cit = citations.find(c => c.index === idx);
            if (cit) return <CitationMarker key={i} num={idx} citation={cit} onClick={() => onCitationClick(cit)} />;
          }
          return <span key={i}>{part}</span>;
        })}
      </p>
    );
  };

  return (
    <div className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} mb-4`}>
      <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
        msg.role === "user" ? "bg-[var(--color-primary)] text-white" : "bg-white border border-[var(--color-border)] shadow-sm"
      }`}>
        {msg.role === "user" ? (
          <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
        ) : (
          renderContent(msg.content, msg.citations || [])
        )}
        {msg.citations && msg.citations.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-100">
            <p className="text-[10px] text-[var(--color-text-muted)] mb-1">References:</p>
            <div className="flex flex-wrap gap-1">
              {msg.citations.map(c => (
                <button key={c.index} onClick={() => onCitationClick(c)}
                  className="text-[10px] px-2 py-0.5 bg-gray-100 hover:bg-blue-100 rounded-full text-[var(--color-text-muted)] hover:text-[var(--color-primary)] transition-colors">
                  [{c.index}] {c.filename}{c.page ? ` p.${c.page}` : ""}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ChatPanel({ notebookId, selectedSources, systemPrompt, onCitationClick }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const userMsg: Message = { role: "user", content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const result = await api.chat({
        notebook_id: notebookId,
        message: input,
        source_ids: selectedSources.size > 0 ? Array.from(selectedSources) : [],
      });
      setMessages(prev => [...prev, { role: "assistant", content: result.answer, citations: result.citations }]);
    } catch (e: any) {
      setMessages(prev => [...prev, { role: "assistant", content: `Error: ${e.message}` }]);
    }
    setLoading(false);
  };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {systemPrompt && (
        <div className="px-4 py-2 bg-amber-50 border-b border-amber-200 text-xs text-amber-800">
          System: {systemPrompt}
        </div>
      )}
      {selectedSources.size === 0 && (
        <div className="px-4 py-2 bg-blue-50 border-b border-blue-200 text-xs text-blue-700">
          No sources selected. Select sources in the left panel for grounded answers, or chat freely.
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-[var(--color-text-muted)]">
            <div className="text-center">
              <div className="text-3xl mb-2">💬</div>
              <p className="text-sm font-medium">Start a conversation</p>
              <p className="text-xs mt-1">Ask questions about your selected sources</p>
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} onCitationClick={onCitationClick} />
        ))}
        {loading && (
          <div className="flex justify-start mb-4">
            <div className="bg-white border border-[var(--color-border)] rounded-2xl px-4 py-3 shadow-sm">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" />
                <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }} />
                <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="p-4 border-t border-[var(--color-border)] bg-white">
        <div className="flex gap-2">
          <input className="flex-1 border border-[var(--color-border)] rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
            placeholder={selectedSources.size > 0 ? "Ask about selected sources..." : "Type a message..."}
            value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && !e.shiftKey && send()} />
          <button onClick={send} disabled={loading}
            className="px-5 py-2.5 bg-[var(--color-primary)] text-white rounded-xl text-sm font-medium hover:bg-[var(--color-primary-dark)] disabled:opacity-50 transition-colors">
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
