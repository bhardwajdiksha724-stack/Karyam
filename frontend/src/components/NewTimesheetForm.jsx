import { useState } from "react";

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

export default function NewTimesheetForm({ employees, tasks, onCreate, onCancel }) {
  const [employeeId, setEmployeeId] = useState(employees[0]?.id ?? "");
  const [taskId, setTaskId] = useState("");
  const [entryDate, setEntryDate] = useState(todayISO());
  const [hours, setHours] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await onCreate({
        employee_id: Number(employeeId),
        task_id: taskId ? Number(taskId) : null,
        entry_date: entryDate,
        hours: Number(hours),
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-surface border border-border rounded-lg p-5 mb-6 grid grid-cols-2 md:grid-cols-5 gap-3 items-end"
    >
      <div>
        <label className="block text-sm text-text-muted mb-1">Employee</label>
        <select
          value={employeeId}
          onChange={(e) => setEmployeeId(e.target.value)}
          className="w-full bg-base border border-border rounded-md px-3 py-2 text-text text-sm focus:outline-none focus:ring-2 focus:ring-accent"
        >
          {employees.map((emp) => (
            <option key={emp.id} value={emp.id}>{emp.name}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm text-text-muted mb-1">Task (optional)</label>
        <select
          value={taskId}
          onChange={(e) => setTaskId(e.target.value)}
          className="w-full bg-base border border-border rounded-md px-3 py-2 text-text text-sm focus:outline-none focus:ring-2 focus:ring-accent"
        >
          <option value="">None</option>
          {tasks.map((t) => (
            <option key={t.id} value={t.id}>{t.title}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm text-text-muted mb-1">Date</label>
        <input
          type="date"
          required
          value={entryDate}
          onChange={(e) => setEntryDate(e.target.value)}
          className="w-full bg-base border border-border rounded-md px-3 py-2 text-text text-sm focus:outline-none focus:ring-2 focus:ring-accent"
        />
      </div>

      <div>
        <label className="block text-sm text-text-muted mb-1">Hours</label>
        <input
          type="number"
          step="0.5"
          min="0"
          required
          value={hours}
          onChange={(e) => setHours(e.target.value)}
          className="w-full bg-base border border-border rounded-md px-3 py-2 text-text text-sm focus:outline-none focus:ring-2 focus:ring-accent"
        />
      </div>

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={submitting}
          className="bg-accent text-white text-sm rounded-md px-4 py-2 font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
        >
          {submitting ? "Logging…" : "Log"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="text-sm text-text-muted hover:text-text px-3 py-2"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}