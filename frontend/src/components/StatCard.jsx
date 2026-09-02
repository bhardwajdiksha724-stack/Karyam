export default function StatCard({ label, value, accent = false }) {
  return (
    <div className="bg-surface border border-border rounded-lg p-5">
      <p className="text-sm text-text-muted">{label}</p>
      <p className={`mt-1 text-2xl font-display font-bold ${accent ? "text-accent" : "text-text"}`}>
        {value}
      </p>
    </div>
  );
}