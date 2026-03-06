import { useQuery } from "@tanstack/react-query";

import { getPaymentStatus } from "../services/paymentService";

export default function useSubscription() {
  return useQuery({
    queryKey: ["subscription-status"],
    queryFn: getPaymentStatus,
    refetchInterval: 30000,
  });
}
