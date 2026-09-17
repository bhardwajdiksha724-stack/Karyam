import { useState } from "react";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function AccountPage() {
  const { employee, isManager, refreshEmployee } = useAuth();

  const [name, setName] = useState(employee?.name || "");
  const [role, setRole] = useState(employee?.role || "");
  const [team, setTeam] = useState(employee?.team || "");
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMessage, setProfileMessage] = useState("");
  const [profileError, setProfileError] = useState("");

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState("");
  const [passwordError, setPasswordError] = useState("");

  async function handleProfileSubmit(e) {
    e.preventDefault();
    setProfileMessage("");
    setProfileError("");
    setProfileSaving(true);
    try {
      await client.patch("/auth/me", { name, role, team });
      await refreshEmployee();
      setProfileMessage("Profile updated.");
    } catch (err) {
      setProfileError(err?.response?.data?.detail || "Something went wrong.");
    } finally {
      setProfileSaving(false);
    }
  }

  async function handlePasswordSubmit(e) {
    e.preventDefault();
    setPasswordMessage("");
    setPasswordError("");

    if (newPassword !== confirmPassword) {
      setPasswordError("New passwords don't match.");
      return;
    }

    setPasswordSaving(true);
    try {
      await client.post("/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPasswordMessage("Password changed.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setPasswordError(err?.response?.data?.detail || "Something went wrong.");
    } finally {
      setPasswordSaving(false);
    }
  }

  return (
    <div className="max-w-lg">
      <h2 className="font-display text-2xl font-bold text-text mb-6">Account</h2>

      <div className="bg-surface border border-border rounded-lg p-5 mb-6">
        <h3 className="text-text font-medium mb-1">Profile</h3>
        <p className="text-xs text-text-muted mb-4">
          {employee?.email} · {isManager ? "Manager" : "Employee"} account
        </p>
        <form onSubmit={handleProfileSubmit} className="space-y-3">
          <div>
            <label className="block text-sm text-text-muted mb-1">Name</label>
            <input
              type="text" value={name} onChange={(e) => setName(e.target.value)}
              className="w-full bg-base border border-border rounded-md px-3 py-2 text-text text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          <div>
            <label className="block text-sm text-text-muted mb-1">Job title</label>
            <input
              type="text" value={role} onChange={(e) => setRole(e.target.value)}
              className="w-full bg-base border border-border rounded-md px-3 py-2 text-text text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          <div>
            <label className="block text-sm text-text-muted mb-1">Team</label>
            <input
              type="text" value={team} onChange={(e) => setTeam(e.target.value)}
              className="w-full bg-base border border-border rounded-md px-3 py-2 text-text text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          {profileError && <p className="text-sm text-status-high">{profileError}</p>}
          {profileMessage && <p className="text-sm text-status-done">{profileMessage}</p>}
          <button
            type="submit" disabled={profileSaving}
            className="bg-accent text-white text-sm rounded-md px-4 py-2 font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
          >
            {profileSaving ? "Saving…" : "Save changes"}
          </button>
        </form>
      </div>

      <div className="bg-surface border border-border rounded-lg p-5">
        <h3 className="text-text font-medium mb-1">Change password</h3>
        <p className="text-xs text-text-muted mb-4">
          Requires your current password to confirm it's really you.
        </p>
        <form onSubmit={handlePasswordSubmit} className="space-y-3">
          <div>
            <label className="block text-sm text-text-muted mb-1">Current password</label>
            <input
              type="password" required value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)}
              className="w-full bg-base border border-border rounded-md px-3 py-2 text-text text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          <div>
            <label className="block text-sm text-text-muted mb-1">New password</label>
            <input
              type="password" required minLength={6} value={newPassword} onChange={(e) => setNewPassword(e.target.value)}
              className="w-full bg-base border border-border rounded-md px-3 py-2 text-text text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          <div>
            <label className="block text-sm text-text-muted mb-1">Confirm new password</label>
            <input
              type="password" required value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full bg-base border border-border rounded-md px-3 py-2 text-text text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          {passwordError && <p className="text-sm text-status-high">{passwordError}</p>}
          {passwordMessage && <p className="text-sm text-status-done">{passwordMessage}</p>}
          <button
            type="submit" disabled={passwordSaving}
            className="bg-accent text-white text-sm rounded-md px-4 py-2 font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
          >
            {passwordSaving ? "Saving…" : "Change password"}
          </button>
        </form>
      </div>
    </div>
  );
}