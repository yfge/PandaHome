"use client";

import { useCallback, useLayoutEffect, useRef, useEffect, useState } from "react";
import { Plus } from "lucide-react";
import Link from "next/link";
import { useTranslations } from "next-intl";

import { accessRequest } from "@/components/access/access-api";
import { NetworkSummary } from "@/components/access/network-summary";
import { ServiceCard } from "@/components/access/service-card";
import { ServiceForm } from "@/components/access/service-form";
import { useAccessState } from "@/components/access/use-access-state";
import { DataStateCard } from "@/components/common/data-state-card";
import { useToast } from "@/components/providers/toast-provider";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { getErrorMessage } from "@/lib/api-client";
import type { PublishedService, ServiceDraft } from "@/types/access";

export function AccessPageClient() {
  const t = useTranslations("access");
  const { toast } = useToast();
  const { data, error, permissionDenied, reload } = useAccessState();
  const [detecting, setDetecting] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [editing, setEditing] = useState<PublishedService | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<PublishedService | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const actionControllers = useRef(new Set<AbortController>());
  const addButtonRef = useRef<HTMLButtonElement>(null);
  const formTriggerRef = useRef<HTMLElement | null>(null);
  const formWasOpenRef = useRef(false);
  const deleteTriggerRef = useRef<HTMLElement | null>(null);
  const deleteWasOpenRef = useRef(false);

  const focusTrigger = useCallback((trigger: HTMLElement | null) => {
    const target = trigger?.isConnected ? trigger : addButtonRef.current;
    target?.focus({ preventScroll: true });
  }, []);
  useLayoutEffect(() => {
    // Restore before another Tab; Radix's deferred callback must not steal it back.
    if (formWasOpenRef.current && !formOpen) focusTrigger(formTriggerRef.current);
    if (deleteWasOpenRef.current && !deleting) focusTrigger(deleteTriggerRef.current);
    formWasOpenRef.current = formOpen;
    deleteWasOpenRef.current = Boolean(deleting);
  }, [formOpen, deleting, focusTrigger]);

  useEffect(() => {
    const controllers = actionControllers.current;
    return () => { controllers.forEach((controller) => controller.abort()); };
  }, []);

  const request = async <T,>(path: string, method: string, body?: ServiceDraft): Promise<T> => {
    const controller = new AbortController();
    actionControllers.current.add(controller);
    try { return await accessRequest<T>(path, { method, body, signal: controller.signal }); }
    finally { actionControllers.current.delete(controller); }
  };
  const reportError = (cause: unknown) => {
    if (!(cause instanceof DOMException && cause.name === "AbortError")) {
      toast({ title: t("actionFailed"), description: getErrorMessage(cause), variant: "error" });
    }
  };
  const detect = async () => {
    setDetecting(true);
    try { await request("/detect", "POST"); await reload(); }
    catch (cause) { reportError(cause); }
    finally { setDetecting(false); }
  };
  const save = async (draft: ServiceDraft) => {
    setSaving(true);
    setFormError(null);
    try {
      await request(editing ? `/services/${editing.id}` : "/services", editing ? "PUT" : "POST", draft);
      if (!editing) formTriggerRef.current = null;
      setFormOpen(false);
      toast({ title: t("saved"), description: t("savedDescription"), variant: "success" });
      await reload();
    } catch (cause) { if (!(cause instanceof DOMException && cause.name === "AbortError")) setFormError(getErrorMessage(cause)); }
    finally { setSaving(false); }
  };
  const check = async (service: PublishedService) => {
    setBusyId(service.id);
    try { await request(`/services/${service.id}/check`, "POST"); await reload(); }
    catch (cause) { reportError(cause); }
    finally { setBusyId(null); }
  };
  const toggle = async (service: PublishedService) => {
    setBusyId(service.id);
    const draft: ServiceDraft = {
      name: service.name, local_ip: service.local_ip, local_port: service.local_port,
      public_port: service.public_port, protocol: service.protocol, mode: service.mode,
      domain: service.domain, rr: service.rr, enabled: !service.enabled, lease_duration: service.lease_duration,
    };
    try {
      await request(`/services/${service.id}`, "PUT", draft);
      toast({ title: t(service.enabled ? "pauseSaved" : "enableSaved") });
      await reload();
    } catch (cause) { reportError(cause); }
    finally { setBusyId(null); }
  };
  const remove = async () => {
    if (!deleting) return;
    setBusyId(deleting.id);
    setDeleteError(null);
    try {
      await request(`/services/${deleting.id}`, "DELETE");
      deleteTriggerRef.current = null;
      setDeleting(null);
      toast({ title: t("deleted"), variant: "success" });
      await reload();
    } catch (cause) { if (!(cause instanceof DOMException && cause.name === "AbortError")) setDeleteError(getErrorMessage(cause)); }
    finally { setBusyId(null); }
  };
  const openForm = (service: PublishedService | null, trigger: HTMLElement | null) => {
    formTriggerRef.current = trigger;
    setEditing(service);
    setFormError(null);
    setFormOpen(true);
  };

  return (
    <div className="container mx-auto max-w-6xl space-y-8 px-4 py-8 sm:py-10">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div className="max-w-2xl space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">{t("title")}</h1>
          <p className="text-muted-foreground">{t("description")}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" asChild><Link href="/access/setup">{t("configureRelay")}</Link></Button>
          <Button ref={addButtonRef} onClick={(event) => openForm(null, event.currentTarget)} disabled={!data}>
            <Plus aria-hidden="true" />{t("addService")}</Button>
        </div>
      </header>
      {error ? <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm">
        <div>
          <p className="font-medium">{t(permissionDenied ? "adminOnly" : data ? "staleState" : "loadFailed")}</p>
          <p className="text-muted-foreground">{permissionDenied ? t("adminDescription") : error}</p>
        </div>
        <Button variant="outline" onClick={() => void reload()}>{t("retry")}</Button>
      </div> : null}
      {!data && !error ? <div role="status" aria-label={t("loading")} className="space-y-5">
        <Skeleton className="h-60 w-full" />
        <Skeleton className="h-40 w-full" />
        <span className="sr-only">{t("loading")}</span>
      </div> : null}
      {data ? <>
        <NetworkSummary state={data} detecting={detecting} onDetect={() => void detect()} />
        <section aria-labelledby="access-services-title" className="space-y-4">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h2 id="access-services-title" className="text-xl font-semibold">{t("servicesTitle")}</h2>
            <p className="text-xs text-muted-foreground">{t("maintenanceNote", { seconds: data.poll_interval_seconds })}</p>
          </div>
          {data.services.length ? (
            <div className="grid items-start gap-4 lg:grid-cols-2">
              {data.services.map((service) => (
                <ServiceCard
                  key={service.id}
                  service={service}
                  busy={busyId !== null}
                  onEdit={(event) => openForm(service, event.currentTarget)}
                  onDelete={(event) => {
                    deleteTriggerRef.current = event.currentTarget;
                    setDeleting(service);
                    setDeleteError(null);
                  }}
                  onCheck={() => void check(service)}
                  onToggle={() => void toggle(service)}
                />
              ))}
            </div>
          ) : (
            <DataStateCard
              title={t("emptyTitle")}
              description={t("emptyDescription")}
              action={{ label: t("addService"), onClick: (event) => openForm(null, event.currentTarget) }}
            />
          )}
        </section>
      </> : null}
      {formOpen ? <ServiceForm service={editing} busy={saving} error={formError} relayAvailable={data?.relay.available ?? false} onClose={() => setFormOpen(false)} onCloseAutoFocus={(event) => event.preventDefault()} onSave={save} /> : null}
      {deleting ? <Dialog open onOpenChange={(open) => { if (!open && busyId === null) setDeleting(null); }}>
        <DialogContent onCloseAutoFocus={(event) => event.preventDefault()}>
          <DialogHeader>
            <DialogTitle>{t("deleteTitle")}</DialogTitle>
            <DialogDescription>{t("deleteDescription", { name: deleting?.name ?? "" })}</DialogDescription>
          </DialogHeader>{deleteError ? <p role="alert" className="text-sm text-destructive">{deleteError}</p> : null}<DialogFooter>
            <Button variant="outline" disabled={busyId !== null} onClick={() => setDeleting(null)}>{t("cancel")}</Button>
            <Button variant="destructive" disabled={busyId !== null} onClick={() => void remove()}>{t(busyId !== null ? "deleting" : "delete")}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog> : null}
    </div>
  );
}
