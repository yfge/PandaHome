"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { UpnpMappingList } from "@/components/upnp/mapping-list";

export function UpnpPageClient() {
  const t = useTranslations("upnp");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  return (
    <div className="container mx-auto py-10">
      <h1 className="text-4xl font-bold mb-8">{t("title")}</h1>
      <UpnpMappingList />
    </div>
  );
} 