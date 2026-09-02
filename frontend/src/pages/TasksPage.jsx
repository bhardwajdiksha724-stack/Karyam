import { useEffect, useState } from "react";
import client from "../api/client";
import TaskCard from "../components/TaskCard";
import NewTaskForm from "../components/NewTaskForm";

const columns = [
  { key: "todo", label: "To Do", dot: "bg-status-todo" },
  { key: "in_progress", label: "In Progress", dot: "bg-status-progress" },
  { key: "done", label: "Done", dot: "bg-status-done" },
];

export default function TasksPage() {
  const [tasks, setTasks] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  function loadData() {
    setLoading(true);
    return Promise.all([client.get("/tasks"), client.get("/employees")])
      .then(([taskRes, empRes]) => {
        setTasks(taskRes.data);
        setEmployees(empRes.data);
      })
      .finally(() => setLoading(false));
  }

  async function handleCreate(data) {
    await client.post("/tasks", data);
    setShowForm(false);
    await loadData();
  }

  async function handleStatusChange(taskId, status) {
    // Update locally right away so the card jumps columns instantly,
    // then confirm with the backend.
    setTasks((prev) => prev.map((t) => (t.id === taskId ? { ...t, status } : t)));
    await client.patch(`/tasks/${taskId}`, { status });
  }

  async function handleDelete(taskId) {
    setTasks((prev) => prev.filter((t) => t.id !== taskId));
    await client.delete(`/tasks/${taskId}`);
  }

  if (loading) {
    return <p className="text-text-muted">Loading tasks…</p>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="font-display text-2xl font-bold text-text">Tasks</h2>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="bg-accent text-white text-sm rounded-md px-4 py-2 font-medium hover:opacity-90 transition-opacity"
        >
          {showForm ? "Close" : "+ New task"}
        </button>
      </div>

      {showForm && (
        <NewTaskForm
          employees={employees}
          onCreate={handleCreate}
          onCancel={() => setShowForm(false)}
        />
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {columns.map((col) => {
          const colTasks = tasks.filter((t) => t.status === col.key);
          return (
            <div key={col.key}>
              <div className="flex items-center gap-2 mb-3">
                <span className={`w-2 h-2 rounded-full ${col.dot}`} />
                <h3 className="text-sm font-medium text-text">{col.label}</h3>
                <span className="text-xs text-text-muted">{colTasks.length}</span>
              </div>

              <div className="space-y-3">
                {colTasks.length === 0 ? (
                  <p className="text-xs text-text-muted">No tasks here.</p>
                ) : (
                  colTasks.map((task) => (
                    <TaskCard
                      key={task.id}
                      task={task}
                      onStatusChange={handleStatusChange}
                      onDelete={handleDelete}
                    />
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}