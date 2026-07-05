import { useMutation, useQuery } from "@tanstack/react-query";
import axios from "axios";
import { Bot, Loader2, Send, Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getApiErrorMessage } from "@/lib/api/client";
import { copilotApi, type ChatMessage } from "@/lib/api/copilot";
import { cn } from "@/lib/utils";

const SUGGESTIONS = [
  "How is my business doing this month?",
  "Which products should I reorder?",
  "Who are my best customers?",
  "How can I improve my profit?",
];

export function CopilotPage() {
  const { data: status, isLoading } = useQuery({
    queryKey: ["copilot-status"],
    queryFn: copilotApi.status,
  });

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [needsUpgrade, setNeedsUpgrade] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const chat = useMutation({
    mutationFn: (history: ChatMessage[]) => copilotApi.chat(history),
    onSuccess: (reply) => setMessages((prev) => [...prev, { role: "assistant", content: reply }]),
    onError: (error) => {
      // 402 → the Copilot is a Pro feature and this company is on Free.
      if (axios.isAxiosError(error) && error.response?.status === 402) {
        setNeedsUpgrade(true);
      } else {
        toast.error(getApiErrorMessage(error));
      }
    },
  });

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, chat.isPending]);

  const send = (text: string) => {
    const content = text.trim();
    if (!content || chat.isPending) return;
    const next: ChatMessage[] = [...messages, { role: "user", content }];
    setMessages(next);
    setInput("");
    chat.mutate(next);
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!status?.configured) {
    return (
      <div className="mx-auto max-w-xl py-16">
        <Card>
          <CardContent className="flex flex-col items-center gap-3 p-8 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <Bot className="h-6 w-6" />
            </span>
            <h2 className="text-lg font-semibold">AI Copilot isn&apos;t configured</h2>
            <p className="text-sm text-muted-foreground">
              Add a <code className="rounded bg-muted px-1">GEMINI_API_KEY</code> to the backend
              environment to enable the Copilot. Everything else keeps working without it.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (needsUpgrade) {
    return (
      <div className="mx-auto max-w-xl py-16">
        <Card>
          <CardContent className="flex flex-col items-center gap-4 p-8 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <Sparkles className="h-6 w-6" />
            </span>
            <h2 className="text-lg font-semibold">The AI Copilot is a Pro feature</h2>
            <p className="text-sm text-muted-foreground">
              Upgrade to Pro to ask questions about your business and get instant, data-grounded
              answers.
            </p>
            <Button asChild>
              <Link to="/settings?billing=upgrade">
                <Sparkles className="h-4 w-4" /> Upgrade to Pro
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-7rem)] max-w-3xl flex-col">
      <div className="mb-4 flex items-center gap-2">
        <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Sparkles className="h-5 w-5" />
        </span>
        <div>
          <h1 className="text-lg font-semibold leading-tight">AI Copilot</h1>
          <p className="text-xs text-muted-foreground">
            Ask anything about your business — grounded in your live data.
          </p>
        </div>
      </div>

      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto rounded-xl border border-border bg-card/40 p-4">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
            <Bot className="h-10 w-10 text-muted-foreground/60" />
            <p className="text-sm text-muted-foreground">Ask me anything, or try one of these:</p>
            <div className="flex flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="rounded-full border border-border px-3 py-1.5 text-sm transition-colors hover:bg-accent hover:text-accent-foreground"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m, i) => (
            <div
              key={i}
              className={cn("flex gap-3", m.role === "user" ? "justify-end" : "justify-start")}
            >
              {m.role === "assistant" && (
                <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Bot className="h-4 w-4" />
                </span>
              )}
              <div
                className={cn(
                  "max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm",
                  m.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-foreground",
                )}
              >
                {m.content}
              </div>
            </div>
          ))
        )}

        {chat.isPending && (
          <div className="flex gap-3">
            <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Bot className="h-4 w-4" />
            </span>
            <div className="flex items-center gap-1 rounded-2xl bg-muted px-4 py-3">
              <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/60 [animation-delay:-0.3s]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/60 [animation-delay:-0.15s]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/60" />
            </div>
          </div>
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="mt-4 flex gap-2"
      >
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask your business copilot…"
          disabled={chat.isPending}
        />
        <Button type="submit" size="icon" disabled={chat.isPending || !input.trim()}>
          <Send className="h-4 w-4" />
        </Button>
      </form>
    </div>
  );
}
