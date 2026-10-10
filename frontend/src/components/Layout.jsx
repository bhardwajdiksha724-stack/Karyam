import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import ChatWidget from "./ChatWidget";

export default function Layout() {
  // When Kai changes data (creates a task, logs hours...), bumping this key
  // remounts the current page so it refetches and shows the change instantly.
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-8">
        <div key={refreshKey}>
          <Outlet />
        </div>
      </main>
      <ChatWidget endpoint="/chat" onDataChanged={() => setRefreshKey((k) => k + 1)} />
    </div>
  );
}