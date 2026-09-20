import { useEffect, useState } from "react";
import { ListTodo, CheckCircle2, Clock, Users, Inbox } from "lucide-react";
import client from "../api/client";
import StatCard from "../components/StatCard";
import Avatar from "../components/Avatar";

export default function DashboardHome() {
  const [employees, setEmployees] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [timesheets, setTimesheets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([client.get("/employees"), client.get("/tasks"), client.get("/timesheets")])
      .then(([empRes, taskRes, tsRes]) => {
        setEmployees(empRes.data);
        setTasks(taskRes.data);
        setTimesheets(tsRes.data);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-text-muted">Loading dashboard…</p>;

  const doneCount = tasks.filter((t) => t.status === "done").length;
  const totalHours = timesheets.reduce((sum, t) => sum + t.hours, 0);

  function workloadFor(employeeId) {
    return tasks.filter((t) => t.assignee_id === employeeId && t.status !== "done").length;
  }

  return (
    <div>
      <h2 className="font-display text-2xl font-bold text-text mb-6">Dashboard</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total tasks" value={tasks.length} icon={ListTodo} accentColor="text-accent" iconBg="bg-accent/10" />
        <StatCard label="Completed" value={doneCount} icon={CheckCircle2} accentColor="text-status-done" iconBg="bg-status-done/10" />
        <StatCard label="Hours logged" value={totalHours} icon={Clock} accentColor="text-status-progress" iconBg="bg-status-progress/10" />
        <StatCard label="Team members" value={employees.length} icon={Users} accentColor="text-accent2" iconBg="bg-accent2/10" />
      </div>
      <div className="bg-surface border border-border rounded-lg">
        <div className="px-5 py-4 border-b border-border"><h3 className="text-text font-medium">Team</h3></div>
        {employees.length === 0 ? (
          <div className="px-5 py-10 flex flex-col items-center gap-2 text-text-muted">
            <Inbox size={28} />
            <p className="text-sm">No team members yet.</p>
          </div>
        ) : (
          <ul className="divide-y divide-border">
            {employees.map((emp) => (
              <li key={emp.id} className="px-5 py-3 flex items-center justify-between hover:bg-base/50 transition-colors">
                <div className="flex items-center gap-3">
                  <Avatar name={emp.name} />
                  <div>
                    <p className="text-text text-sm font-medium">{emp.name}</p>
                    <p className="text-text-muted text-xs">{emp.role} · {emp.team}</p>
                  </div>
                </div>
                <span className="text-xs text-text-muted bg-base border border-border rounded-full px-3 py-1">
                  {workloadFor(emp.id)} open task{workloadFor(emp.id) === 1 ? "" : "s"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}