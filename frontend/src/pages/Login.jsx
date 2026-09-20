import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ListChecks, Clock, Sparkles } from "lucide-react";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";
import ChatWidget from "../components/ChatWidget";
import PasswordInput from "../components/PasswordInput";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

const FEATURES = [
  { icon: ListChecks, text: "A Kanban board your whole team actually uses" },
  { icon: Clock, text: "Timesheets with a real manager approval flow" },
  { icon: Sparkles, text: "Kai, an AI assistant grounded in your real data" },
];

export default function Login() {
  const [mode, setMode] = useState("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [accessRole, setAccessRole] = useState("employee");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const { login, loginWithGoogle } = useAuth();
  const navigate = useNavigate();
  const googleButtonRef = useRef(null);

  async function handleGoogleCredential(response) {
    setError("");
    try {
      await loginWithGoogle(response.credential);
      navigate("/");
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Google sign-in failed. Try again.");
    }
  }

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID || !window.google || !googleButtonRef.current) return;

    window.google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: handleGoogleCredential,
    });
    window.google.accounts.id.renderButton(googleButtonRef.current, {
      theme: "filled_black",
      shape: "pill",
      size: "large",
      width: 320,
    });
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      if (mode === "signup") {
        await client.post("/auth/signup", { name, email, password, access_role: accessRole });
      }
      await login(email, password);
      navigate("/");
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Something went wrong. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* Left: form */}
      <div className="flex-1 flex items-center justify-center px-4 py-10">
        <div className="w-full max-w-sm">
          <div className="mb-8 text-center">
            <h1 className="font-display text-3xl font-bold text-text">Karyam</h1>
            <p className="mt-1 text-sm text-text-muted">
              {mode === "login" ? "Sign in to your dashboard" : "Create your account"}
            </p>
          </div>

          {GOOGLE_CLIENT_ID && (
            <div className="mb-4 flex flex-col items-center gap-3">
              <div ref={googleButtonRef} />
              <div className="w-full flex items-center gap-3">
                <div className="flex-1 h-px bg-border" />
                <span className="text-xs text-text-muted">or</span>
                <div className="flex-1 h-px bg-border" />
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="bg-surface border border-border rounded-lg p-6 space-y-4">
            {mode === "signup" && (
              <>
                <div>
                  <label className="block text-sm text-text-muted mb-1">Name</label>
                  <input
                    type="text" required value={name} onChange={(e) => setName(e.target.value)}
                    className="w-full bg-base border border-border rounded-md px-3 py-2 text-text focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                </div>
                <div>
                  <label className="block text-sm text-text-muted mb-1">I am a...</label>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setAccessRole("employee")}
                      className={`flex-1 rounded-md py-2 text-sm border transition-colors ${
                        accessRole === "employee" ? "bg-accent text-white border-accent" : "border-border text-text-muted"
                      }`}
                    >
                      Employee
                    </button>
                    <button
                      type="button"
                      onClick={() => setAccessRole("manager")}
                      className={`flex-1 rounded-md py-2 text-sm border transition-colors ${
                        accessRole === "manager" ? "bg-accent text-white border-accent" : "border-border text-text-muted"
                      }`}
                    >
                      Manager
                    </button>
                  </div>
                  <p className="mt-1 text-xs text-text-muted">
                    Managers can create/delete tasks and approve timesheets. Employees can update their own tasks and log their own hours.
                  </p>
                </div>
              </>
            )}

            <div>
              <label className="block text-sm text-text-muted mb-1">Email</label>
              <input
                type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-base border border-border rounded-md px-3 py-2 text-text focus:outline-none focus:ring-2 focus:ring-accent"
              />
            </div>

            <div>
              <label className="block text-sm text-text-muted mb-1">Password</label>
              <PasswordInput required value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>

            {error && <p className="text-sm text-status-high">{error}</p>}

            <button
              type="submit" disabled={submitting}
              className="w-full bg-accent text-white rounded-md py-2 font-medium hover:opacity-90 active:scale-[0.98] disabled:opacity-50 transition-all"
            >
              {submitting ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
            </button>
          </form>

          <p className="mt-4 text-center text-sm text-text-muted">
            {mode === "login" ? (
              <>New here? <button className="text-accent hover:underline" onClick={() => setMode("signup")}>Create an account</button></>
            ) : (
              <>Already have an account? <button className="text-accent hover:underline" onClick={() => setMode("login")}>Sign in</button></>
            )}
          </p>
        </div>
      </div>

      {/* Right: gradient hero, hidden on small screens */}
      <div className="hidden lg:flex flex-1 relative overflow-hidden items-center justify-center bg-gradient-to-br from-accent to-accent2 p-12">
        <div className="absolute w-96 h-96 rounded-full bg-white/10 blur-3xl -top-20 -right-20" />
        <div className="absolute w-72 h-72 rounded-full bg-white/10 blur-3xl bottom-0 left-0" />
        <div className="relative max-w-md">
          <h2 className="font-display text-4xl font-bold text-white mb-4 leading-tight">
            Where your team's work actually lives.
          </h2>
          <p className="text-white/80 mb-8">
            Tasks, timesheets, and an AI assistant that knows what's really going on — no more digging through spreadsheets.
          </p>
          <div className="space-y-4">
            {FEATURES.map(({ icon: Icon, text }) => (
              <div key={text} className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-white/15 flex items-center justify-center shrink-0">
                  <Icon size={18} className="text-white" />
                </div>
                <p className="text-white/90 text-sm">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <ChatWidget
        endpoint="/chat/public"
        greeting="heyy 👋 I'm Kai! Ask me what Karyam does, how it works, or what it costs — no sign up needed."
        placeholder="Ask Kai about Karyam…"
        label="Kai"
      />
    </div>
  );
}