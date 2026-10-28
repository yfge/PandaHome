"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { UpnpMappingList } from "@/components/upnp/mapping-list";
import { UpnpGatewayManager } from "@/components/upnp/gateway-manager";
import { useAuth } from "@/components/providers/auth-provider";

export function UpnpPageClient() {
  const t = useTranslations("upnp");
  const { user } = useAuth();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // This is a safe one-time hydration guard (avoids mismatches while i18n/auth providers bootstrap).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  return (
    <div className="container mx-auto px-4 py-10">
      <h1 className="text-4xl font-bold mb-8">{t("title")}</h1>
      {user?.role === "admin" ? <UpnpGatewayManager /> : <UpnpMappingList />}
    </div>
  );
}
