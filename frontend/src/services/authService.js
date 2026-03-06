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
