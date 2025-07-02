"use client";

import { useState } from "react";
import LatexEditor from "@/components/editor";
import PdfPreview from "@/components/pdf-preview";
import axios from "axios";

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

  return (
    <div className="min-h-screen bg-gray-50">
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
