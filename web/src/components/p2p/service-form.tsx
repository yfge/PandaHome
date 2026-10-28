"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { type P2pServiceDraft } from "@/components/p2p/p2p-api";
import { useP2pTranslations } from "@/components/p2p/translations";

interface ServiceFormProps {
  initial?: P2pServiceDraft;
  busy: boolean;
  error?: string | null;
  onSave: (draft: P2pServiceDraft) => Promise<void>;
  onCancel: () => void;
}

export function ServiceForm({ initial, busy, error, onSave, onCancel }: ServiceFormProps) {
  const t = useP2pTranslations();
  const errorRef = useRef<HTMLParagraphElement>(null);
  useEffect(() => {
    if (error) errorRef.current?.focus();
  }, [error]);
  const [draft, setDraft] = useState<P2pServiceDraft>(initial ?? {
    name: "", local_ip: "127.0.0.1", local_port: 8080, enabled: true, fallback_enabled: true,
  });
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void onSave({ ...draft, name: draft.name.trim(), local_ip: draft.local_ip.trim() });
  };
  return (
    <form onSubmit={submit} className="bg-muted/40 space-y-4 rounded-lg border p-4">
      <h3 className="font-semibold">{t("formTitle")}</h3>
      <fieldset disabled={busy} className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="grid gap-2">
            <label htmlFor="p2p-name" className="text-sm font-medium">{t("name")}</label>
            <Input id="p2p-name" required maxLength={80} value={draft.name}
              onChange={(event) => setDraft({ ...draft, name: event.target.value })} />
          </div>
          <div className="grid gap-2">
            <label htmlFor="p2p-local-port" className="text-sm font-medium">{t("localPort")}</label>
            <Input id="p2p-local-port" type="number" min={1} max={65535} step={1} required value={draft.local_port || ""}
              onChange={(event) => setDraft({ ...draft, local_port: Number(event.target.value) })} />
          </div>
          <div className="grid gap-2 sm:col-span-2">
            <label htmlFor="p2p-local-ip" className="text-sm font-medium">{t("localIp")}</label>
            <Input id="p2p-local-ip" required inputMode="decimal" value={draft.local_ip}
              pattern="(?:(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])"
              aria-describedby="p2p-local-ip-help"
              onChange={(event) => setDraft({ ...draft, local_ip: event.target.value })} />
            <p id="p2p-local-ip-help" className="text-muted-foreground text-sm">{t("localIpHelp")}</p>
          </div>
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={draft.enabled} onChange={(event) => setDraft({ ...draft, enabled: event.target.checked })} />
          {t("enabled")}
        </label>
        <div className="space-y-1">
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={draft.fallback_enabled} aria-describedby="p2p-fallback-help"
              onChange={(event) => setDraft({ ...draft, fallback_enabled: event.target.checked })} />
            {t("fallback")}
          </label>
          <p id="p2p-fallback-help" className="text-muted-foreground text-sm">{t("fallbackHelp")}</p>
        </div>
        {error ? <p ref={errorRef} role="alert" tabIndex={-1} className="text-destructive rounded-md border border-destructive/30 p-3 text-sm">{error}</p> : null}
        <div className="flex flex-wrap gap-2">
          <Button type="submit" disabled={!draft.name.trim()}>{busy ? t("working") : t("save")}</Button>
          <Button type="button" variant="outline" onClick={onCancel}>{t("cancel")}</Button>
        </div>
      </fieldset>
    </form>
  );
}
