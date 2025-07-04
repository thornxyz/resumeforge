import { auth } from "@/auth";
import { redirect } from "next/navigation";
import EditorContent from "./editor-content";
import Header from "@/components/header";
import { getResumeById } from "@/lib/actions";
import { EditorPageProps } from "@/lib/types";

export default async function Page({ searchParams }: EditorPageProps) {
  const session = await auth();

  if (!session?.user) {
    redirect("/");
  }

  const params = await searchParams;
  let resumeData = null;
  if (params.resumeId) {
    resumeData = await getResumeById(params.resumeId);
  }

  return (
    <>
      <Header />
      <EditorContent user={session.user} initialResume={resumeData} />
    </>
  );
}
