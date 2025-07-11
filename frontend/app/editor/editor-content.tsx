"use client";

import { useState, useEffect, useCallback } from "react";
import dynamic from "next/dynamic";
import LatexEditor from "@/components/editor";
import axios from "axios";
import { toast } from "sonner";
import Link from "next/link";
import { User, Resume, EditorContentProps, Message } from "@/lib/types";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { IoChevronBackSharp } from "react-icons/io5";
import { IoMdDownload } from "react-icons/io";
import Chat from "@/components/chat";

const PdfPreview = dynamic(() => import("@/components/pdf-preview"), {
  ssr: false,
});

export default function EditorContent({
  user,
  initialResume,
}: EditorContentProps) {
  const [latex, setLatex] = useState<string>(
    initialResume?.latexContent ||
      "\\documentclass{article}\\begin{document}Hello, world!\\end{document}"
  );
  const [pdfUrl, setPdfUrl] = useState<string>("");
  const [zoom, setZoom] = useState<number>(100);
  const [showSaveModal, setShowSaveModal] = useState<boolean>(false);
  const [resumeTitle, setResumeTitle] = useState<string>(
    initialResume?.title || ""
  );
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [currentResumeId, setCurrentResumeId] = useState<string | null>(
    initialResume?.id || null
  );
  const [editorWidth, setEditorWidth] = useState<number>(50); // Percentage width
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"code" | "chat">("code");

  // Chat state
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content:
        "Hello! I'm your **LaTeX resume assistant**. I can help you modify your resume through natural language commands. For example:\n\n- 'Add a skills section with JavaScript and React'\n- 'Make the title bigger and bold'\n- 'Add my education from MIT'\n- 'Change the font to Times New Roman'\n\nWhat would you like me to help you with?",
      role: "assistant",
      timestamp: new Date(),
    },
  ]);

  // Load existing PDF if available
  useEffect(() => {
    if (initialResume?.pdfUrl) {
      setPdfUrl(initialResume.pdfUrl);
    }
  }, [initialResume]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isDragging) return;

      const containerRect = document
        .querySelector(".resizable-container")
        ?.getBoundingClientRect();
      if (!containerRect) return;

      const newWidth =
        ((e.clientX - containerRect.left) / containerRect.width) * 100;
      // Constrain between 20% and 80%
      const constrainedWidth = Math.min(Math.max(newWidth, 20), 80);
      setEditorWidth(constrainedWidth);
    },
    [isDragging]
  );

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
    } else {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
  }, [isDragging, handleMouseMove, handleMouseUp]);

  const handleCompile = async (latexContent?: string) => {
    const contentToCompile = latexContent || latex;
    try {
      // Create a blob from the LaTeX content
      const latexBlob = new Blob([contentToCompile], { type: "text/plain" });

      // Create FormData to send the file
      const formData = new FormData();
      formData.append("file", latexBlob, "resume.tex");

      // Make API call to compile endpoint using axios
      const response = await axios.post("/api/compile", formData, {
        responseType: "blob",
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      // Create object URL for the PDF blob
      const url = URL.createObjectURL(response.data);
      setPdfUrl(url);
      toast.success("LaTeX compiled successfully!");

      // Auto-update saved resume if it exists
      if (currentResumeId && resumeTitle.trim()) {
        try {
          // Create FormData for updating the resume
          const updateFormData = new FormData();
          updateFormData.append("resumeId", currentResumeId);
          updateFormData.append("title", resumeTitle);
          updateFormData.append("latexContent", contentToCompile);
          updateFormData.append("pdf", response.data, "resume.pdf");

          const updateResponse = await axios.put(
            "/api/update-resume",
            updateFormData,
            {
              headers: {
                "Content-Type": "multipart/form-data",
              },
            }
          );

          if (updateResponse.data.success) {
            toast.success("Resume automatically updated!");
          }
        } catch (updateError) {
          console.error("Error auto-updating resume:", updateError);
          // Don't show error toast for auto-update failure, just log it
        }
      }
    } catch (error) {
      console.error("Error compiling LaTeX:", error);
      if (axios.isAxiosError(error)) {
        console.error("Axios error details:", error.response?.data);
      }
      toast.error("Failed to compile LaTeX. Please check your syntax.");
    }
  };

  const handleSave = async () => {
    if (!resumeTitle.trim()) {
      toast.error("Please enter a title for your resume");
      return;
    }

    if (!pdfUrl) {
      toast.error("Please compile your resume first");
      return;
    }

    setIsSaving(true);
    try {
      // Get the PDF blob from the current URL
      const pdfResponse = await fetch(pdfUrl);
      const pdfBlob = await pdfResponse.blob();

      // Create FormData
      const formData = new FormData();
      formData.append("title", resumeTitle);
      formData.append("latexContent", latex);
      formData.append("pdf", pdfBlob, "resume.pdf");

      let response;

      if (currentResumeId) {
        // Update existing resume
        formData.append("resumeId", currentResumeId);
        response = await axios.put("/api/update-resume", formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        });
      } else {
        // Create new resume
        response = await axios.post("/api/save-resume", formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        });
      }

      if (response.data.success) {
        const message = currentResumeId
          ? "Resume updated successfully!"
          : "Resume saved successfully!";
        toast.success(message);
        setShowSaveModal(false);

        // If this was a new resume, set the ID for future updates
        if (!currentResumeId) {
          setCurrentResumeId(response.data.id);
        }
      }
    } catch (error) {
      console.error("Error saving resume:", error);
      const action = currentResumeId ? "update" : "save";
      toast.error(`Failed to ${action} resume. Please try again.`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleZoomIn = () => {
    setZoom((prev) => Math.min(prev + 25, 200));
  };

  const handleZoomOut = () => {
    setZoom((prev) => Math.max(prev - 25, 50));
  };

  const handleDownload = () => {
    if (pdfUrl) {
      const link = document.createElement("a");
      link.href = pdfUrl;
      link.download = "resume.pdf";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Main Content */}
      <div className="resizable-container flex h-screen p-2">
        <div className="flex flex-col" style={{ width: `${editorWidth}%` }}>
          {/* Tabs */}
          <div className="flex mb-0">
            <button
              onClick={() => setActiveTab("code")}
              className={`px-3 py-1 text-sm font-medium border-b-2 transition-colors ${
                activeTab === "code"
                  ? "border-blue-500 text-blue-600 bg-blue-50"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              Code
            </button>
            <button
              onClick={() => setActiveTab("chat")}
              className={`px-3 py-1 text-sm font-medium border-b-2 transition-colors ${
                activeTab === "chat"
                  ? "border-blue-500 text-blue-600 bg-blue-50"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              Chat
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-hidden">
            {activeTab === "code" ? (
              <LatexEditor
                value={latex}
                onChange={(val) => setLatex(val ?? "")}
              />
            ) : (
              <Chat
                latexContent={latex}
                onLatexUpdate={setLatex}
                onCompile={handleCompile}
                messages={messages}
                onMessagesUpdate={setMessages}
              />
            )}
          </div>
        </div>

        {/* Resizable splitter */}
        <div
          className="w-1.5 hover:bg-gray-400 cursor-col-resize flex-shrink-0 transition-colors flex flex-col items-center justify-center"
          onMouseDown={handleMouseDown}
        >
          <div className="flex flex-col space-y-0.5">
            <div className="w-1 h-1 bg-gray-500 rounded-full"></div>
            <div className="w-1 h-1 bg-gray-500 rounded-full"></div>
            <div className="w-1 h-1 bg-gray-500 rounded-full"></div>
          </div>
        </div>

        <div
          className="flex flex-col px-1"
          style={{ width: `${100 - editorWidth}%` }}
        >
          <div className="flex flex-wrap justify-between items-center mb-1 gap-2">
            <Link href="/" className="flex-shrink-0">
              <button className="flex items-center px-2 py-1 bg-gray-300 text-gray-700 text-sm rounded hover:bg-gray-200">
                <IoChevronBackSharp className="mr-1" />
                <span className="hidden sm:inline">Back</span>
              </button>
            </Link>
            <div className="flex flex-wrap gap-1 sm:gap-2 items-center">
              <button
                onClick={() => handleCompile()}
                className="bg-blue-500 px-2 sm:px-3 py-1 text-white text-xs sm:text-sm rounded hover:bg-blue-600 flex-shrink-0"
              >
                <span className="hidden sm:inline">Compile</span>
                <span className="sm:hidden">▶</span>
              </button>
              <Dialog open={showSaveModal} onOpenChange={setShowSaveModal}>
                <DialogTrigger asChild>
                  <button
                    disabled={!pdfUrl}
                    className="bg-purple-500 px-2 sm:px-3 py-1 text-white text-xs sm:text-sm rounded hover:bg-purple-600 disabled:bg-gray-300 flex-shrink-0"
                  >
                    <span className="hidden sm:inline">
                      {currentResumeId ? "Update" : "Save"}
                    </span>
                    <span className="sm:hidden">💾</span>
                  </button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-md">
                  <DialogHeader>
                    <DialogTitle>
                      {currentResumeId ? "Update Resume" : "Save Resume"}
                    </DialogTitle>
                    <DialogDescription>
                      Enter a title for your resume to save it.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="mb-4">
                    <label
                      htmlFor="resumeTitle"
                      className="block text-sm font-medium text-gray-700 mb-2"
                    >
                      Resume Title
                    </label>
                    <input
                      type="text"
                      id="resumeTitle"
                      value={resumeTitle}
                      onChange={(e) => setResumeTitle(e.target.value)}
                      placeholder="e.g., Software Engineer Resume"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                      disabled={isSaving}
                    />
                  </div>
                  <div className="flex gap-3 justify-end">
                    <button
                      onClick={() => {
                        setShowSaveModal(false);
                        setResumeTitle("");
                      }}
                      disabled={isSaving}
                      className="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSave}
                      disabled={isSaving || !resumeTitle.trim()}
                      className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:bg-gray-300"
                    >
                      {isSaving
                        ? currentResumeId
                          ? "Updating..."
                          : "Saving..."
                        : currentResumeId
                        ? "Update Resume"
                        : "Save Resume"}
                    </button>
                  </div>
                </DialogContent>
              </Dialog>
              <div className="flex items-center bg-white rounded-lg text-xs sm:text-sm shadow-sm flex-shrink-0">
                <button
                  onClick={handleZoomOut}
                  disabled={zoom <= 50}
                  className="px-1 sm:px-2 py-1 text-gray-600 hover:text-gray-800 disabled:text-gray-300 disabled:cursor-not-allowed transition-colors border-r border-gray-200"
                >
                  -
                </button>
                <span className="px-2 sm:px-3 py-1 font-medium text-gray-700 min-w-[40px] sm:min-w-[50px] text-center bg-gray-50">
                  {zoom}%
                </span>
                <button
                  onClick={handleZoomIn}
                  disabled={zoom >= 200}
                  className="px-1 sm:px-2 py-1 text-gray-600 hover:text-gray-800 disabled:text-gray-300 disabled:cursor-not-allowed transition-colors border-l border-gray-200"
                >
                  +
                </button>
              </div>
              <button
                onClick={handleDownload}
                disabled={!pdfUrl}
                className="flex items-center bg-green-500 px-2 sm:px-3 py-1 text-white text-xs sm:text-sm rounded hover:bg-green-600 disabled:bg-gray-300 flex-shrink-0"
              >
                <IoMdDownload className="mr-0 sm:mr-1.5" />
                <span className="hidden sm:inline">Download</span>
              </button>
            </div>
          </div>
          <PdfPreview pdfUrl={pdfUrl} zoom={zoom} />
        </div>
      </div>
    </div>
  );
}
