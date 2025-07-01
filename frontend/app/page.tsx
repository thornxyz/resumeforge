import { auth } from "@/auth";
import SignIn from "@/components/sign-in";
import Dashboard from "@/components/dashboard";
import AuthenticatedHeader from "@/components/authenticated-header";

export default async function Home() {
  const session = await auth();

  if (!session?.user) {
    return <SignIn />;
  }

  return (
    <>
      <AuthenticatedHeader />
      <Dashboard />
    </>
  );
}
