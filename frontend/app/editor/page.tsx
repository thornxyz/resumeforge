"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import LatexEditor from "@/components/editor";
import PdfPreview from "@/components/pdf-preview";
import Link from "next/link";

export default function Page() {
  const [latex, setLatex] = useState<string>(
    "\\documentclass{article}\\begin{document}Hello, world!\\end{document}"
  );
  const [pdfUrl, setPdfUrl] = useState<string>("");
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [user, setUser] = useState<any>(null);
  const router = useRouter();

  // Check authentication status
  useEffect(() => {
    fetch("/api/auth/session")
      .then((res) => res.json())
      .then((data) => {
        if (data.user) {
          setIsAuthenticated(true);
          setUser(data.user);
        } else {
          setIsAuthenticated(false);
          router.push("/");
        }
      })
      .catch(() => {
        setIsAuthenticated(false);
        router.push("/");
      });
  }, [router]);

  const handleSignOut = async () => {
    await fetch("/api/auth/signout", { method: "POST" });
    router.push("/");
  };

  const handleCompile = async () => {
    try {
      // Create a blob from the LaTeX content
      const latexBlob = new Blob([latex], { type: "text/plain" });

      // Create FormData to send the file
      const formData = new FormData();
      formData.append("file", latexBlob, "resume.tex");

      // Make API call to compile endpoint
      const response = await fetch("/api/compile", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Compilation failed");
      }

      // Create object URL for the PDF blob
      const pdfBlob = await response.blob();
      const url = URL.createObjectURL(pdfBlob);
      setPdfUrl(url);
    } catch (error) {
      console.error("Error compiling LaTeX:", error);
      // You might want to show an error message to the user here
    }
  };

  // Show loading state while checking authentication
  if (isAuthenticated === null) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render if not authenticated (will redirect)
  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Shared Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">ResumeForge</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                {user?.image && (
                  <img
                    src={user.image}
                    alt={user.name || "User"}
                    className="w-8 h-8 rounded-full"
                  />
                )}
                <span className="text-sm font-medium text-gray-700">
                  {user?.name}
                </span>
              </div>
              <button
                onClick={handleSignOut}
                className="text-gray-500 hover:text-gray-700 text-sm font-medium"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Editor Navigation */}
      <div className="bg-gray-50 border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-12">
            <div className="flex items-center space-x-4">
              <Link
                href="/"
                className="text-gray-500 hover:text-gray-700 flex items-center text-sm"
              >
                <svg
                  className="w-4 h-4 mr-1"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
                Back to Dashboard
              </Link>
              <span className="text-gray-300">•</span>
              <span className="text-sm font-medium text-gray-900">
                Resume Editor
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <button className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800 font-medium">
                Save Draft
              </button>
              <button className="px-3 py-1 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors font-medium">
                Preview
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-2 gap-4 p-4">
        <div>
          <LatexEditor value={latex} onChange={(val) => setLatex(val ?? "")} />
          <button
            onClick={handleCompile}
            className="mt-2 bg-blue-500 px-4 py-2 text-white rounded"
          >
            Compile
          </button>
        </div>
        <PdfPreview pdfUrl={pdfUrl} />
      </div>
    </div>
  );
}
