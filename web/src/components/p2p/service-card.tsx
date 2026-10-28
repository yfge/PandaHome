"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { type P2pService } from "@/components/p2p/p2p-api";
import { useP2pTranslations } from "@/components/p2p/translations";

interface ServiceCardProps {
  service: P2pService;
  busy: boolean;
  providerReady: boolean;
  onEdit: () => void;
  onToggle: () => void;
  onDelete: () => void;
  onRotate: () => void;
  onDownload: (port: number) => void;
}

export function ServiceCard({ service, busy, providerReady, onEdit, onToggle, onDelete, onRotate, onDownload }: ServiceCardProps) {
  const t = useP2pTranslations();
  const [bindPort, setBindPort] = useState("18080");
  const [confirmation, setConfirmation] = useState<"delete" | "rotate" | null>(null);
  const port = Number(bindPort);
  const portValid = Number.isInteger(port) && port >= 1 && port <= 65535;
  const id = `p2p-visitor-${service.id}`;

  return (
    <Card>
      <CardContent className="space-y-4 p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 space-y-1">
            <h3 className="break-words font-semibold">{service.name}</h3>
            <p className="text-muted-foreground break-all text-sm">{t("destination", { address: service.local_ip, port: service.local_port })}</p>
          </div>
          <span className="bg-muted rounded-md px-2 py-1 text-xs font-medium">{t(service.status)}</span>
        </div>
        <p className="text-muted-foreground text-sm">{t("unknownPath")} · {t(service.fallback_enabled ? "relayOn" : "relayOff")}</p>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" disabled={busy} onClick={onEdit}>{t("edit")}</Button>
          <Button variant="outline" size="sm" disabled={busy} onClick={onToggle}>{t(service.enabled ? "disable" : "enable")}</Button>
          <Button variant="outline" size="sm" disabled={busy} onClick={() => setConfirmation("rotate")}>{t("rotate")}</Button>
          <Button variant="destructive" size="sm" disabled={busy} onClick={() => setConfirmation("delete")}>{t("delete")}</Button>
        </div>
        {confirmation ? (
          <div className="bg-muted space-y-3 rounded-md p-3" role="group" aria-label={t(confirmation === "delete" ? "deleteConfirm" : "rotateConfirm")}>
            <p className="text-sm">{t(confirmation === "delete" ? "deleteConfirm" : "rotateConfirm")}</p>
            <div className="flex gap-2">
              <Button variant={confirmation === "delete" ? "destructive" : "default"} size="sm" disabled={busy}
                onClick={() => { if (confirmation === "delete") onDelete(); else onRotate(); setConfirmation(null); }}>
                {t(confirmation === "delete" ? "deleteAction" : "rotateAction")}
              </Button>
              <Button variant="outline" size="sm" disabled={busy} onClick={() => setConfirmation(null)}>{t("cancel")}</Button>
            </div>
          </div>
        ) : null}
        <form className="space-y-3 border-t pt-4" onSubmit={(event) => { event.preventDefault(); if (portValid) onDownload(port); }}>
          <h4 className="text-sm font-medium">{t("visitorTitle")}</h4>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <div className="grid gap-2">
              <label htmlFor={id} className="text-sm">{t("bindPort")}</label>
              <Input id={id} type="number" required min={1} max={65535} step={1} value={bindPort}
                disabled={busy} aria-describedby={`${id}-help`} aria-invalid={!portValid}
                onChange={(event) => setBindPort(event.target.value)} />
            </div>
            <Button type="submit" variant="outline" disabled={busy || !providerReady || !service.enabled || !portValid}>{t("download")}</Button>
          </div>
          {!portValid ? <p role="alert" className="text-destructive text-sm">{t("portInvalid")}</p> : null}
          <p id={`${id}-help`} className="text-muted-foreground text-sm">{t("downloadHelp")}</p>
          {portValid ? <p className="text-muted-foreground text-sm">{t("visitorAddress", { port })}</p> : null}
        </form>
      </CardContent>
    </Card>
  );
}
