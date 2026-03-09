import api from "./api";

export async function getVapidPublicKey() {
  const { data } = await api.get("/notifications/public-key");
  return data.public_key;
}

export async function subscribePush(subscription) {
  const { data } = await api.post("/notifications/subscribe", subscription);
  return data;
}

export async function sendPushNotification(payload) {
  const { data } = await api.post("/notifications/send", payload);
  return data;
}
