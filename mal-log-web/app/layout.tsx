import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/use-auth";

export const metadata: Metadata = {
  title: "MalLog",
  description: "Protected log analysis workspace powered by the API gateway",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
