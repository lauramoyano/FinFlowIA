import { useMutation } from "@tanstack/react-query";
import { orchestratorApi } from "@/features/transactions/api/transactions.api";

export function useSendChatMessage() {
  return useMutation({
    mutationFn: ({ conversationId, text }: { conversationId: string | null; text: string }) =>
      orchestratorApi.sendMessage(conversationId, text),
  });
}
