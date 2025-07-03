"use client";

import { deleteResume } from "@/lib/actions";
import Link from "next/link";

interface Resume {
  id: string;
  title: string;
  latexContent: string;
  pdfUrl: string | null;
  createdAt: Date;
  updatedAt: Date;
}

export default function ResumeCard({ resume }: { resume: Resume }) {
  const handleDelete = async () => {
    if (confirm("Are you sure you want to delete this resume?")) {
      try {
        await deleteResume(resume.id);
      } catch (error) {
        alert("Failed to delete resume");
      }
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <h4 className="text-lg font-semibold text-gray-900 truncate pr-2">
            {resume.title}
          </h4>
          <button
            onClick={handleDelete}
            className="text-gray-400 hover:text-red-500 transition-colors"
            title="Delete resume"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </button>
        </div>

        <p className="text-sm text-gray-600 mb-4">
          Updated {new Date(resume.updatedAt).toLocaleDateString()}
        </p>

        <div className="flex flex-wrap gap-2">
          <Link
            href={`/editor?resumeId=${resume.id}`}
            className="inline-flex items-center px-3 py-1.5 bg-indigo-100 text-indigo-700 text-sm rounded hover:bg-indigo-200 transition-colors"
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
                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
              />
            </svg>
            Edit
          </Link>

          {resume.pdfUrl && (
            <a
              href={resume.pdfUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-3 py-1.5 bg-blue-100 text-blue-700 text-sm rounded hover:bg-blue-200 transition-colors"
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
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                />
              </svg>
              View PDF
            </a>
          )}

          <a
            href={resume.pdfUrl || "#"}
            download="resume.pdf"
            className={`inline-flex items-center px-3 py-1.5 text-sm rounded transition-colors ${
              resume.pdfUrl
                ? "bg-green-100 text-green-700 hover:bg-green-200"
                : "bg-gray-100 text-gray-400 cursor-not-allowed"
            }`}
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
                d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            Download
          </a>
        </div>
      </div>
    </div>
  );
}
