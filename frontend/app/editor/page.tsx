import { auth } from "@/auth";
import { redirect } from "next/navigation";
import EditorContent from "./editor-content";
import Header from "@/components/header";

export default async function Page() {
  const session = await auth();

  if (!session?.user) {
    redirect("/");
  }

  return (
    <>
      <Header />
      <EditorContent user={session.user} />
    </>
  );
}
