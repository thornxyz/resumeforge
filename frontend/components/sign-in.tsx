import { signIn } from "@/auth";
import { FcGoogle } from "react-icons/fc";

export default function SignIn() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-2xl shadow-xl p-8 space-y-8">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Welcome to ResumeForge
            </h1>
            <p className="text-gray-600">
              Create professional resumes with AI assistance
            </p>
          </div>

          <div className="space-y-4">
            <form
              action={async () => {
                "use server";
                await signIn("google");
              }}
            >
              <button
                type="submit"
                className="w-full flex items-center justify-center gap-3 bg-white border-2 border-gray-300 rounded-lg px-6 py-3 text-gray-700 font-medium hover:bg-gray-50 hover:border-gray-400 transition-colors duration-200 shadow-sm"
              >
                <FcGoogle size={24} />
                Continue with Google
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
