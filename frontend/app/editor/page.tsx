import { auth } from "@/auth";
import { redirect } from "next/navigation";
import EditorContent from "./editor-content";
import Header from "@/components/header";
import { getResumeById } from "@/lib/actions";

interface PageProps {
  searchParams: {
    resumeId?: string;
  };
}

export default async function Page({ searchParams }: PageProps) {
  const session = await auth();

  if (!session?.user) {
    redirect("/");
  }

  let resumeData = null;
  if (searchParams.resumeId) {
    resumeData = await getResumeById(searchParams.resumeId);
  }

  return (
    <>
      <Header />
      <EditorContent user={session.user} initialResume={resumeData} />
    </>
  );
}
