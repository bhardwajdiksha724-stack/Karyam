const COLORS = ["bg-accent", "bg-accent2", "bg-status-progress", "bg-status-done", "bg-status-high"];

function colorForName(name) {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
  return COLORS[Math.abs(hash) % COLORS.length];
}

function initials(name) {
  if (!name) return "?";
  return name.trim().split(/\s+/).map((p) => p[0]).slice(0, 2).join("").toUpperCase();
}

export default function Avatar({ name, size = "w-8 h-8", textSize = "text-xs" }) {
  return (
    <div
      className={`${size} ${colorForName(name || "?")} rounded-full flex items-center justify-center text-white ${textSize} font-medium shrink-0`}
    >
      {initials(name)}
    </div>
  );
}