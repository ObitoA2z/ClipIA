import AsyncStorage from "@react-native-async-storage/async-storage";
import axios from "axios";

const BASE_URL = process.env.EXPO_PUBLIC_API_URL || "https://ton-backend.railway.app";
const ACCESS_TOKEN_KEY = "clipai_mobile_access_token";
const REFRESH_TOKEN_KEY = "clipai_mobile_refresh_token";

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 20000,
});

async function getAccessToken() {
  return AsyncStorage.getItem(ACCESS_TOKEN_KEY);
}

async function authHeaders() {
  const token = await getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function setAuthTokens(accessToken: string, refreshToken: string) {
  await AsyncStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  await AsyncStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export async function clearAuthTokens() {
  await AsyncStorage.removeItem(ACCESS_TOKEN_KEY);
  await AsyncStorage.removeItem(REFRESH_TOKEN_KEY);
}

export async function login(email: string, password: string) {
  const { data } = await api.post("/auth/login", { email, password });
  await setAuthTokens(data.access_token, data.refresh_token);
  return data;
}

export async function register(email: string, password: string, fullName: string) {
  const { data } = await api.post("/auth/register", { email, password, full_name: fullName });
  await setAuthTokens(data.access_token, data.refresh_token);
  return data;
}

export async function me() {
  const headers = await authHeaders();
  const { data } = await api.get("/auth/me", { headers });
  return data;
}

export async function getVideos() {
  const headers = await authHeaders();
  const { data } = await api.get("/video/list", { headers });
  return data;
}

export async function processVideo(url: string) {
  const headers = await authHeaders();
  const { data } = await api.post(
    "/video/process",
    { youtube_url: url },
    { headers },
  );
  return data;
}

export async function getVideoStatus(videoId: string) {
  const headers = await authHeaders();
  const { data } = await api.get(`/video/${videoId}/status`, { headers });
  return data;
}

export async function getClips(videoId: string) {
  const headers = await authHeaders();
  const { data } = await api.get(`/clips/${videoId}`, { headers });
  return data;
}
