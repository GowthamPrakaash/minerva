import { auth } from "@/auth";
import { redirect } from "next/navigation";

/**
 * Root page: just authenticate and redirect to /dashboard.
 * The dashboard page handles showing orgs/businesses or sending to onboarding.
 */
export default async function HomePage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect("/auth/signin");
  }

  redirect("/dashboard");
}
