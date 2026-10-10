import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Zap } from "lucide-react";
import client from "../api/client";
import { celebrate } from "../utils/celebrate";

const STATUS_TEXT = {
  confirming: "Working on it…",
  confirmed: "✓ Confirmed",
  cancelled: "Cancelled",
  failed: "Didn't go through",
};

export default function ChatWidget({
  endpoint = "/chat",
  greeting = "heyy 👋 I'm Kai — ask me about your team, or tell me what to do, like \"create a task for Priya to fix the login bug\".",
  placeholder = "Ask Kai or tell it what to do…",
  label = "Kai",
  onDataChanged,
}) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([{ role: "assistant", content: greeting }]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  function addMessage(message) {
    setMessages((prev) => [...prev, message]);
  }

  function setActionStatus(index, status) {
    setMessages((prev) =>
      prev.map((m, i) => (i === index ? { ...m, action: { ...m.action, status } } : m))
    );
  }

  async function handleSend(e) {
    e.preventDefault();
    if (!input.trim() || sending) return;
    const question = input.trim();
    addMessage({ role: "user", content: question });
    setInput("");
    setSending(true);
    try {
      const res = await client.post(endpoint, { message: question });
      const { reply, action_token, action_summaries } = res.data;
      addMessage({
        role: "assistant",
        content: reply,
        action: action_token
          ? { token: action_token, summaries: action_summaries || [], status: "pending" }
          : undefined,
      });
    } catch (err) {
      const detail = err?.response?.data?.detail || "Something went wrong. Try again.";
      addMessage({ role: "assistant", content: detail });
    } finally {
      setSending(false);
    }
  }

  // Kai proposed an action; the user pressed Confirm or Cancel.
  async function handleAction(index, approve) {
    const action = messages[index]?.action;
    if (!action || action.status !== "pending" || sending) return;

    if (!approve) {
      setActionStatus(index, "cancelled");
      addMessage({ role: "assistant", content: "No problem, I've cancelled that." });
      return;
    }

    setActionStatus(index, "confirming");
    setSending(true);
    try {
      const res = await client.post("/chat/confirm", { action_token: action.token });
      setActionStatus(index, "confirmed");
      addMessage({ role: "assistant", content: res.data.reply });
      if (res.data.celebrate) celebrate();
      if (onDataChanged) onDataChanged();
    } catch (err) {
      setActionStatus(index, "failed");
      addMessage({
        role: "assistant",
        content: err?.response?.data?.detail || "Something went wrong. Try again.",
      });
    } finally {
      setSending(false);
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 bg-gradient-to-br from-accent to-accent2 text-white rounded-full w-14 h-14 flex items-center justify-center text-xl shadow-lg shadow-accent2/30 hover:scale-105 transition-transform"
        title={`Chat with ${label}`}
      >
        ✨
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 w-96 h-[32rem] bg-surface border border-border rounded-lg shadow-xl flex flex-col overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-gradient-to-r from-accent/10 to-accent2/10">
        <span className="text-sm font-display font-bold bg-gradient-to-r from-accent to-accent2 bg-clip-text text-transparent">
          ✨ {label}
        </span>
        <button onClick={() => setOpen(false)} className="text-text-muted hover:text-text text-sm">✕</button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {messages.map((m, i) =>
          m.role === "user" ? (
            <div key={i} className="text-sm max-w-[85%] px-3 py-2 rounded-lg bg-accent text-white ml-auto">{m.content}</div>
          ) : (
            <div key={i} className="text-sm max-w-[90%] px-3 py-2.5 rounded-lg bg-base text-text border border-border prose prose-invert prose-sm max-w-none prose-p:my-1.5 prose-ul:my-1.5 prose-ol:my-1.5 prose-li:my-0.5 prose-strong:text-text prose-headings:text-text prose-headings:my-1.5 prose-table:my-2 prose-th:px-2 prose-th:py-1 prose-td:px-2 prose-td:py-1 prose-th:border prose-td:border prose-th:border-border prose-td:border-border">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  table: ({ children }) => (
                    <div className="overflow-x-auto">
                      <table>{children}</table>
                    </div>
                  ),
                }}
              >
                {m.content}
              </ReactMarkdown>

              {m.action && (
                <div className="not-prose mt-3 rounded-md border border-accent2/40 bg-accent2/5 p-2.5 space-y-2">
                  {m.action.summaries.map((summary, j) => (
                    <div key={j} className="flex items-start gap-2 text-xs text-text">
                      <Zap size={12} className="text-accent2 mt-0.5 shrink-0" />
                      <span>{summary}</span>
                    </div>
                  ))}
                  {m.action.status === "pending" ? (
                    <div className="flex gap-2 pt-1">
                      <button
                        onClick={() => handleAction(i, true)}
                        disabled={sending}
                        className="flex-1 bg-gradient-to-br from-accent to-accent2 text-white text-xs rounded-md py-1.5 font-medium hover:opacity-90 active:scale-95 disabled:opacity-50 transition-all"
                      >
                        Confirm
                      </button>
                      <button
                        onClick={() => handleAction(i, false)}
                        disabled={sending}
                        className="flex-1 border border-border text-text-muted hover:text-text text-xs rounded-md py-1.5 transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <p className="text-[11px] text-text-muted">{STATUS_TEXT[m.action.status]}</p>
                  )}
                </div>
              )}
            </div>
          )
        )}
        {sending && (
          <div className="text-sm text-text-muted bg-base border border-border px-3 py-2 rounded-lg max-w-[85%] flex items-center gap-1.5">
            <span className="animate-pulse">✨</span> Kai's thinking…
          </div>
        )}
      </div>

      <form onSubmit={handleSend} className="border-t border-border p-3 flex gap-2">
        <input type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder={placeholder}
          className="flex-1 bg-base border border-border rounded-md px-3 py-2 text-text text-sm focus:outline-none focus:ring-2 focus:ring-accent" />
        <button type="submit" disabled={sending}
          className="bg-gradient-to-br from-accent to-accent2 text-white text-sm rounded-md px-3 py-2 font-medium hover:opacity-90 disabled:opacity-50 transition-opacity">
          Send
        </button>
      </form>
    </div>
  );
}