import axios from "axios";

export const api = axios.create({
  baseURL: "https://clipai.vercel.app/api",
  timeout: 15000
});

export function setAuthToken(token: string | null) {
  if (!token) {
    delete api.defaults.headers.common.Authorization;
    return;
  }
  api.defaults.headers.common.Authorization = `Bearer ${token}`;
}
