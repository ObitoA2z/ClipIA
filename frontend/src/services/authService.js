import api from "./api";

export async function registerUser(payload) {
  const { data } = await api.post("/auth/register", payload);
  return data;
}

export async function loginUser(payload) {
  const { data } = await api.post("/auth/login", payload);
  return data;
}

export async function refreshAccessToken(refreshToken) {
  const { data } = await api.post("/auth/refresh", { refresh_token: refreshToken });
  return data;
}

export async function meUser(token) {
  const { data } = await api.get("/auth/me", {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  return data;
}

export async function logoutUser(token) {
  const { data } = await api.post(
    "/auth/logout",
    {},
    { headers: token ? { Authorization: `Bearer ${token}` } : undefined }
  );
  return data;
}

export async function forgotPassword(email) {
  const { data } = await api.post("/auth/forgot-password", { email });
  return data;
}

export async function resetPassword(token, newPassword) {
  const { data } = await api.post("/auth/reset-password", { token, new_password: newPassword });
  return data;
}

export async function updateProfile(payload) {
  const { data } = await api.put("/auth/me", payload);
  return data;
}

export async function changePassword(payload) {
  const { data } = await api.post("/auth/change-password", payload);
  return data;
}

export async function getPreferences() {
  const { data } = await api.get("/auth/preferences");
  return data;
}

export async function updatePreferences(payload) {
  const { data } = await api.put("/auth/preferences", payload);
  return data;
}

export async function listSessions() {
  const { data } = await api.get("/auth/sessions");
  return data;
}

export async function revokeSession(sessionId) {
  const { data } = await api.delete(`/auth/sessions/${sessionId}`);
  return data;
}

export async function setupTwoFactor() {
  const { data } = await api.get("/auth/2fa/setup");
  return data;
}

export async function enableTwoFactor(code) {
  const { data } = await api.post("/auth/2fa/enable", { code });
  return data;
}

export async function disableTwoFactor(code) {
  const { data } = await api.post("/auth/2fa/disable", { code });
  return data;
}
