import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children }) {
  const { employee, loading } = useAuth();

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-text-muted">Loading…</div>;
  }

  if (!employee) {
    return <Navigate to="/login" replace />;
  }

  return children;
}