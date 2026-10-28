"use client";

import { Copy, Pencil, RefreshCw, ShieldCheck, Trash2 } from "lucide-react";
import { useFormatter, useTranslations } from "next-intl";

import { useToast } from "@/components/providers/toast-provider";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { PublishedService } from "@/types/access";

export function serviceDisplayStatus(service: PublishedService): string {
  if (service.status === "healthy" && !service.external_verified) return "configured";
  if (service.status === "pending" && service.public_endpoint
    && ["inbound_unverified", "relay_unverified"].includes(service.reason_code ?? "")) return "configured";
  return service.status;
}

export function ServiceCard({ service, busy, onEdit, onDelete, onCheck }: {
  service: PublishedService;
  busy: boolean;
  onEdit: () => void;
  onDelete: () => void;
  onCheck: () => void;
}) {
  const t = useTranslations("access");
  const format = useFormatter();
  const { toast } = useToast();
  const status = serviceDisplayStatus(service);
  const reasonKey = service.reason_code ? `reasons.${service.reason_code}` : "";
  const reason = reasonKey && t.has(reasonKey) ? t(reasonKey) : service.last_error;
  const evidenceReason = ["inbound_unverified", "relay_unverified", "ready"].includes(service.reason_code ?? "");
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(service.public_endpoint!);
      toast({ title: t("copied"), variant: "success" });
    } catch {
      toast({ title: t("copyFailed"), description: t("copyManually"), variant: "error" });
    }
  };

  return (
    <Card>
      <CardHeader className="gap-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <CardTitle className="min-w-0 break-words leading-normal">{service.name}</CardTitle>
          <span className={cn("rounded-full bg-muted px-3 py-1 text-xs font-medium", (status === "error" || status === "degraded") && "bg-destructive/10 text-destructive", status === "healthy" && "bg-primary/10 text-primary")}>
            {t(`status.${status}`)}
          </span>
        </div>
        <p className="break-all text-sm text-muted-foreground">{service.local_ip}:{service.local_port} · {service.protocol} · {t(`mode.${service.active_mode ?? service.mode}`)}</p>
      </CardHeader>
      <CardContent className="space-y-4">
        {service.public_endpoint ? (
          <div className="flex items-center justify-between gap-2 rounded-lg bg-muted p-3">
            <code className="min-w-0 break-all text-sm select-all">{service.public_endpoint}</code>
            <Button variant="ghost" size="icon" aria-label={t("copyEndpoint", { name: service.name })} onClick={() => void copy()}>
              <Copy aria-hidden="true" />
            </Button>
          </div>
        ) : <p className="text-sm text-muted-foreground">{t("endpointPending")}</p>}
        {service.enabled && service.public_endpoint ? (
          <p className="flex items-start gap-2 text-sm text-muted-foreground">
            <ShieldCheck aria-hidden="true" className="mt-0.5 size-4 shrink-0" />{evidenceReason && reason ? reason : t(service.external_verified ? "verified" : "notVerified")}</p>
        ) : null}
        {reason && (!evidenceReason || !service.public_endpoint) ? <p role="status" className="rounded-lg border p-3 text-sm">{reason}</p> : null}
        {service.domain ? <p className="break-all text-xs text-muted-foreground">{t("dnsStatus", { name: `${service.rr === "@" ? "" : `${service.rr}.`}${service.domain}`, status: t.has(`dns.${service.dns_status}`) ? t(`dns.${service.dns_status}`) : t("dns.pending") })}</p> : null}
        {service.last_checked ? <p className="text-xs text-muted-foreground">{t("checkedAt", { time: format.dateTime(new Date(service.last_checked), { dateStyle: "short", timeStyle: "short" }) })}</p> : null}
        <div className="flex flex-wrap gap-2 border-t pt-4">
          <Button variant="outline" size="sm" disabled={busy || !service.enabled} onClick={onCheck}>
            <RefreshCw aria-hidden="true" />{t("check")}</Button>
          <Button variant="ghost" size="sm" disabled={busy} onClick={onEdit}>
            <Pencil aria-hidden="true" />{t("edit")}</Button>
          <Button variant="ghost" size="sm" disabled={busy} onClick={onDelete} className="ml-auto text-destructive">
            <Trash2 aria-hidden="true" />{t("delete")}</Button>
        </div>
      </CardContent>
    </Card>
  );
}
