"use client";

import { Globe, RefreshCw, Router } from "lucide-react";
import Link from "next/link";
import { useFormatter, useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { AccessState } from "@/types/access";

export function NetworkSummary({ state, detecting, onDetect }: {
  state: AccessState;
  detecting: boolean;
  onDetect: () => void;
}) {
  const t = useTranslations("access");
  const format = useFormatter();
  const { network, relay } = state;
  const recommendation = network?.recommended_mode ?? "unknown";
  const needsRelay = recommendation === "relay" || state.services.some((service) =>
    service.enabled && (service.mode === "relay" || service.reason_code === "relay_not_configured")
  );
  return (
    <Card>
      <CardHeader className="gap-4 sm:flex sm:flex-row sm:justify-between">
        <div className="space-y-2">
          <CardTitle className="flex items-center gap-2">
            <Router aria-hidden="true" className="size-5" />{t("networkTitle")}</CardTitle>
          <CardDescription>{t("networkDescription")}</CardDescription>
        </div>
        <Button variant="outline" disabled={detecting} onClick={onDetect}>
          <RefreshCw aria-hidden="true" className={detecting ? "animate-spin" : ""} />
          {t(detecting ? "detecting" : "detect")}
        </Button>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid grid-cols-2 gap-5">
          <div>
            <p className="text-sm text-muted-foreground">{t("networkType")}</p>
            <p className="mt-1 font-medium">{t(`topology.${network?.topology ?? "unknown"}`)}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">{t("recommended")}</p>
            <p className="mt-1 font-medium">{t(`recommendation.${recommendation}`)}</p>
          </div>
        </div>
        <p className="text-sm text-muted-foreground">{t(`networkHelp.${recommendation}`)}</p>
        {network && !network.upnp_available ? <p className="rounded-lg bg-muted p-3 text-sm">{t("upnpMissing")}</p> : null}
        {needsRelay && !relay.available ? (
          <div className="space-y-2 rounded-lg border p-4">
            <h3 className="flex items-center gap-2 font-medium">
              <Globe aria-hidden="true" className="size-4" />{t("relaySetupTitle")}</h3>
            <p className="text-sm text-muted-foreground">{t("relaySetupDescription")}</p>
            <Button variant="outline" size="sm" asChild>
              <Link href="/access/setup">{t("openSetupGuide")}</Link>
            </Button>
          </div>
        ) : null}
        <details className="border-t pt-4 text-xs text-muted-foreground">
          <summary className="cursor-pointer font-medium">{t("networkDetails")}</summary>
          <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2">
            <span>{t("observedIp")}: <span className="font-mono">{network?.observed_public_ip || t("notAvailable")}</span>
            </span>
            <span>{t("directAvailability", { state: t(network?.upnp_available ? "available" : "unavailable") })}</span>
            <span>{t("relayAvailability", { state: t(relay.available ? "available" : "unavailable") })}</span>
            {network ? <span>{t("checkedAt", { time: format.dateTime(new Date(network.checked_at), { dateStyle: "short", timeStyle: "short" }) })}</span> : null}
          </div>
          <p className="mt-3">{t("detectionLimit")}</p>
        </details>
      </CardContent>
    </Card>
  );
}
