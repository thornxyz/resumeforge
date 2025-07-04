import { auth } from "@/auth";
import Link from "next/link";
import { getUserResumes } from "@/lib/actions";
import ResumeCard from "./resume-card";
import { Resume } from "@/lib/types";
import { IoMdCreate } from "react-icons/io";
import { IoDocumentTextOutline } from "react-icons/io5";

export default async function Dashboard() {
  const session = await auth();

  if (!session?.user) {
    return null;
  }

  const resumes = await getUserResumes();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome back, {session.user.name?.split(" ")[0]}! 👋
          </h2>
          <p className="text-gray-600 mb-6">
            Ready to create your next professional resume?
          </p>
          <Link
            href="/editor"
            className="inline-flex items-center px-4 py-3 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 transition-colors duration-200 shadow-sm"
          >
            <IoMdCreate className="mr-2" size={19} />
            Create New Resume
          </Link>
        </div>

        {/* Saved Resumes Section */}
        <div className="mb-8">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">
            Your Resumes
          </h3>
          {resumes.length === 0 ? (
            <div className="text-center py-8 bg-white rounded-lg border-2 border-dashed border-gray-300">
              <IoDocumentTextOutline
                className="mx-auto mb-2 text-gray-500"
                size={100}
              />
              <h4 className="text-lg font-medium text-gray-900 mb-2">
                No resumes yet
              </h4>
              <p className="text-gray-600 mb-4">
                Create your first resume to get started
              </p>
              <Link
                href="/editor"
                className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700"
              >
                Create Resume
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {resumes.map((resume: Resume) => (
                <ResumeCard key={resume.id} resume={resume} />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
