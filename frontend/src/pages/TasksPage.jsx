import { useEffect, useState } from "react";
import { Inbox } from "lucide-react";
import client from "../api/client";
import TaskCard from "../components/TaskCard";
import NewTaskForm from "../components/NewTaskForm";
import { useAuth } from "../context/AuthContext";
import { celebrate } from "../utils/celebrate";

const columns = [
  { key: "todo", label: "To Do", dot: "bg-status-todo" },
  { key: "in_progress", label: "In Progress", dot: "bg-status-progress" },
  { key: "done", label: "Done", dot: "bg-status-done" },
];

export default function TasksPage() {
  const { isManager, employee } = useAuth();
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
    setTasks((prev) => prev.map((t) => (t.id === taskId ? { ...t, status } : t)));
    await client.patch(`/tasks/${taskId}`, { status });
    if (status === "done") celebrate();
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
        {isManager && (
          <button
            onClick={() => setShowForm((v) => !v)}
            className="bg-accent text-white text-sm rounded-md px-4 py-2 font-medium hover:opacity-90 active:scale-95 transition-all"
          >
            {showForm ? "Close" : "+ New task"}
          </button>
        )}
      </div>

      {!isManager && (
        <p className="text-xs text-text-muted mb-4">
          You can update the status of tasks assigned to you. Creating, reassigning, and deleting tasks requires manager access.
        </p>
      )}

      {showForm && isManager && (
        <NewTaskForm employees={employees} onCreate={handleCreate} onCancel={() => setShowForm(false)} />
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
                  <div className="flex flex-col items-center gap-1.5 py-6 text-text-muted border border-dashed border-border rounded-lg">
                    <Inbox size={20} />
                    <p className="text-xs">No tasks here.</p>
                  </div>
                ) : (
                  colTasks.map((task) => (
                    <TaskCard
                      key={task.id}
                      task={task}
                      onStatusChange={handleStatusChange}
                      onDelete={handleDelete}
                      isManager={isManager}
                      currentEmployeeId={employee?.id}
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