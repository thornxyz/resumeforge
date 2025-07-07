"use client";

import { useState, useRef, useEffect } from "react";
import { IoSend } from "react-icons/io5";
import { BsRobot } from "react-icons/bs";
import { Message, ChatProps } from "@/lib/types";
import axios from "axios";
import { toast } from "sonner";

function Chat({
  latexContent,
  onLatexUpdate,
  onCompile,
  messages,
  onMessagesUpdate,
}: ChatProps) {
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [pendingChange, setPendingChange] = useState<{
    originalLatex: string;
    newLatex: string;
    explanation: string;
  } | null>(null);
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

    onMessagesUpdate([...messages, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // Call the chat API
      const response = await axios.post("/api/chat", {
        message: userMessage.content,
        conversationHistory: [...messages, userMessage].slice(-10), // Include the new message
        latexContent: latexContent,
        mode: "agent",
      });

      if (response.data.success) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: response.data.explanation || response.data.response,
          role: "assistant",
          timestamp: new Date(),
        };

        // Update messages with both user and assistant messages
        const updatedMessages = [...messages, userMessage, assistantMessage];
        onMessagesUpdate(updatedMessages);

        // If the AI returned modified LaTeX code, show preview with keep/undo options
        if (
          response.data.modifiedLatex &&
          response.data.modifiedLatex !== latexContent
        ) {
          setPendingChange({
            originalLatex: latexContent,
            newLatex: response.data.modifiedLatex,
            explanation:
              response.data.explanation || "LaTeX code has been modified.",
          });

          // Apply the change immediately for preview
          onLatexUpdate(response.data.modifiedLatex);

          // Auto-compile to show the preview
          setTimeout(() => {
            onCompile();
          }, 500);
        }
      } else {
        throw new Error(response.data.error || "Failed to get response");
      }
    } catch (error) {
      console.error("Error sending message:", error);

      // Show error message to user
      let errorMessage = "Sorry, I'm having trouble responding right now.";
      if (axios.isAxiosError(error)) {
        if (error.response?.status === 401) {
          errorMessage =
            "API authentication failed. Please check the configuration.";
        } else if (error.response?.status === 429) {
          errorMessage = "API rate limit exceeded. Please try again later.";
        } else if (error.response?.data?.error) {
          errorMessage = error.response.data.error;
        }
      }

      toast.error(errorMessage);

      // Add error message to chat
      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        content: errorMessage,
        role: "assistant",
        timestamp: new Date(),
      };
      onMessagesUpdate([...messages, userMessage, errorResponse]);
    } finally {
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

  const handleKeepChange = () => {
    setPendingChange(null);
    toast.success("Changes applied successfully!");
  };

  const handleUndoChange = () => {
    if (pendingChange) {
      onLatexUpdate(pendingChange.originalLatex);
      setPendingChange(null);
      toast.info("Changes reverted");

      // Recompile with original content
      setTimeout(() => {
        onCompile();
      }, 500);
    }
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

      {/* Keep/Undo Actions - Show when there's a pending change */}
      {pendingChange && (
        <div className="border-t border-orange-200 bg-orange-50 p-3 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-orange-800 font-medium">
                LaTeX code modified
              </span>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={handleUndoChange}
                className="px-3 py-1 text-xs bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
              >
                Undo
              </button>
              <button
                onClick={handleKeepChange}
                className="px-3 py-1 text-xs bg-green-500 text-white rounded hover:bg-green-600 transition-colors"
              >
                Keep
              </button>
            </div>
          </div>
        </div>
      )}

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
