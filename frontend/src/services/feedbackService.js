import api from "./api";

export async function submitFeedback(payload) {
  const { data } = await api.post("/feedback", payload);
  return data;
}

export async function listFeatureRequests() {
  const { data } = await api.get("/feedback/requests");
  return data.items || [];
}

