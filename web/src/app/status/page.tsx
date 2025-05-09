"use client";

import { useTranslations } from "next-intl";
import { ServerStatus } from "@/components/server/status";

export default function StatusPage() {
  const t = useTranslations();

  return (
    <div className="container mx-auto py-10">
      <h1 className="text-4xl font-bold mb-8">{t("server.status")}</h1>
      <ServerStatus />
    </div>
  );
} 