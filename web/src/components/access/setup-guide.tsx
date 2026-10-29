"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RelaySettings } from "@/components/access/relay-settings";

export function AccessSetupGuide() {
  const t = useTranslations("access.setup");
  return (
    <div className="container mx-auto max-w-3xl space-y-6 px-4 py-8">
      <Button variant="ghost" asChild>
        <Link href="/access">
          <ArrowLeft aria-hidden="true" />{t("back")}</Link>
      </Button>
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">{t("title")}</h1>
        <p className="text-muted-foreground">{t("description")}</p>
      </div>
      <RelaySettings />
      <Card>
        <CardHeader>
          <CardTitle>{t("directTitle")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>{t("directBody")}</p>
          <p>{t("directCheck")}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>{t("relayTitle")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <ol className="list-decimal space-y-3 pl-5">
            <li>{t("relayServer")}</li>
            <li>{t("relayClient")}</li>
            <li>{t("relayConfigure")}</li>
            <li>{t("relayRestart")}</li>
          </ol>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>{t("verifyTitle")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>{t("verifyBody")}</p>
          <p>{t("probeBody")}</p>
          <p className="text-muted-foreground">{t("reference")}</p>
        </CardContent>
      </Card>
    </div>
  );
}
