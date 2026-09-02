import { useAuth } from "../context/AuthContext";

export default function Dashboard() {
  const { employee, logout } = useAuth();

  return (
    <div className="min-h-screen p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-display text-2xl font-bold text-text">Karyam</h1>
        <button
          onClick={logout}
          className="text-sm text-text-muted hover:text-text border border-border rounded-md px-3 py-1.5"
        >
          Log out
        </button>
      </div>

      <div className="bg-surface border border-border rounded-lg p-6">
        <p className="text-text-muted text-sm">Signed in as</p>
        <p className="text-text text-lg font-medium">{employee?.name}</p>
        <p className="text-text-muted text-sm mt-1">{employee?.email} · {employee?.role}</p>
      </div>

      <p className="text-text-muted text-sm mt-6">
        This is a placeholder — the real dashboard (task board, timesheets, charts) is next.
      </p>
    </div>
  );
}