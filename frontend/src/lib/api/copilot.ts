import { apiClient } from "@/lib/api/client";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface CopilotStatus {
  configured: boolean;
  model: string | null;
}

export const copilotApi = {
  status: async (): Promise<CopilotStatus> =>
    (await apiClient.get<CopilotStatus>("/copilot/status")).data,
  chat: async (messages: ChatMessage[]): Promise<string> => {
    const { data } = await apiClient.post<{ message: string }>("/copilot/chat", { messages });
    return data.message;
  },
};
