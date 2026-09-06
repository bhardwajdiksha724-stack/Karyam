import axios from "axios";

// In production (deployed), set VITE_API_URL to your deployed backend's URL.
// Locally, it falls back to your local backend automatically.
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const client = axios.create({
  baseURL: API_BASE_URL,
});

// Runs before every request — if we have a saved token, attach it automatically
// so every page doesn't need to remember to do this itself.
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("karyam_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default client;