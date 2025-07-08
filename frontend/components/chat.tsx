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

        // If the AI returned modified LaTeX code, apply it directly and compile
        if (
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
        mode: "agent",
      });
      if (response.data.success) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: response.data.explanation || response.data.response,
          role: "assistant",
          timestamp: new Date(),
        };
        const updatedMessages = [...messages, assistantMessage];
        onMessagesUpdate(updatedMessages);
        if (
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
        throw new Error(response.data.error || "Failed to get response");
      }
    } catch (error) {
      toast.error("Retry failed. Please try again later.");
    } finally {
      setRetrying(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white overflow-hidden">
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
                          ul: ({ node, ...props }) => (
                            <ul className="list-disc pl-4 my-2" {...props} />
                          ),
                          ol: ({ node, ...props }) => (
                            <ol className="list-decimal pl-4 my-2" {...props} />
                          ),
                          li: ({ node, ...props }) => (
                            <li className="my-0.5" {...props} />
                          ),
                          p: ({ node, ...props }) => (
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
