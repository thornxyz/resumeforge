"use client";

import { useState, useRef, useEffect } from "react";
import { IoSend } from "react-icons/io5";
import { BsRobot } from "react-icons/bs";

interface Message {
  id: string;
  content: string;
  role: "user" | "assistant";
  timestamp: Date;
}

function Chat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content:
        "Hello! I'm your AI assistant. I can help you with LaTeX resume writing, formatting, and any questions you might have. How can I assist you today?",
      role: "assistant",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Auto-focus the input field on mount and after messages
    if (textareaRef.current && !isLoading) {
      textareaRef.current.focus();
    }
  }, [messages, isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input.trim(),
      role: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // TODO: Replace with your actual AI API call
      // For now, simulate a response
      setTimeout(() => {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: `I understand you said: "${userMessage.content}". This is a placeholder response. You'll need to integrate with an AI service like OpenAI, Anthropic, or your preferred AI provider to get actual AI responses.`,
          role: "assistant",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
        setIsLoading(false);
      }, 1000);
    } catch (error) {
      console.error("Error sending message:", error);
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className="flex flex-col h-full bg-white overflow-hidden">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-2 py-2 space-y-4 min-h-0">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`flex max-w-[85%] ${
                message.role === "user" ? "flex-row-reverse" : "flex-row"
              }`}
            >
              {/* Avatar */}
              <div
                className={`flex-shrink-0 ${
                  message.role === "user" ? "ml-2" : "mr-2"
                }`}
              >
                {message.role === "assistant" && (
                  <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                    <BsRobot className="w-4 h-4 text-white" />
                  </div>
                )}
              </div>

              {/* Message Content */}
              <div className="flex flex-col">
                <div
                  className={`px-3 py-2 rounded-lg ${
                    message.role === "user"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-900"
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">
                    {message.content}
                  </p>
                </div>
                <span className="text-xs text-gray-500 mt-1 px-1">
                  {formatTime(message.timestamp)}
                </span>
              </div>
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="flex">
              <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center mr-2">
                <BsRobot className="w-4 h-4 text-white" />
              </div>
              <div className="bg-gray-100 px-3 py-2 rounded-lg">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0.1s" }}
                  ></div>
                  <div
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0.2s" }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 p-1 flex-shrink-0">
        <form onSubmit={handleSubmit} className="flex items-center gap-2">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me anything..."
            className="w-full text-base px-2 py-1 border border-gray-300 rounded-md resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
            rows={1}
            disabled={isLoading}
            autoFocus
            style={{
              minHeight: "20px",
              maxHeight: "200px",
            }}
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement;
              target.style.height = "40px";
              target.style.height = `${Math.min(target.scrollHeight, 200)}px`;
            }}
          />

          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="flex items-center justify-center w-15 h-10 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            <IoSend size={20} />
          </button>
        </form>
      </div>
    </div>
  );
}

export default Chat;
