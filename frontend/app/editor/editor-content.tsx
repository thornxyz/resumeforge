"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import LatexEditor from "@/components/editor";
import axios from "axios";

const PdfPreview = dynamic(() => import("@/components/pdf-preview"), {
  ssr: false,
});

interface User {
  name?: string | null;
  email?: string | null;
  image?: string | null;
}

export default function EditorContent({ user }: { user: User }) {
  const [latex, setLatex] = useState<string>(
    "\\documentclass{article}\\begin{document}Hello, world!\\end{document}"
  );
  const [pdfUrl, setPdfUrl] = useState<string>("");
  const [zoom, setZoom] = useState<number>(100);

  const handleCompile = async () => {
    try {
      // Create a blob from the LaTeX content
      const latexBlob = new Blob([latex], { type: "text/plain" });

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
    } catch (error) {
      console.error("Error compiling LaTeX:", error);
      if (axios.isAxiosError(error)) {
        console.error("Axios error details:", error.response?.data);
      }
      // You might want to show an error message to the user here
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
    <div className="min-h-screen bg-gray-50">
      {/* Main Content */}
      <div className="grid grid-cols-2 gap-4 p-4">
        <div>
          <LatexEditor value={latex} onChange={(val) => setLatex(val ?? "")} />
        </div>
        <div>
          <div className="flex gap-2 mb-2">
            <button
              onClick={handleCompile}
              className="bg-blue-500 px-3 py-1 text-white text-sm rounded hover:bg-blue-600"
            >
              Compile
            </button>
            <button
              onClick={handleZoomIn}
              disabled={zoom >= 200}
              className="bg-gray-500 px-2 py-1 text-white text-sm rounded hover:bg-gray-600 disabled:bg-gray-300"
            >
              +
            </button>
            <button
              onClick={handleZoomOut}
              disabled={zoom <= 50}
              className="bg-gray-500 px-2 py-1 text-white text-sm rounded hover:bg-gray-600 disabled:bg-gray-300"
            >
              −
            </button>
            <span className="px-2 py-1 text-sm text-gray-600">{zoom}%</span>
            <button
              onClick={handleDownload}
              disabled={!pdfUrl}
              className="bg-green-500 px-3 py-1 text-white text-sm rounded hover:bg-green-600 disabled:bg-gray-300"
            >
              Download
            </button>
          </div>
          <PdfPreview pdfUrl={pdfUrl} zoom={zoom} />
        </div>
      </div>
    </div>
  );
}
