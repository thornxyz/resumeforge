"use client";

import { useState, useRef, useEffect } from "react";
import { IoSend } from "react-icons/io5";
import { BsRobot } from "react-icons/bs";
import { Message, ChatProps } from "@/lib/types";
import axios from "axios";
import { toast } from "sonner";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function Chat({
  latexContent,
  onLatexUpdate,
  onCompile,
  messages,
  onMessagesUpdate,
}: ChatProps) {
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState<"ask" | "edit">("ask");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const threadIdRef = useRef<string>("");
  if (!threadIdRef.current) {
    threadIdRef.current =
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  }

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
        mode,
        threadId: threadIdRef.current,
      });

      console.log("API Response:", response.data); // Debug log

      if (response.data) {
        // Always try to get a response, regardless of success status
        if (response.data.threadId) {
          threadIdRef.current = response.data.threadId;
        }

        if (response.data.mode === "ask" || response.data.mode === "edit") {
          setMode(response.data.mode);
        }

        const toolsUsed: string[] = Array.isArray(response.data.toolsUsed)
          ? response.data.toolsUsed.filter(Boolean)
          : [];

        let assistantContent =
          response.data.explanation ||
          response.data.response ||
          response.data.error ||
          "I apologize, but I couldn't generate a proper response.";

        if (toolsUsed.length > 0) {
          assistantContent += `\n\n_Tools used: ${toolsUsed.join(", ")}_`;
        }

        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: assistantContent,
          role: "assistant",
          timestamp: new Date(),
        };

        // Update messages with both user and assistant messages
        const updatedMessages = [...messages, userMessage, assistantMessage];
        onMessagesUpdate(updatedMessages);

        // If the AI returned modified LaTeX code and the operation was successful, apply it
        const isEditFlow =
          (response.data.mode || mode) === "edit" || mode === "edit";

        if (
          isEditFlow &&
          response.data.success &&
          response.data.modifiedLatex &&
          response.data.modifiedLatex !== latexContent
        ) {
          // Apply the change directly
          onLatexUpdate(response.data.modifiedLatex);

          // Trigger compilation with the new content directly
          onCompile(response.data.modifiedLatex);

          toast.success("Code updated and compiled successfully!");
        } else if (response.data.modifiedLatex && !response.data.success) {
          // If there's modified LaTeX but operation failed, still update but don't compile
          onLatexUpdate(response.data.modifiedLatex);
          toast.info(
            "LaTeX code updated, but there may be issues. Check the response for details."
          );
        }

        if (
          response.data.compilation_result &&
          response.data.compilation_result.status === "error"
        ) {
          const errors = response.data.compilation_result.errors || [];
          const errorText =
            Array.isArray(errors) && errors.length > 0
              ? errors.join("\n")
              : "Compilation failed";
          toast.error(errorText);
        }
      } else {
        throw new Error("No response data received from AI");
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

  // Retry logic
  const [retrying, setRetrying] = useState(false);
  const handleRetry = async () => {
    if (isLoading || retrying) return;
    setRetrying(true);
    // Find the last user message
    const lastUserMessage = [...messages]
      .reverse()
      .find((msg) => msg.role === "user");
    if (!lastUserMessage) {
      setRetrying(false);
      return;
    }
    try {
      const response = await axios.post("/api/chat", {
        message: lastUserMessage.content,
        conversationHistory: messages.slice(-10),
        latexContent: latexContent,
        mode,
        threadId: threadIdRef.current,
      });

      console.log("Retry API Response:", response.data); // Debug log

      if (response.data && response.data.success) {
        if (response.data.threadId) {
          threadIdRef.current = response.data.threadId;
        }

        if (response.data.mode === "ask" || response.data.mode === "edit") {
          setMode(response.data.mode);
        }

        const toolsUsed: string[] = Array.isArray(response.data.toolsUsed)
          ? response.data.toolsUsed.filter(Boolean)
          : [];

        let assistantContent =
          response.data.explanation ||
          response.data.response ||
          "I apologize, but I couldn't generate a proper response.";

        if (toolsUsed.length > 0) {
          assistantContent += `\n\n_Tools used: ${toolsUsed.join(", ")}_`;
        }

        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: assistantContent,
          role: "assistant",
          timestamp: new Date(),
        };
        const updatedMessages = [...messages, assistantMessage];
        onMessagesUpdate(updatedMessages);
        const isEditFlow =
          (response.data.mode || mode) === "edit" || mode === "edit";

        if (
          isEditFlow &&
          response.data.modifiedLatex &&
          response.data.modifiedLatex !== latexContent
        ) {
          // Apply the change directly
          onLatexUpdate(response.data.modifiedLatex);

          // Trigger compilation with the new content directly
          onCompile(response.data.modifiedLatex);

          toast.success("Code updated and compiled successfully!");
        }
      } else {
        throw new Error(response.data?.error || "Failed to get response");
      }
    } catch (error) {
      console.error("Retry error:", error);
      toast.error("Retry failed. Please try again later.");
    } finally {
      setRetrying(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white overflow-hidden">
      <div className="border-b border-gray-200 px-2 py-2 flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">Mode</span>
        <div className="inline-flex rounded-md shadow-sm" role="group">
          <button
            type="button"
            onClick={() => setMode("ask")}
            className={`px-3 py-1 text-xs font-medium border border-gray-300 first:rounded-l-md last:rounded-r-md focus:z-10 focus:outline-none focus:ring-1 focus:ring-blue-500 ${
              mode === "ask"
                ? "bg-blue-600 text-white border-blue-600"
                : "bg-white text-gray-700 hover:bg-gray-50"
            }`}
            disabled={isLoading}
          >
            Ask
          </button>
          <button
            type="button"
            onClick={() => setMode("edit")}
            className={`px-3 py-1 text-xs font-medium border border-gray-300 first:rounded-l-md last:rounded-r-md focus:z-10 focus:outline-none focus:ring-1 focus:ring-blue-500 ${
              mode === "edit"
                ? "bg-blue-600 text-white border-blue-600"
                : "bg-white text-gray-700 hover:bg-gray-50"
            }`}
            disabled={isLoading}
          >
            Edit
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-2 py-2 space-y-4 min-h-0">
        {messages.map((message, idx) => (
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
                  {message.role === "assistant" ? (
                    <div className="text-sm prose prose-sm max-w-none prose-p:my-1 prose-ul:my-2 prose-ol:my-2 prose-li:my-0 prose-ul:pl-4 prose-ol:pl-4">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          ul: ({ ...props }) => (
                            <ul className="list-disc pl-4 my-2" {...props} />
                          ),
                          ol: ({ ...props }) => (
                            <ol className="list-decimal pl-4 my-2" {...props} />
                          ),
                          li: ({ ...props }) => (
                            <li className="my-0.5" {...props} />
                          ),
                          p: ({ ...props }) => (
                            <p className="my-1" {...props} />
                          ),
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <p className="text-sm whitespace-pre-wrap">
                      {message.content}
                    </p>
                  )}
                </div>
                <span className="text-xs text-gray-500 mt-1 px-1">
                  {formatTime(message.timestamp)}
                </span>
                {/* Retry button: only show for last assistant message */}
                {idx === messages.length - 1 &&
                  message.role === "assistant" && (
                    <button
                      onClick={handleRetry}
                      disabled={isLoading || retrying}
                      className="mt-1 text-xs text-blue-600 underline disabled:text-gray-400"
                    >
                      {retrying ? "Retrying..." : "Retry"}
                    </button>
                  )}
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
