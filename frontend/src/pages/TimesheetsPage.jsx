import { useEffect, useState } from "react";
import client from "../api/client";
import NewTimesheetForm from "../components/NewTimesheetForm";

function toISO(date) {
  return date.toISOString().slice(0, 10);
}

function mondayOf(date) {
  const d = new Date(date);
  const day = d.getDay(); // 0 = Sunday, 1 = Monday, ...
  const diff = day === 0 ? -6 : 1 - day;
  d.setDate(d.getDate() + diff);
  return d;
}

function formatRange(monday, sunday) {
  const opts = { month: "short", day: "numeric" };
  return `${monday.toLocaleDateString(undefined, opts)} – ${sunday.toLocaleDateString(undefined, opts)}`;
}

export default function TimesheetsPage() {
  const [weekStart, setWeekStart] = useState(() => mondayOf(new Date()));
  const [entries, setEntries] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  const weekEnd = new Date(weekStart);
  weekEnd.setDate(weekStart.getDate() + 6);

  useEffect(() => {
    loadData();
  }, [weekStart]);

  function loadData() {
    setLoading(true);
    return Promise.all([
      client.get("/timesheets", {
        params: { start_date: toISO(weekStart), end_date: toISO(weekEnd) },
      }),
      client.get("/employees"),
      client.get("/tasks"),
    ])
      .then(([tsRes, empRes, taskRes]) => {
        setEntries(tsRes.data);
        setEmployees(empRes.data);
        setTasks(taskRes.data);
      })
      .finally(() => setLoading(false));
  }

  async function handleCreate(data) {
    await client.post("/timesheets", data);
    setShowForm(false);
    await loadData();
  }

  async function handleToggleApprove(entry) {
    setEntries((prev) =>
      prev.map((e) => (e.id === entry.id ? { ...e, approved: !e.approved } : e))
    );
    await client.patch(`/timesheets/${entry.id}`, { approved: !entry.approved });
  }

  async function handleDelete(entryId) {
    setEntries((prev) => prev.filter((e) => e.id !== entryId));
    await client.delete(`/timesheets/${entryId}`);
  }

  function shiftWeek(days) {
    const next = new Date(weekStart);
    next.setDate(next.getDate() + days);
    setWeekStart(next);
  }

  const totalHours = entries.reduce((sum, e) => sum + e.hours, 0);

  if (loading && entries.length === 0) {
    return <p className="text-text-muted">Loading timesheets…</p>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="font-display text-2xl font-bold text-text">Timesheets</h2>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="bg-accent text-white text-sm rounded-md px-4 py-2 font-medium hover:opacity-90 transition-opacity"
        >
          {showForm ? "Close" : "+ Log hours"}
        </button>
      </div>

      {showForm && (
        <NewTimesheetForm
          employees={employees}
          tasks={tasks}
          onCreate={handleCreate}
          onCancel={() => setShowForm(false)}
        />
      )}

      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => shiftWeek(-7)}
            className="text-sm text-text-muted hover:text-text border border-border rounded-md px-3 py-1.5"
          >
            ← Prev
          </button>
          <span className="text-sm text-text">{formatRange(weekStart, weekEnd)}</span>
          <button
            onClick={() => shiftWeek(7)}
            className="text-sm text-text-muted hover:text-text border border-border rounded-md px-3 py-1.5"
          >
            Next →
          </button>
        </div>
        <span className="text-sm text-text-muted">Total: {totalHours} hrs</span>
      </div>

      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        {entries.length === 0 ? (
          <p className="px-5 py-6 text-sm text-text-muted">No entries logged this week.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-text-muted border-b border-border">
                <th className="px-5 py-3 font-medium">Date</th>
                <th className="px-5 py-3 font-medium">Employee</th>
                <th className="px-5 py-3 font-medium">Task</th>
                <th className="px-5 py-3 font-medium">Hours</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {entries.map((entry) => (
                <tr key={entry.id}>
                  <td className="px-5 py-3 text-text">{entry.entry_date}</td>
                  <td className="px-5 py-3 text-text">{entry.employee_name}</td>
                  <td className="px-5 py-3 text-text-muted">{entry.task_title || "—"}</td>
                  <td className="px-5 py-3 text-text">{entry.hours}</td>
                  <td className="px-5 py-3">
                    <button
                      onClick={() => handleToggleApprove(entry)}
                      className={`text-xs px-2 py-1 rounded-full border ${
                        entry.approved
                          ? "text-status-done border-status-done/40"
                          : "text-text-muted border-border"
                      }`}
                    >
                      {entry.approved ? "Approved" : "Pending"}
                    </button>
                  </td>
                  <td className="px-5 py-3 text-right">
                    <button
                      onClick={() => handleDelete(entry.id)}
                      className="text-xs text-text-muted hover:text-status-high"
                    >
                      ✕
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}