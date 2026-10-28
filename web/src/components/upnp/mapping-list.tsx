"use client";

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type MouseEvent } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { mappingEndpoint } from "@/components/upnp/gateway-api";
import { useGatewayTranslations } from "@/components/upnp/gateway-translations";
import { UpnpMapping } from "@/types/upnp";
import { Clock, Globe, MoreVertical, Network, Plus, Shield } from "lucide-react";
import { DataStateCard } from "@/components/common/data-state-card";
import { ApiClientError, apiClient, getErrorMessage, isApiEnvelope, type ApiEnvelope } from "@/lib/api-client";
import type { AsyncState } from "@/lib/async-state";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useToast } from "@/components/providers/toast-provider";
import { UpnpMappingFormDialog, type UpnpMappingDraft } from "@/components/upnp/mapping-form-dialog";
import { UpnpMappingDeleteDialog } from "@/components/upnp/mapping-delete-dialog";

export function UpnpMappingList({ deviceUrl, onBusyChange }: {
  deviceUrl?: string;
  onBusyChange?: (busy: boolean) => void;
}) {
  const t = useTranslations("upnp");
  const gatewayT = useGatewayTranslations();
  const [state, setState] = useState<AsyncState<UpnpMapping[]>>({ status: "loading" });
  const isUnmountedRef = useRef(false);
  const stateRef = useRef(state);
  const addButtonRef = useRef<HTMLButtonElement>(null);
  const formTriggerRef = useRef<HTMLElement | null>(null);
  const deleteTriggerRef = useRef<HTMLElement | null>(null);
  const pendingFocusRef = useRef<HTMLElement | null>(null);
  const formWasOpenRef = useRef(false);
  const deleteWasOpenRef = useRef(false);

  const { toast } = useToast();

  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<"add" | "edit">("add");
  const [editingMapping, setEditingMapping] = useState<UpnpMapping | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const formInitialValues = useMemo<UpnpMappingDraft | undefined>(() => editingMapping ? {
    description: editingMapping.description,
    internal_ip: editingMapping.internal_ip,
    internal_port: editingMapping.internal_port,
    external_port: editingMapping.external_port,
    protocol: editingMapping.protocol,
    lease_duration: editingMapping.lease_duration,
  } : undefined, [editingMapping]);

  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<UpnpMapping | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const restoreDialogFocus = useCallback((trigger: HTMLElement | null) => {
    if (isUnmountedRef.current) return;
    const target = trigger?.isConnected ? trigger : addButtonRef.current;
    if (target?.matches(':disabled, [aria-disabled="true"], [data-disabled]')) {
      // A successful write may close the dialog before its list refresh ends.
      pendingFocusRef.current = target;
    } else {
      target?.focus({ preventScroll: true });
      pendingFocusRef.current = null;
    }
  }, []);

  useLayoutEffect(() => {
    // Restore during close rendering; a deferred Radix callback must not reset Tab.
    if (formWasOpenRef.current && !formOpen) restoreDialogFocus(formTriggerRef.current);
    if (deleteWasOpenRef.current && !deleteOpen) restoreDialogFocus(deleteTriggerRef.current);
    formWasOpenRef.current = formOpen;
    deleteWasOpenRef.current = deleteOpen;
  }, [formOpen, deleteOpen, restoreDialogFocus]);

  useLayoutEffect(() => {
    if (isSubmitting || isDeleting || !pendingFocusRef.current) return;
    const pending = pendingFocusRef.current;
    pendingFocusRef.current = null;
    // A user who already continued navigation owns the new focus.
    if (document.activeElement !== document.body) return;
    const target = pending.isConnected ? pending : addButtonRef.current;
    target?.focus({ preventScroll: true });
  }, [isSubmitting, isDeleting]);

  useEffect(() => {
    onBusyChange?.(isSubmitting || isDeleting || formOpen || deleteOpen);
    return () => onBusyChange?.(false);
  }, [onBusyChange, isSubmitting, isDeleting, formOpen, deleteOpen]);

  useEffect(() => {
    isUnmountedRef.current = false;
    return () => {
      isUnmountedRef.current = true;
    };
  }, []);

  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  const setSafeState = useCallback(
    (value: AsyncState<UpnpMapping[]>) => {
      if (!isUnmountedRef.current) {
        setState(value);
      }
    },
    []
  );

  const setMappings = useCallback(
    (mappings: UpnpMapping[]) => {
      if (mappings.length === 0) {
        setSafeState({ status: "empty" });
      } else {
        setSafeState({ status: "success", data: mappings });
      }
    },
    [setSafeState],
  );

  const mappingKey = useCallback((mapping: UpnpMapping) => `${mapping.protocol}-${mapping.external_port}`, []);

  const loadMappings = useCallback(
    async (forceLoading = false) => {
      if (forceLoading) {
        setSafeState({ status: "loading" });
      }

      try {
        type MappingResult = { mappings?: UpnpMapping[]; enumeration_supported?: boolean; complete?: boolean };
        const response = await apiClient<MappingResult | ApiEnvelope<MappingResult>>(
          mappingEndpoint(deviceUrl),
        );

        const data = isApiEnvelope<MappingResult>(response) ? response.data : response;
        if (data?.enumeration_supported === false) throw new Error(gatewayT("enumerationUnavailable"));
        if (data?.enumeration_supported === true && data.complete === false) throw new Error(gatewayT("incomplete"));

        let mappings: UpnpMapping[] = [];
        if (isApiEnvelope<{ mappings?: UpnpMapping[] }>(response)) {
          if (response.code !== 0) {
            throw new Error(response.message ?? t("failed"));
          }
          if (Array.isArray(response.data?.mappings)) {
            mappings = response.data.mappings;
          }
        } else if (Array.isArray(response.mappings)) {
          mappings = response.mappings;
        }

        if (mappings.length === 0) {
          setSafeState({ status: "empty" });
          return;
        }

        setSafeState({ status: "success", data: mappings });
      } catch (error) {
        setSafeState({
          status: "error",
          message: getErrorMessage(error, t("failed")),
        });
      }
    },
    [setSafeState, t, deviceUrl, gatewayT]
  );

  const openAddDialog = useCallback((event: MouseEvent<HTMLButtonElement>) => {
    formTriggerRef.current = event.currentTarget;
    setFormMode("add");
    setEditingMapping(null);
    setFormOpen(true);
  }, []);

  const openEditDialog = useCallback((mapping: UpnpMapping, trigger: HTMLElement) => {
    formTriggerRef.current = trigger;
    setFormMode("edit");
    setEditingMapping(mapping);
    setFormOpen(true);
  }, []);

  const requestDelete = useCallback((mapping: UpnpMapping, trigger: HTMLElement) => {
    deleteTriggerRef.current = trigger;
    setDeleteTarget(mapping);
    setDeleteOpen(true);
  }, []);

  const closeDeleteDialog = useCallback((open: boolean) => {
    setDeleteOpen(open);
    if (!open) {
      setDeleteTarget(null);
    }
  }, []);

  const closeFormDialog = useCallback((open: boolean) => {
    setFormOpen(open);
    if (!open) {
      setEditingMapping(null);
      setFormMode("add");
    }
  }, []);

  const createMapping = useCallback(
    async (draft: UpnpMappingDraft) => {
      const payload = {
        external_port: draft.external_port,
        internal_port: draft.internal_port,
        protocol: draft.protocol,
        local_ip: draft.internal_ip,
        description: draft.description,
        lease_duration: draft.lease_duration,
        enabled: true,
      };

      const response = await apiClient<unknown | ApiEnvelope<unknown>>(mappingEndpoint(deviceUrl), {
        method: "POST",
        body: payload,
      });

      if (isApiEnvelope(response) && response.code !== 0) {
        throw new Error(response.message ?? t("failed"));
      }
    },
    [t, deviceUrl],
  );

  const deleteMapping = useCallback(
    async (externalPort: number, protocol: UpnpMapping["protocol"]) => {
      const endpoint = mappingEndpoint(deviceUrl, externalPort, protocol);
      const response = await apiClient<unknown | ApiEnvelope<unknown>>(endpoint, { method: "DELETE" });
      if (isApiEnvelope(response) && response.code !== 0) {
        throw new Error(response.message ?? t("failed"));
      }
    },
    [t, deviceUrl],
  );

  const handleSubmit = useCallback(
    async (draft: UpnpMappingDraft) => {
      const previousState = stateRef.current;
      const optimistic: UpnpMapping = { ...draft, enabled: true };

      setIsSubmitting(true);
      try {
        if (formMode === "add") {
          const current =
            previousState.status === "success"
              ? previousState.data
              : previousState.status === "empty"
                ? []
                : [];
          await createMapping(draft);
          setMappings([optimistic, ...current]);
          toast({ variant: "success", title: t("success"), description: t("toast.addSuccess") });
          closeFormDialog(false);
          await loadMappings();
          return;
        }

        const original = editingMapping;
        if (!original) {
          return;
        }

        const current =
          previousState.status === "success"
            ? previousState.data
            : previousState.status === "empty"
              ? []
              : [];
        const originalKey = mappingKey(original);
        const index = current.findIndex((item) => mappingKey(item) === originalKey);
        const next = [...current];
        if (index >= 0) {
          next[index] = optimistic;
        } else {
          next.unshift(optimistic);
        }
        try {
          await deleteMapping(original.external_port, original.protocol);
        } catch (err) {
          // If the mapping is already gone, still try to add the new one.
          if (!(err instanceof ApiClientError && err.status === 404)) {
            throw err;
          }
        }

        try {
          await createMapping(draft);
        } catch (err) {
          // Best-effort rollback: attempt to restore the original mapping.
          try {
            await createMapping({
              description: original.description,
              internal_ip: original.internal_ip,
              internal_port: original.internal_port,
              external_port: original.external_port,
              protocol: original.protocol,
              lease_duration: original.lease_duration,
            });
          } catch {
            // Ignore rollback failures.
          }
          throw err;
        }

        setMappings(next);
        toast({ variant: "success", title: t("success"), description: t("toast.editSuccess") });
        closeFormDialog(false);
        await loadMappings();
      } catch (error) {
        setSafeState(previousState);
        toast({
          variant: "error",
          title: t("failed"),
          description: getErrorMessage(error, t("failed")),
        });
        throw error;
      } finally {
        setIsSubmitting(false);
      }
    },
    [
      closeFormDialog,
      createMapping,
      deleteMapping,
      editingMapping,
      formMode,
      loadMappings,
      mappingKey,
      setMappings,
      setSafeState,
      t,
      toast,
    ],
  );

  const confirmDelete = useCallback(async () => {
    const target = deleteTarget;
    if (!target) {
      return;
    }

    const previousState = stateRef.current;
    setIsDeleting(true);

    try {
      const current =
        previousState.status === "success"
          ? previousState.data
          : previousState.status === "empty"
            ? []
            : [];
      await deleteMapping(target.external_port, target.protocol);
      setMappings(current.filter((item) => mappingKey(item) !== mappingKey(target)));
      toast({ variant: "success", title: t("success"), description: t("toast.deleteSuccess") });
      closeDeleteDialog(false);
      await loadMappings();
    } catch (error) {
      setSafeState(previousState);
      toast({
        variant: "error",
        title: t("failed"),
        description: getErrorMessage(error, t("failed")),
      });
      throw error;
    } finally {
      setIsDeleting(false);
    }
  }, [closeDeleteDialog, deleteMapping, deleteTarget, loadMappings, mappingKey, setMappings, setSafeState, t, toast]);

  useEffect(() => {
    loadMappings(true);
    const interval = setInterval(() => {
      loadMappings();
    }, 30000);

    return () => clearInterval(interval);
  }, [loadMappings]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-end gap-2">
        <Button ref={addButtonRef} type="button" onClick={openAddDialog} disabled={isSubmitting || isDeleting}>
          <Plus className="h-4 w-4" />
          {t("addMapping")}
        </Button>
      </div>

      {state.status === "loading" ? <MappingListSkeleton /> : null}

      {state.status === "error" ? (
        <DataStateCard
          variant="error"
          title={t("error")}
          description={state.message}
          action={{
            label: t("retry"),
            onClick: () => loadMappings(true),
          }}
        />
      ) : null}

      {state.status === "empty" ? (
        <DataStateCard
          title={t("noMappings")}
          description={t("addMapping")}
          action={{
            label: t("add"),
            onClick: openAddDialog,
          }}
        />
      ) : null}

      {state.status === "success" ? (
        <Card>
          <CardContent className="p-0">
            <div className="divide-y">
              {state.data.map((mapping) => (
                <div
                  key={mappingKey(mapping)}
                  className="flex items-start justify-between gap-3 p-4 transition-colors hover:bg-muted/50 sm:items-center"
                >
                  <div className="flex min-w-0 flex-1 flex-col gap-2 xl:flex-row xl:items-center xl:gap-4">
                    <div className="flex min-w-0 items-start gap-2 xl:min-w-[180px] xl:items-center">
                      <Network className="text-muted-foreground mt-0.5 h-4 w-4 shrink-0 xl:mt-0" />
                      <span className="break-all font-medium">{mapping.description || t("noDescription")}</span>
                    </div>
                    <div className="text-muted-foreground flex items-center gap-2 text-sm">
                      <Globe className="h-4 w-4 shrink-0" />
                      <span className="break-all">
                        {mapping.internal_ip}:{mapping.internal_port}
                      </span>
                    </div>
                    <div className="text-muted-foreground flex items-center gap-2 text-sm">
                      <Shield className="h-4 w-4 shrink-0" />
                      <span>
                        {mapping.protocol}:{mapping.external_port}
                      </span>
                    </div>
                    <div className="text-muted-foreground flex items-center gap-2 text-sm">
                      <Clock className="h-4 w-4 shrink-0" />
                      <span>
                        {mapping.lease_duration === 0
                          ? t("permanent")
                          : `${mapping.lease_duration} ${t("seconds")}`}
                      </span>
                    </div>
                  </div>
                  <div className="flex shrink-0 flex-col items-end gap-2 sm:flex-row sm:items-center">
                    <span
                      className={`rounded-full px-2 py-1 text-xs font-medium ${
                        mapping.enabled ? "bg-emerald-500/10 text-emerald-700" : "bg-destructive/10 text-destructive"
                      }`}
                    >
                      {mapping.enabled ? t("enabled") : t("disabled")}
                    </span>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button type="button" variant="ghost" size="icon" disabled={isSubmitting || isDeleting}
                          aria-label={gatewayT("mappingActions", { description: mapping.description || t("noDescription") })}>
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" onCloseAutoFocus={(event) => {
                        const active = document.activeElement;
                        const menu = event.target;
                        // A delayed menu close must preserve the user's new focus.
                        if (active instanceof HTMLElement && active !== document.body
                          && !active.hasAttribute("data-radix-focus-guard")
                          && !(menu instanceof HTMLElement && menu.contains(active))) {
                          event.preventDefault();
                        }
                      }}>
                        <DropdownMenuItem
                          onSelect={(event) => {
                            event.preventDefault();
                            openEditDialog(mapping, event.currentTarget as HTMLElement);
                          }}
                          disabled={isSubmitting || isDeleting}
                        >
                          {t("edit")}
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          variant="destructive"
                          onSelect={(event) => {
                            event.preventDefault();
                            requestDelete(mapping, event.currentTarget as HTMLElement);
                          }}
                          disabled={isSubmitting || isDeleting}
                        >
                          {t("delete")}
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : null}

      {formOpen ? <UpnpMappingFormDialog
        mode={formMode}
        open={formOpen}
        onOpenChange={closeFormDialog}
        onCloseAutoFocus={(event) => event.preventDefault()}
        initialValues={formInitialValues}
        isSubmitting={isSubmitting}
        onSubmit={handleSubmit}
      /> : null}

      {deleteOpen ? <UpnpMappingDeleteDialog
        open={deleteOpen}
        onOpenChange={closeDeleteDialog}
        onCloseAutoFocus={(event) => event.preventDefault()}
        mapping={deleteTarget}
        isDeleting={isDeleting}
        onConfirm={confirmDelete}
      /> : null}
    </div>
  );
}

function MappingListSkeleton() {
  return (
    <Card>
      <CardContent className="p-0">
        <div className="divide-y">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center justify-between gap-3 p-4">
              <div className="grid min-w-0 flex-1 gap-2 sm:grid-cols-2 xl:grid-cols-4">
                <Skeleton className="h-4 w-[200px] max-w-full" />
                <Skeleton className="h-4 w-32 max-w-full" />
                <Skeleton className="h-4 w-24 max-w-full" />
                <Skeleton className="h-4 w-32 max-w-full" />
              </div>
              <Skeleton className="h-6 w-16" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
