import type { Metadata } from "next";

import LoginPageClient from "@/components/login-page-client";

export const metadata: Metadata = {
  title: "Login | MalLog",
  description: "Sign in to the protected MalLog workspace.",
};

export default function LoginPage() {
  return <LoginPageClient />;
}
