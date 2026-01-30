"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { API_ENDPOINTS } from "@/config/api";
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

export function UpnpMappingList() {
  const t = useTranslations("upnp");
  const [state, setState] = useState<AsyncState<UpnpMapping[]>>({ status: "loading" });
  const isUnmountedRef = useRef(false);
  const stateRef = useRef(state);

  const { toast } = useToast();

  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<"add" | "edit">("add");
  const [editingMapping, setEditingMapping] = useState<UpnpMapping | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<UpnpMapping | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

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
        const response = await apiClient<{ mappings?: UpnpMapping[] } | ApiEnvelope<{ mappings?: UpnpMapping[] }>>(
          API_ENDPOINTS.upnpMappings,
        );

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
    [setSafeState, t]
  );

  const openAddDialog = useCallback(() => {
    setFormMode("add");
    setEditingMapping(null);
    setFormOpen(true);
  }, []);

  const openEditDialog = useCallback((mapping: UpnpMapping) => {
    setFormMode("edit");
    setEditingMapping(mapping);
    setFormOpen(true);
  }, []);

  const requestDelete = useCallback((mapping: UpnpMapping) => {
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

      const response = await apiClient<unknown | ApiEnvelope<unknown>>(API_ENDPOINTS.upnpMappings, {
        method: "POST",
        body: payload,
      });

      if (isApiEnvelope(response) && response.code !== 0) {
        throw new Error(response.message ?? t("failed"));
      }
    },
    [t],
  );

  const deleteMapping = useCallback(
    async (externalPort: number, protocol: UpnpMapping["protocol"]) => {
      const endpoint = `${API_ENDPOINTS.upnpMappings}/${externalPort}?protocol=${encodeURIComponent(protocol)}`;
      const response = await apiClient<unknown | ApiEnvelope<unknown>>(endpoint, { method: "DELETE" });
      if (isApiEnvelope(response) && response.code !== 0) {
        throw new Error(response.message ?? t("failed"));
      }
    },
    [t],
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
          setMappings([optimistic, ...current]);

          await createMapping(draft);
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
        setMappings(next);

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
      setMappings(current.filter((item) => mappingKey(item) !== mappingKey(target)));

      await deleteMapping(target.external_port, target.protocol);
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
        <Button type="button" onClick={openAddDialog} disabled={isSubmitting || isDeleting}>
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
                  className="flex items-center justify-between gap-3 p-4 transition-colors hover:bg-muted/50"
                >
                  <div className="flex flex-1 items-center gap-4">
                    <div className="flex min-w-[180px] items-center gap-2">
                      <Network className="text-muted-foreground h-4 w-4" />
                      <span className="font-medium">{mapping.description || t("noDescription")}</span>
                    </div>
                    <div className="text-muted-foreground flex items-center gap-2 text-sm">
                      <Globe className="h-4 w-4" />
                      <span>
                        {mapping.internal_ip}:{mapping.internal_port}
                      </span>
                    </div>
                    <div className="text-muted-foreground flex items-center gap-2 text-sm">
                      <Shield className="h-4 w-4" />
                      <span>
                        {mapping.protocol}:{mapping.external_port}
                      </span>
                    </div>
                    <div className="text-muted-foreground flex items-center gap-2 text-sm">
                      <Clock className="h-4 w-4" />
                      <span>
                        {mapping.lease_duration === 0
                          ? t("permanent")
                          : `${mapping.lease_duration} ${t("seconds")}`}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded-full px-2 py-1 text-xs font-medium ${
                        mapping.enabled ? "bg-emerald-500/10 text-emerald-700" : "bg-destructive/10 text-destructive"
                      }`}
                    >
                      {mapping.enabled ? t("enabled") : t("disabled")}
                    </span>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button type="button" variant="ghost" size="icon" disabled={isSubmitting || isDeleting}>
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onSelect={(event) => {
                            event.preventDefault();
                            openEditDialog(mapping);
                          }}
                          disabled={isSubmitting || isDeleting}
                        >
                          {t("edit")}
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          variant="destructive"
                          onSelect={(event) => {
                            event.preventDefault();
                            requestDelete(mapping);
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

      <UpnpMappingFormDialog
        mode={formMode}
        open={formOpen}
        onOpenChange={closeFormDialog}
        initialValues={
          formMode === "edit" && editingMapping
            ? {
                description: editingMapping.description,
                internal_ip: editingMapping.internal_ip,
                internal_port: editingMapping.internal_port,
                external_port: editingMapping.external_port,
                protocol: editingMapping.protocol,
                lease_duration: editingMapping.lease_duration,
              }
            : undefined
        }
        isSubmitting={isSubmitting}
        onSubmit={handleSubmit}
      />

      <UpnpMappingDeleteDialog
        open={deleteOpen}
        onOpenChange={closeDeleteDialog}
        mapping={deleteTarget}
        isDeleting={isDeleting}
        onConfirm={confirmDelete}
      />
    </div>
  );
}

function MappingListSkeleton() {
  return (
    <Card>
      <CardContent className="p-0">
        <div className="divide-y">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center justify-between p-4">
              <div className="flex items-center gap-4 flex-1">
                <Skeleton className="h-4 w-[200px]" />
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 w-32" />
              </div>
              <Skeleton className="h-6 w-16" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
