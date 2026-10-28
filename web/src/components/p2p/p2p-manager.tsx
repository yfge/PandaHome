"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { downloadConfiguration, downloadVisitor, P2P_ENDPOINT, p2pRequest, serviceEndpoint, type P2pService, type P2pServiceDraft, type P2pSnapshot } from "@/components/p2p/p2p-api";
import { ServiceCard } from "@/components/p2p/service-card";
import { ServiceForm } from "@/components/p2p/service-form";
import { useP2pTranslations } from "@/components/p2p/translations";
import { getErrorMessage } from "@/lib/api-client";

const REASON_KEYS = {
  p2p_not_configured: "reason_p2p_not_configured",
  p2p_binary_missing: "reason_p2p_binary_missing",
  p2p_process_exited: "reason_p2p_process_exited",
  p2p_start_failed: "reason_p2p_start_failed",
  p2p_stopped: "reason_p2p_stopped",
  p2p_awaiting_connection: "reason_p2p_awaiting_connection",
  p2p_disabled: "reason_p2p_disabled",
  p2p_reconcile_failed: "reason_p2p_reconcile_failed",
} as const;

export function P2pManager() {
  const t = useP2pTranslations();
  const [snapshot, setSnapshot] = useState<P2pSnapshot | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editor, setEditor] = useState<P2pService | "new" | null>(null);
  const lifecycle = useRef<AbortController | null>(null);
  const locked = useRef(false);
  const addButtonRef = useRef<HTMLButtonElement>(null);
  const editorTriggerRef = useRef<HTMLButtonElement | null>(null);
  const restoreEditorFocusRef = useRef(false);

  const closeEditor = () => {
    restoreEditorFocusRef.current = true;
    setEditor(null);
  };

  const openEditor = (value: P2pService | "new", trigger: HTMLButtonElement) => {
    editorTriggerRef.current = trigger;
    setError(null);
    setEditor(value);
  };

  useEffect(() => {
    if (editor || busy || !restoreEditorFocusRef.current) return;
    restoreEditorFocusRef.current = false;
    const trigger = editorTriggerRef.current;
    const target = trigger?.isConnected ? trigger : addButtonRef.current;
    target?.focus({ preventScroll: true });
  }, [editor, busy]);

  const reload = useCallback(async (signal: AbortSignal) => {
    const data = await p2pRequest<P2pSnapshot>(P2P_ENDPOINT, { signal, cache: "no-store" });
    if (!signal.aborted) setSnapshot(data);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    lifecycle.current = controller;
    setBusy(true);
    reload(controller.signal)
      .catch((cause) => { if (!controller.signal.aborted) setError(getErrorMessage(cause, t("failed"))); })
      .finally(() => { if (!controller.signal.aborted) setBusy(false); });
    return () => controller.abort();
  }, [reload, t]);

  const perform = async (action: (signal: AbortSignal) => Promise<unknown>, refresh = true): Promise<boolean> => {
    const signal = lifecycle.current?.signal;
    if (!signal || signal.aborted || locked.current) return false;
    locked.current = true;
    setBusy(true);
    setError(null);
    let performed = false;
    try {
      await action(signal);
      performed = true;
      if (signal.aborted) return false;
      if (refresh) await reload(signal);
      return !signal.aborted;
    } catch (cause) {
      if (!signal.aborted) setError(getErrorMessage(cause, t("failed")));
      return performed && !signal.aborted;
    } finally {
      locked.current = false;
      if (!signal.aborted) setBusy(false);
    }
  };

  const save = async (draft: P2pServiceDraft) => {
    const endpoint = editor && editor !== "new" ? serviceEndpoint(editor.id) : `${P2P_ENDPOINT}/services`;
    const saved = await perform((signal) => p2pRequest(endpoint, {
      method: editor === "new" ? "POST" : "PUT", body: draft, signal,
    }));
    if (saved) closeEditor();
  };

  const provider = snapshot?.provider;
  const providerLabel = !provider?.configured ? "providerSetup" : !provider.available ? "providerUnavailable" : provider.running ? "providerRunning" : "providerStopped";
  const reason = provider?.reason_code;
  const reasonKey = reason && Object.hasOwn(REASON_KEYS, reason) ? REASON_KEYS[reason as keyof typeof REASON_KEYS] : "providerReason";

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="space-y-3 p-6">
          <h2 className="text-lg font-semibold">{t("setupTitle")}</h2>
          <ol className="text-muted-foreground list-decimal space-y-2 pl-5 text-sm">
            <li>{t("setupOne")}</li><li>{t("setupTwo")}</li><li>{t("setupThree")}</li>
          </ol>
          <pre className="bg-muted overflow-x-auto rounded-md p-3 text-sm"><code>frpc -c visitor.toml</code></pre>
          <p className="text-muted-foreground text-sm">{t("setupLimits")}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="space-y-3 p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-lg font-semibold">{t("providerTitle")}</h2>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" disabled={busy} onClick={() => void perform(async () => {}, true)}>{t("reload")}</Button>
              <Button disabled={busy || !!editor} onClick={() => void perform((signal) => p2pRequest(`${P2P_ENDPOINT}/reconcile`, { method: "POST", signal }))}>{t("reconcile")}</Button>
            </div>
          </div>
          {provider ? <p className="text-sm font-medium">{t(providerLabel)}</p> : null}
          {reason ? <p className="text-muted-foreground text-sm">{t(reasonKey)}</p> : null}
          <p className="text-muted-foreground text-sm">{t("providerEvidence")}</p>
          {provider?.ca_required ? <div className="space-y-2">
            <Button variant="outline" disabled={busy} onClick={() => void perform((signal) => downloadConfiguration(`${P2P_ENDPOINT}/ca`, "frps-ca.crt", signal), false)}>{t("downloadCa")}</Button>
            <p className="text-muted-foreground text-sm">{t("caHelp")}</p>
          </div> : null}
        </CardContent>
      </Card>
      {busy ? <p role="status" className="text-muted-foreground text-sm">{t("working")}</p> : null}
      {error && !editor ? <p role="alert" className="text-destructive text-sm">{error}</p> : null}
      {editor ? <ServiceForm key={editor === "new" ? "new" : editor.id} initial={editor === "new" ? undefined : editor}
        busy={busy} error={error} onSave={save} onCancel={() => { setError(null); closeEditor(); }} /> :
        <Button ref={addButtonRef} disabled={busy} onClick={(event) => openEditor("new", event.currentTarget)}>{t("add")}</Button>}
      {snapshot?.services.length === 0 ? <p className="text-muted-foreground text-sm">{t("empty")}</p> : null}
      <div className="grid gap-4 xl:grid-cols-2">
        {snapshot?.services.map((service) => (
          <ServiceCard key={service.id} service={service} busy={busy || !!editor} providerReady={!!provider?.configured && !!provider.available}
            onEdit={(trigger) => openEditor(service, trigger)}
            onToggle={() => void perform((signal) => p2pRequest(serviceEndpoint(service.id), { method: "PUT", body: { name: service.name, local_ip: service.local_ip, local_port: service.local_port, enabled: !service.enabled, fallback_enabled: service.fallback_enabled }, signal }))}
            onDelete={() => void perform((signal) => p2pRequest(serviceEndpoint(service.id), { method: "DELETE", signal }))}
            onRotate={() => void perform((signal) => p2pRequest(`${serviceEndpoint(service.id)}/rotate-key`, { method: "POST", signal }))}
            onDownload={(port) => void perform((signal) => downloadVisitor(service.id, port, signal), false)} />
        ))}
      </div>
    </div>
  );
}
