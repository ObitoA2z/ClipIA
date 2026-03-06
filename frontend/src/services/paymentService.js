import api from "./api";

export async function createCheckout(plan) {
  const { data } = await api.post("/payment/create-checkout", { plan });
  return data;
}

export async function getPaymentStatus() {
  const { data } = await api.get("/payment/status");
  return data;
}
