import type { Metadata } from "next";

import HomePageClient from "@/components/home-page-client";

export const metadata: Metadata = {
  title: "Workspace | MalLog",
  description: "Protected homepage for authenticated MalLog users.",
};

export default function HomePage() {
  return <HomePageClient />;
}
