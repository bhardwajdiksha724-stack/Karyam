const priorityStyles = {
  low: "text-text-muted border-border",
  medium: "text-accent border-accent/40",
  high: "text-status-high border-status-high/40",
};

export default function TaskCard({ task, onStatusChange, onDelete }) {
  return (
    <div className="bg-surface border border-border rounded-lg p-4 space-y-3">
      <div className="flex items-start justify-between gap-2">
        <p className="text-text text-sm font-medium">{task.title}</p>
        <span
          className={`shrink-0 text-[11px] px-2 py-0.5 rounded-full border ${priorityStyles[task.priority]}`}
        >
          {task.priority}
        </span>
      </div>

      {task.description && (
        <p className="text-text-muted text-xs line-clamp-2">{task.description}</p>
      )}

      <div className="flex items-center justify-between text-xs text-text-muted">
        <span>{task.assignee_name || "Unassigned"}</span>
        {task.due_date && <span>{task.due_date}</span>}
      </div>

      <div className="flex items-center gap-2 pt-1">
        <select
          value={task.status}
          onChange={(e) => onStatusChange(task.id, e.target.value)}
          className="flex-1 bg-base border border-border rounded-md text-xs text-text px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-accent"
        >
          <option value="todo">To Do</option>
          <option value="in_progress">In Progress</option>
          <option value="done">Done</option>
        </select>
        <button
          onClick={() => onDelete(task.id)}
          className="text-xs text-text-muted hover:text-status-high px-2 py-1.5"
          title="Delete task"
        >
          ✕
        </button>
      </div>
    </div>
  );
}