import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import ChatWidget from "./ChatWidget";

export default function Layout() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-8">
        <Outlet />
      </main>
      <ChatWidget
        endpoint="/chat"
        greeting="Hi! Ask me about your team's tasks or timesheets."
        placeholder="Ask about tasks, workload…"
        label="Karyam Assistant"
      />
    </div>
  );
}