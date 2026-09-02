import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const navItems = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/tasks", label: "Tasks" },
  { to: "/timesheets", label: "Timesheets" },
];

export default function Sidebar() {
  const { employee, logout } = useAuth();

  return (
    <aside className="w-60 shrink-0 h-screen sticky top-0 bg-surface border-r border-border flex flex-col">
      <div className="px-5 py-5">
        <h1 className="font-display text-xl font-bold text-text">Karyam</h1>
      </div>

      <nav className="flex-1 px-3 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `block px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive
                  ? "bg-accent/15 text-accent"
                  : "text-text-muted hover:text-text hover:bg-base"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="px-3 py-4 border-t border-border">
        <div className="px-3 mb-2">
          <p className="text-sm text-text font-medium truncate">{employee?.name}</p>
          <p className="text-xs text-text-muted truncate">{employee?.role}</p>
        </div>
        <button
          onClick={logout}
          className="w-full text-left px-3 py-2 rounded-md text-sm text-text-muted hover:text-text hover:bg-base transition-colors"
        >
          Log out
        </button>
      </div>
    </aside>
  );
}