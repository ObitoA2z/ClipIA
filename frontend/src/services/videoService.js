import api from "./api";

export async function processVideo(input) {
  const payload =
    typeof input === "string"
      ? { youtube_url: input }
      : {
          youtube_url: input?.youtube_url || "",
          clip_mode: input?.clip_mode || "talking",
          prompt: input?.prompt || null,
          max_clips: input?.max_clips ?? 8,
          min_duration: input?.min_duration ?? 30,
          max_duration: input?.max_duration ?? 90,
          target_platform: input?.target_platform || "all",
          layout: input?.layout || "centered",
        };

  const { data } = await api.post("/video/process", payload);
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

export async function downloadAllClips(videoId) {
  const response = await api.get(`/clips/${videoId}/download-all`, { responseType: "blob" });
  return response.data;
}

export async function deleteVideo(videoId) {
  const { data } = await api.delete(`/video/${videoId}`);
  return data;
}

export async function recutClip(clipId, { start, end }) {
  const { data } = await api.post(`/clips/${clipId}/recut`, { start, end });
  return data;
}

export async function getPipelineStats() {
  const { data } = await api.get("/stats/pipeline");
  return data;
}
