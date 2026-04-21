import type { Metadata } from "next";

import RegisterPageClient from "@/components/register-page-client";

export const metadata: Metadata = {
  title: "Register | MalLog",
  description: "Create a MalLog account and enter the protected workspace.",
};

export default function RegisterPage() {
  return <RegisterPageClient />;
}
