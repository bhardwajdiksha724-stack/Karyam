import { createContext, useContext, useEffect, useState } from "react";
import client from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [employee, setEmployee] = useState(null);
  const [loading, setLoading] = useState(true);

  // On first load, if we already have a saved token, try to fetch the
  // logged-in employee so a page refresh doesn't kick you back to login.
  useEffect(() => {
    const token = localStorage.getItem("karyam_token");
    if (!token) {
      setLoading(false);
      return;
    }
    client
      .get("/auth/me")
      .then((res) => setEmployee(res.data))
      .catch(() => localStorage.removeItem("karyam_token"))
      .finally(() => setLoading(false));
  }, []);

  async function login(email, password) {
    const res = await client.post("/auth/login", { email, password });
    localStorage.setItem("karyam_token", res.data.access_token);
    const me = await client.get("/auth/me");
    setEmployee(me.data);
  }

  function logout() {
    localStorage.removeItem("karyam_token");
    setEmployee(null);
  }

  return (
    <AuthContext.Provider value={{ employee, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}