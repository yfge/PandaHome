"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import type { PublishedService, ServiceDraft } from "@/types/access";

const INITIAL_DRAFT: ServiceDraft = {
  name: "", local_ip: "", local_port: 8080, public_port: 18080,
  protocol: "TCP", mode: "auto", domain: "", rr: "@", enabled: true, lease_duration: 3600,
};
const selectClass = "border-input bg-background focus-visible:ring-ring/50 h-9 w-full rounded-md border px-3 text-sm outline-none focus-visible:ring-[3px]";

function normalizeDomain(value: string): string {
  if (!value.trim()) return "";
  if (/[/:?#@\s]/.test(value.trim())) return value;
  try { return new URL(`https://${value.trim()}`).hostname.toLowerCase(); }
  catch { return value; }
}

export function validateServiceDraft(draft: ServiceDraft): string | null {
  if (!draft.name.trim()) return "requiredName";
  const parts = draft.local_ip.trim().split(".");
  if (parts.length !== 4 || parts.some((part) => !/^(0|[1-9]\d{0,2})$/.test(part) || Number(part) > 255)) return "invalidIp";
  if (draft.mode !== "relay" && parts[0] === "127") return "loopbackRequiresRelay";
  if (![draft.local_port, draft.public_port].every((port) => Number.isInteger(port) && port >= 1 && port <= 65535)) return "invalidPort";
  const domain = normalizeDomain(draft.domain);
  const rr = draft.rr.trim() || "@";
  if (domain && !/^(?:[a-z\d](?:[a-z\d-]*[a-z\d])?\.)+[a-z](?:[a-z\d-]*[a-z\d])$/i.test(domain)) return "invalidDomain";
  if (domain && rr !== "@" && !/^(?:[a-z\d_](?:[a-z\d_-]*[a-z\d_])?\.)*[a-z\d_](?:[a-z\d_-]*[a-z\d_])?$/i.test(rr)) return "invalidRr";
  if (!Number.isInteger(draft.lease_duration) || (draft.lease_duration !== 0 && draft.lease_duration < 60) || draft.lease_duration > 604800) return "invalidLease";
  return null;
}

export function ServiceForm({ service, busy, error, relayAvailable, onClose, onCloseAutoFocus, onSave }: {
  service: PublishedService | null;
  busy: boolean;
  error: string | null;
  relayAvailable: boolean;
  onClose: () => void;
  onCloseAutoFocus?: (event: Event) => void;
  onSave: (draft: ServiceDraft) => Promise<void>;
}) {
  const t = useTranslations("access");
  const [draft, setDraft] = useState<ServiceDraft>(service ? { ...service } : { ...INITIAL_DRAFT });
  const [validation, setValidation] = useState<string | null>(null);
  const errorRef = useRef<HTMLParagraphElement>(null);
  useEffect(() => {
    if (validation) errorRef.current?.focus();
  }, [validation]);
  useEffect(() => {
    if (error) errorRef.current?.focus();
  }, [error]);
  const update = <K extends keyof ServiceDraft>(key: K, value: ServiceDraft[K]) => {
    setDraft((current) => ({ ...current, [key]: value }));
    setValidation(null);
  };
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const message = validateServiceDraft(draft);
    setValidation(message);
    if (!message) await onSave({
      name: draft.name.trim(),
      local_ip: draft.local_ip.trim(),
      local_port: draft.local_port,
      public_port: draft.public_port,
      protocol: draft.protocol,
      mode: draft.mode,
      domain: normalizeDomain(draft.domain),
      rr: draft.rr.trim() || "@",
      enabled: draft.enabled,
      lease_duration: draft.lease_duration,
    });
  };

  return (
    <Dialog open onOpenChange={(open) => { if (!open && !busy) onClose(); }}>
      <DialogContent className="max-h-[90dvh] overflow-y-auto sm:max-w-xl" onCloseAutoFocus={onCloseAutoFocus}>
        <DialogHeader>
          <DialogTitle>{t(service ? "editService" : "addService")}</DialogTitle>
          <DialogDescription>{t("formDescription")}</DialogDescription>
        </DialogHeader>
        <form className="space-y-5" onSubmit={(event) => void submit(event)} noValidate>
          <fieldset className="space-y-4" disabled={busy}>
            <legend className="sr-only">{t("serviceDetails")}</legend>
            <div className="space-y-1.5">
              <label htmlFor="access-name" className="text-sm font-medium">{t("name")}</label>
              <Input id="access-name" value={draft.name} onChange={(event) => update("name", event.target.value)} placeholder={t("namePlaceholder")} maxLength={80} autoFocus required />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label htmlFor="access-ip" className="text-sm font-medium">{t("localIp")}</label>
                <Input id="access-ip" value={draft.local_ip} onChange={(event) => update("local_ip", event.target.value)} placeholder="192.168.1.10" aria-describedby="access-ip-help" required />
                <p id="access-ip-help" className="text-xs text-muted-foreground">{t("localIpHelp")}</p>
              </div>
              <div className="space-y-1.5">
                <label htmlFor="access-local-port" className="text-sm font-medium">{t("localPort")}</label>
                <Input id="access-local-port" type="number" min={1} max={65535} value={draft.local_port || ""} onChange={(event) => update("local_port", Number(event.target.value))} required />
              </div>
              <div className="space-y-1.5">
                <label htmlFor="access-public-port" className="text-sm font-medium">{t("publicPort")}</label>
                <Input id="access-public-port" type="number" min={1} max={65535} value={draft.public_port || ""} onChange={(event) => update("public_port", Number(event.target.value))} aria-describedby="access-port-help" required />
                <p id="access-port-help" className="text-xs text-muted-foreground">{t("publicPortHelp")}</p>
              </div>
              <div className="space-y-1.5">
                <label htmlFor="access-protocol" className="text-sm font-medium">{t("protocol")}</label>
                <select id="access-protocol" className={selectClass} value={draft.protocol} onChange={(event) => update("protocol", event.target.value as ServiceDraft["protocol"])}>
                  <option value="TCP">TCP</option>
                  <option value="UDP">UDP</option>
                </select>
              </div>
            </div>
            <div className="space-y-2">
              <label htmlFor="access-mode" className="text-sm font-medium">{t("connectionMode")}</label>
              <select id="access-mode" className={selectClass} value={draft.mode} onChange={(event) => update("mode", event.target.value as ServiceDraft["mode"])} aria-describedby="access-mode-help">
                <option value="auto">{t("mode.auto")}</option>
                <option value="direct">{t("mode.direct")}</option>
                <option value="relay">{t("mode.relay")}</option>
              </select>
              <p id="access-mode-help" className="text-xs text-muted-foreground">{t("automaticHelp")}</p>
              {draft.mode === "relay" && !relayAvailable ? <p className="text-sm">{t("relayRequired")}</p> : null}
            </div>
            <details className="rounded-lg border p-4" open={Boolean(service?.domain)}>
              <summary className="cursor-pointer text-sm font-medium">{t("advanced")}</summary>
              <div className="mt-4 space-y-4">
                <p className="text-xs text-muted-foreground">{t("domainHelp")}</p>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <label htmlFor="access-domain" className="text-sm font-medium">{t("domain")}</label>
                    <Input id="access-domain" value={draft.domain} onChange={(event) => update("domain", event.target.value)} placeholder="example.com" />
                  </div>
                  <div className="space-y-1.5">
                    <label htmlFor="access-rr" className="text-sm font-medium">{t("rr")}</label>
                    <Input id="access-rr" value={draft.rr} onChange={(event) => update("rr", event.target.value)} placeholder="home" />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <label htmlFor="access-lease" className="text-sm font-medium">{t("lease")}</label>
                  <Input id="access-lease" type="number" min={0} max={604800} value={draft.lease_duration} onChange={(event) => update("lease_duration", Number(event.target.value))} />
                  <p className="text-xs text-muted-foreground">{t("leaseHelp")}</p>
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={draft.enabled} onChange={(event) => update("enabled", event.target.checked)} className="size-4 accent-primary" />
                  {t("enabled")}
                </label>
              </div>
            </details>
          </fieldset>
          {validation || error ? <p ref={errorRef} role="alert" tabIndex={-1} className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">{validation ? t(`validation.${validation}`) : error}</p> : null}
          <p className="text-xs text-muted-foreground">{t("publishNotice")}</p>
          <DialogFooter>
            <Button type="button" variant="outline" disabled={busy} onClick={onClose}>{t("cancel")}</Button>
            <Button type="submit" disabled={busy}>{t(busy ? "saving" : "save")}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
