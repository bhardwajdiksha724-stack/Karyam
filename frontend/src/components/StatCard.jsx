export default function StatCard({ label, value, icon: Icon, accentColor = "text-text", iconBg = "bg-base" }) {
  return (
    <div className="bg-surface border border-border rounded-lg p-5 transition-transform hover:-translate-y-0.5 hover:shadow-lg">
      <div className="flex items-center gap-3 mb-2">
        {Icon && (
          <div className={`w-8 h-8 rounded-lg ${iconBg} flex items-center justify-center`}>
            <Icon size={16} className={accentColor} />
          </div>
        )}
        <p className="text-sm text-text-muted">{label}</p>
      </div>
      <p className={`text-2xl font-display font-bold ${accentColor}`}>{value}</p>
    </div>
  );
}