"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { useTranslations } from "next-intl";

import { accessRequest } from "@/components/access/access-api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiClientError, getErrorMessage } from "@/lib/api-client";
import type { RelayConfigDraft, RelayConfigView, RelayConfigWrite } from "@/types/access";

function editable(config: RelayConfigView): RelayConfigDraft {
  return {
    server_addr: config.server_addr, server_port: config.server_port, public_host: config.public_host,
    binary: config.binary, tls_trusted_ca_file: config.tls_trusted_ca_file, tls_server_name: config.tls_server_name,
    ssh_enabled: config.ssh_enabled, ssh_host: config.ssh_host, ssh_port: config.ssh_port, ssh_user: config.ssh_user,
    ssh_identity_file: config.ssh_identity_file, ssh_known_hosts_file: config.ssh_known_hosts_file,
    ssh_local_port: config.ssh_local_port, ssh_binary: config.ssh_binary,
  };
}

export function RelaySettings() {
  const t = useTranslations("access.relaySettings");
  const [config, setConfig] = useState<RelayConfigView | null>(null);
  const [draft, setDraft] = useState<RelayConfigDraft | null>(null);
  const [token, setToken] = useState("");
  const [clearToken, setClearToken] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorAttempt, setErrorAttempt] = useState(0);
  const [denied, setDenied] = useState(false);
  const requestRef = useRef<AbortController | null>(null);
  const errorRef = useRef<HTMLParagraphElement>(null);
  const sshRef = useRef<HTMLDetailsElement>(null);
  const showError = useCallback((message: string) => {
    setError(message);
    setErrorAttempt((attempt) => attempt + 1);
  }, []);

  const load = useCallback(async () => {
    requestRef.current?.abort();
    const controller = new AbortController();
    requestRef.current = controller;
    setLoading(true);
    setError(null);
    try {
      const result = await accessRequest<RelayConfigView>("/relay-config", { signal: controller.signal });
      if (controller.signal.aborted) return;
      setConfig(result);
      setDraft(editable(result));
      setDenied(false);
    } catch (cause) {
      if (!controller.signal.aborted) {
        setDenied(cause instanceof ApiClientError && cause.status === 403);
        showError(getErrorMessage(cause));
      }
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  }, [showError]);

  useEffect(() => {
    void load();
    return () => requestRef.current?.abort();
  }, [load]);
  useEffect(() => { if (error) errorRef.current?.focus(); }, [error, errorAttempt]);

  const update = <K extends keyof RelayConfigDraft>(key: K, value: RelayConfigDraft[K]) => {
    setDraft((current) => current ? { ...current, [key]: value } : current);
    setSaved(false);
  };
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!draft || saving) return;
    setError(null);
    setSaved(false);
    const validPort = (port: number, allowZero = false) => Number.isInteger(port) && port >= (allowZero ? 0 : 1) && port <= 65535;
    if (!draft.server_addr.trim() || !draft.binary.trim() || !validPort(draft.server_port)) {
      showError(t("invalidRelay"));
      return;
    }
    if (draft.ssh_enabled && (!draft.public_host.trim() || !draft.ssh_host.trim() || !draft.ssh_user.trim()
      || !draft.ssh_identity_file.trim() || !draft.ssh_known_hosts_file.trim()
      || !validPort(draft.ssh_port) || !validPort(draft.ssh_local_port, true))) {
      if (sshRef.current) sshRef.current.open = true;
      showError(t("invalidSsh"));
      return;
    }
    const body: RelayConfigWrite = { ...draft };
    if (clearToken) body.clear_token = true;
    else if (token) body.token = token;
    requestRef.current?.abort();
    const controller = new AbortController();
    requestRef.current = controller;
    setSaving(true);
    try {
      const result = await accessRequest<RelayConfigView>("/relay-config", { method: "PUT", body, signal: controller.signal });
      if (controller.signal.aborted) return;
      setConfig(result);
      setDraft(editable(result));
      setToken("");
      setClearToken(false);
      setSaved(true);
    } catch (cause) {
      if (!controller.signal.aborted) showError(getErrorMessage(cause));
    } finally {
      if (!controller.signal.aborted) setSaving(false);
    }
  };

  const textField = (key: Exclude<keyof RelayConfigDraft, "ssh_enabled">, label: string, help?: string, numeric = false, zero = false) => (
    <div className="min-w-0 space-y-1.5">
      <label htmlFor={`relay-${key}`} className="text-sm font-medium">{label}</label>
      <Input id={`relay-${key}`} type={numeric ? "number" : "text"} value={draft?.[key] ?? ""}
        onChange={(event) => update(key, numeric ? Number(event.target.value) : event.target.value)}
        min={numeric ? (zero ? 0 : 1) : undefined} max={numeric ? 65535 : undefined}
        autoComplete="off" spellCheck={false} aria-describedby={help ? `relay-${key}-help` : undefined} />
      {help ? <p id={`relay-${key}-help`} className="text-xs text-muted-foreground">{help}</p> : null}
    </div>
  );

  return (
    <Card>
      <CardHeader className="space-y-2">
        <CardTitle>{t("title")}</CardTitle>
        <CardDescription>{t("description")}</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? <div role="status" aria-label={t("loading")} className="space-y-4"><Skeleton className="h-10 w-full" /><Skeleton className="h-10 w-full" /><Skeleton className="h-10 w-2/3" /></div> : !draft ? (
          <div className="space-y-3">
            <p role="alert" className="rounded-lg border p-3 text-sm">{denied ? t("adminOnly") : error || t("loadFailed")}</p>
            <Button variant="outline" onClick={() => void load()}>{t("retry")}</Button>
          </div>
        ) : (
          <form onSubmit={(event) => void submit(event)} className="space-y-6" noValidate aria-busy={saving}>
            <fieldset disabled={saving} className="min-w-0 space-y-5">
              <legend className="sr-only">{t("title")}</legend>
              <p className="text-xs text-muted-foreground">{t(config?.source === "managed" ? "savedSource" : "defaultSource")}</p>
              <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_9rem]">
                {textField("server_addr", t("serverAddress"), t(draft.ssh_enabled ? "serverSshHelp" : "serverHelp"))}
                {textField("server_port", t("serverPort"), undefined, true)}
              </div>
              {textField("public_host", t("publicHost"), t("publicHostHelp"))}
              <div className="space-y-2">
                <label htmlFor="relay-token" className="text-sm font-medium">{t("token")}</label>
                <Input id="relay-token" type="password" value={token} autoComplete="new-password" disabled={clearToken}
                  onChange={(event) => { setToken(event.target.value); setSaved(false); }} aria-describedby="relay-token-help" />
                <p id="relay-token-help" className="text-xs text-muted-foreground">{t(config?.has_token ? "tokenSaved" : "tokenHelp")}</p>
                {config?.has_token ? <label className="flex items-start gap-2 text-sm">
                  <input type="checkbox" checked={clearToken} className="mt-1 size-4 shrink-0 accent-primary"
                    onChange={(event) => { setClearToken(event.target.checked); setToken(""); setSaved(false); }} />{t("removeToken")}
                </label> : null}
                {clearToken ? <p className="text-sm text-destructive">{t("removeTokenWarning")}</p> : null}
              </div>
              <div className="space-y-4 rounded-lg border p-4">
                <div><h3 className="text-sm font-medium">{t("tlsTitle")}</h3><p className="mt-1 text-xs text-muted-foreground">{t("tlsHelp")}</p></div>
                {textField("tls_trusted_ca_file", t("caFile"), t("caHelp"))}
                {textField("tls_server_name", t("serverName"), t("serverNameHelp"))}
              </div>
              <details ref={sshRef} className="rounded-lg border p-4">
                <summary className="cursor-pointer text-sm font-medium">{t("sshTitle")} · {t(draft.ssh_enabled ? "sshOn" : "sshOff")}</summary>
                <div className="mt-4 space-y-4">
                  <p className="text-xs text-muted-foreground">{t("sshHelp")}</p>
                  <label className="flex items-center gap-2 text-sm"><input type="checkbox" className="size-4 accent-primary" checked={draft.ssh_enabled}
                    onChange={(event) => update("ssh_enabled", event.target.checked)} />{t("sshEnabled")}</label>
                  {draft.ssh_enabled ? <div className="space-y-4">
                    <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_9rem]">
                      {textField("ssh_host", t("sshHost"))}{textField("ssh_port", t("sshPort"), undefined, true)}
                    </div>
                    {textField("ssh_user", t("sshUser"))}
                    {textField("ssh_identity_file", t("sshIdentity"), t("sshIdentityHelp"))}
                    {textField("ssh_known_hosts_file", t("sshKnownHosts"), t("sshKnownHostsHelp"))}
                    {textField("ssh_local_port", t("sshLocalPort"), t("sshLocalPortHelp"), true, true)}
                  </div> : null}
                </div>
              </details>
              <details className="rounded-lg border p-4">
                <summary className="cursor-pointer text-sm font-medium">{t("advanced")}</summary>
                <div className="mt-4 space-y-4">
                  {textField("binary", t("binary"), t("binaryHelp"))}
                  {textField("ssh_binary", t("sshBinary"))}
                </div>
              </details>
            </fieldset>
            <p className="text-sm text-muted-foreground">{t("applyNotice")}</p>
            {error ? <p ref={errorRef} role="alert" tabIndex={-1} className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">{error}</p> : null}
            {saved ? <p role="status" className="rounded-lg bg-muted p-3 text-sm">{t("saved")}</p> : null}
            <div className="flex flex-wrap items-center gap-3">
              <Button type="submit" disabled={saving}>{t(saving ? "saving" : "save")}</Button>
              <Button type="button" variant="outline" asChild><Link href="/access">{t("viewServices")}</Link></Button>
            </div>
          </form>
        )}
      </CardContent>
    </Card>
  );
}
