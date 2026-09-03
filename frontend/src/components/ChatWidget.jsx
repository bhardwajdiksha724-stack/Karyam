import { useState } from "react";
import ReactMarkdown from "react-markdown";
import client from "../api/client";

export default function ChatWidget({
  endpoint = "/chat",
  greeting = "Hi! Ask me about your team's tasks or timesheets.",
  placeholder = "Ask about tasks, workload…",
  label = "Karyam Assistant",
}) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([{ role: "assistant", content: greeting }]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  async function handleSend(e) {
    e.preventDefault();
    if (!input.trim() || sending) return;

    const question = input.trim();
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setInput("");
    setSending(true);

    try {
      const res = await client.post(endpoint, { message: question });
      setMessages((prev) => [...prev, { role: "assistant", content: res.data.reply }]);
    } catch (err) {
      const detail = err?.response?.data?.detail || "Something went wrong. Try again.";
      setMessages((prev) => [...prev, { role: "assistant", content: detail }]);
    } finally {
      setSending(false);
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 bg-accent text-white rounded-full w-14 h-14 flex items-center justify-center shadow-lg hover:opacity-90 transition-opacity"
        title={label}
      >
        💬
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 w-96 h-[32rem] bg-surface border border-border rounded-lg shadow-xl flex flex-col overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <span className="text-sm font-medium text-text">{label}</span>
        <button
          onClick={() => setOpen(false)}
          className="text-text-muted hover:text-text text-sm"
        >
          ✕
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {messages.map((m, i) =>
          m.role === "user" ? (
            <div
              key={i}
              className="text-sm max-w-[85%] px-3 py-2 rounded-lg bg-accent text-white ml-auto"
            >
              {m.content}
            </div>
          ) : (
            <div
              key={i}
              className="text-sm max-w-[90%] px-3 py-2.5 rounded-lg bg-base text-text border border-border
                         prose prose-invert prose-sm max-w-none
                         prose-p:my-1.5 prose-ul:my-1.5 prose-ol:my-1.5 prose-li:my-0.5
                         prose-strong:text-text prose-headings:text-text prose-headings:my-1.5"
            >
              <ReactMarkdown>{m.content}</ReactMarkdown>
            </div>
          )
        )}
        {sending && (
          <div className="text-sm text-text-muted bg-base border border-border px-3 py-2 rounded-lg max-w-[85%]">
            Thinking…
          </div>
        )}
      </div>

      <form onSubmit={handleSend} className="border-t border-border p-3 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={placeholder}
          className="flex-1 bg-base border border-border rounded-md px-3 py-2 text-text text-sm focus:outline-none focus:ring-2 focus:ring-accent"
        />
        <button
          type="submit"
          disabled={sending}
          className="bg-accent text-white text-sm rounded-md px-3 py-2 font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
        >
          Send
        </button>
      </form>
    </div>
  );
}