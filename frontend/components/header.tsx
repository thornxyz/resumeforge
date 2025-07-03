import { auth } from "@/auth";
import { handleSignOut } from "@/lib/actions";
import Link from "next/link";
import Image from "next/image";

export default async function Header() {
  const session = await auth();

  if (!session?.user) {
    return null;
  }

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-12">
          <Link href="/">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">ResumeForge</h1>
            </div>
          </Link>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-3">
              {session.user.image && (
                <Image
                  width={32}
                  height={32}
                  src={session.user.image}
                  alt={session.user.name || "User"}
                  className="w-8 h-8 rounded-full"
                />
              )}
              <span className="text-sm font-medium text-gray-700">
                {session.user.name}
              </span>
            </div>
            <form action={handleSignOut}>
              <button
                type="submit"
                className="text-gray-500 hover:text-gray-700 text-sm font-medium"
              >
                Sign out
              </button>
            </form>
          </div>
        </div>
      </div>
    </header>
  );
}
