"use client";

import { useTranslations } from "next-intl";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/components/providers/auth-provider";

export default function HomePage() {
  const t = useTranslations("common");
  const { token } = useAuth();

  return (
    <div className="container mx-auto py-10">
      <div className="flex flex-col items-center justify-center space-y-8 text-center">
        <h1 className="text-4xl font-bold">{t("welcome")}</h1>
        <p className="text-xl text-muted-foreground">{t("description")}</p>
        <div className="flex space-x-4">
          {token ? (
            <>
              <Link href="/status">
                <Button size="lg">{t("viewStatus")}</Button>
              </Link>
              <Link href="/upnp">
                <Button size="lg" variant="outline">
                  {t("manageServices")}
                </Button>
              </Link>
            </>
          ) : (
            <Link href="/login">
              <Button size="lg">{t("login")}</Button>
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
