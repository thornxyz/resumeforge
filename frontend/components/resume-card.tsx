"use client";

import { deleteResume } from "@/lib/actions";
import Link from "next/link";
import { toast } from "sonner";
import { Resume, ResumeCardProps } from "@/lib/types";
import { MdDelete } from "react-icons/md";
import { FiEdit } from "react-icons/fi";
import { LuEye } from "react-icons/lu";
import { IoMdDownload } from "react-icons/io";

export default function ResumeCard({ resume }: ResumeCardProps) {
  const handleDelete = async () => {
    if (confirm("Are you sure you want to delete this resume?")) {
      try {
        await deleteResume(resume.id);
        toast.success("Resume deleted successfully");
      } catch (error) {
        toast.error("Failed to delete resume");
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
            <MdDelete size={22} />
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
            <FiEdit className="mr-1.5" />
            Edit
          </Link>

          {resume.pdfUrl && (
            <a
              href={resume.pdfUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-3 py-1.5 bg-blue-100 text-blue-700 text-sm rounded hover:bg-blue-200 transition-colors"
            >
              <LuEye className="mr-1.5" />
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
            <IoMdDownload className="mr-1.5" />
            Download
          </a>
        </div>
      </div>
    </div>
  );
}
