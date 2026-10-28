"use client";

import { useAuth } from "@/components/providers/auth-provider";
import { P2pManager } from "@/components/p2p/p2p-manager";
import { useP2pTranslations } from "@/components/p2p/translations";

export function P2pPageClient() {
  const { user } = useAuth();
  const t = useP2pTranslations();
  return (
    <div className="container mx-auto space-y-6 px-4 py-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">{t("title")}</h1>
        <p className="text-muted-foreground">{t("description")}</p>
      </div>
      {!user ? <p role="status">{t("loadingProfile")}</p> : user.role === "admin" ? <P2pManager /> : <p>{t("adminRequired")}</p>}
    </div>
  );
}
