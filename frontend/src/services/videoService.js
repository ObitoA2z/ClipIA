import api from "./api";

export async function processVideo(youtubeUrl) {
  const { data } = await api.post("/video/process", { youtube_url: youtubeUrl });
  return data;
}

export async function listVideos() {
  const { data } = await api.get("/video/list");
  return data;
}

export async function getVideo(videoId) {
  const { data } = await api.get(`/video/${videoId}`);
  return data;
}

export async function getVideoStatus(videoId) {
  const { data } = await api.get(`/video/${videoId}/status`);
  return data;
}

export async function getVideoClips(videoId) {
  const { data } = await api.get(`/clips/${videoId}`);
  return data;
}

export async function deleteVideo(videoId) {
  const { data } = await api.delete(`/video/${videoId}`);
  return data;
}

export async function recutClip(clipId, { start, end }) {
  const { data } = await api.post(`/clips/${clipId}/recut`, { start, end });
  return data;
}
