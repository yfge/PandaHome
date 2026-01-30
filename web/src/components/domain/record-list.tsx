"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { DomainRecord } from "@/types/domain";
import { API_ENDPOINTS } from "@/config/api";
import { Clock, Globe, Link as LinkIcon, Lock, MoreVertical, Network, Plus, Shield } from "lucide-react";
import { DataStateCard } from "@/components/common/data-state-card";
import { apiClient, getErrorMessage, isApiEnvelope, type ApiEnvelope } from "@/lib/api-client";
import type { AsyncState } from "@/lib/async-state";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useToast } from "@/components/providers/toast-provider";
import { DomainRecordFormDialog, type DomainRecordDraft } from "@/components/domain/record-form-dialog";
import { DomainRecordDeleteDialog } from "@/components/domain/record-delete-dialog";

interface DomainRecordsPayload {
  DomainRecords?: {
    Record?: DomainRecord[] | DomainRecord;
  };
}

const extractRecords = (payload?: unknown): DomainRecord[] => {
  if (!payload) {
    return [];
  }

  if (Array.isArray(payload)) {
    return payload as DomainRecord[];
  }

  if (typeof payload !== "object") {
    return [];
  }

  const records = (payload as DomainRecordsPayload).DomainRecords?.Record;
  if (Array.isArray(records)) {
    return records;
  }

  if (records && typeof records === "object") {
    return [records as DomainRecord];
  }

  return [];
};

interface RecordListProps {
  domainName: string;
}

const RecordList = ({ domainName }: RecordListProps) => {
  const t = useTranslations("domain");
  const [state, setState] = useState<AsyncState<DomainRecord[]>>({ status: "loading" });
  const isUnmountedRef = useRef(false);
  const stateRef = useRef(state);

  const { toast } = useToast();

  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<"add" | "edit">("add");
  const [editingRecord, setEditingRecord] = useState<DomainRecord | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<DomainRecord | null>(null);
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
    (value: AsyncState<DomainRecord[]>) => {
      if (!isUnmountedRef.current) {
        setState(value);
      }
    },
    []
  );

  const setRecords = useCallback(
    (records: DomainRecord[]) => {
      if (records.length === 0) {
        setSafeState({ status: "empty" });
      } else {
        setSafeState({ status: "success", data: records });
      }
    },
    [setSafeState],
  );

  const loadRecords = useCallback(
    async (forceLoading = false) => {
      if (forceLoading) {
        setSafeState({ status: "loading" });
      }

      try {
        const endpoint = `${API_ENDPOINTS.domains}/${domainName}/records`;
        const response = await apiClient<
          DomainRecord[] | DomainRecordsPayload | ApiEnvelope<DomainRecord[] | DomainRecordsPayload>
        >(endpoint);

        let records: DomainRecord[] = [];
        if (isApiEnvelope<DomainRecord[] | DomainRecordsPayload>(response)) {
          if (response.code !== 0) {
            throw new Error(response.message ?? t("failed"));
          }
          records = extractRecords(response.data);
        } else {
          records = extractRecords(response);
        }

        if (records.length === 0) {
          setSafeState({ status: "empty" });
          return;
        }

        setSafeState({ status: "success", data: records });
      } catch (error) {
        setSafeState({
          status: "error",
          message: getErrorMessage(error, t("failed")),
        });
      }
    },
    [domainName, setSafeState, t]
  );

  const openAddDialog = useCallback(() => {
    setFormMode("add");
    setEditingRecord(null);
    setFormOpen(true);
  }, []);

  const openEditDialog = useCallback((record: DomainRecord) => {
    setFormMode("edit");
    setEditingRecord(record);
    setFormOpen(true);
  }, []);

  const requestDelete = useCallback((record: DomainRecord) => {
    setDeleteTarget(record);
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
      setEditingRecord(null);
      setFormMode("add");
    }
  }, []);

  const createRecord = useCallback(
    async (draft: DomainRecordDraft) => {
      const endpoint = `${API_ENDPOINTS.domains}/${domainName}/records`;
      const response = await apiClient<unknown | ApiEnvelope<unknown>>(endpoint, {
        method: "POST",
        body: {
          rr: draft.rr,
          type: draft.type,
          value: draft.value,
          ttl: draft.ttl,
          line: draft.line,
          priority: draft.priority,
        },
      });

      if (isApiEnvelope(response) && response.code !== 0) {
        throw new Error(response.message ?? t("failed"));
      }
    },
    [domainName, t],
  );

  const updateRecord = useCallback(
    async (recordId: string, draft: DomainRecordDraft) => {
      const endpoint = `${API_ENDPOINTS.domains}/${domainName}/records/${recordId}`;
      const response = await apiClient<unknown | ApiEnvelope<unknown>>(endpoint, {
        method: "PUT",
        body: {
          rr: draft.rr,
          type: draft.type,
          value: draft.value,
          ttl: draft.ttl,
          line: draft.line,
          priority: draft.priority,
        },
      });

      if (isApiEnvelope(response) && response.code !== 0) {
        throw new Error(response.message ?? t("failed"));
      }
    },
    [domainName, t],
  );

  const deleteRecord = useCallback(
    async (recordId: string) => {
      const endpoint = `${API_ENDPOINTS.domains}/${domainName}/records/${recordId}`;
      const response = await apiClient<unknown | ApiEnvelope<unknown>>(endpoint, { method: "DELETE" });

      if (isApiEnvelope(response) && response.code !== 0) {
        throw new Error(response.message ?? t("failed"));
      }
    },
    [domainName, t],
  );

  const handleSubmit = useCallback(
    async (draft: DomainRecordDraft) => {
      const previousState = stateRef.current;
      setIsSubmitting(true);

      const now = Date.now();

      try {
        if (formMode === "add") {
          const optimistic: DomainRecord = {
            Status: "ENABLE",
            RR: draft.rr,
            Line: draft.line,
            Locked: false,
            Type: draft.type,
            DomainName: domainName,
            Value: draft.value,
            RecordId: `optimistic-${now}-${Math.random().toString(16).slice(2)}`,
            TTL: draft.ttl,
            CreateTimestamp: now,
            UpdateTimestamp: now,
            Priority: draft.priority,
            Weight: undefined,
          };

          const current =
            previousState.status === "success"
              ? previousState.data
              : previousState.status === "empty"
                ? []
                : [];

          setRecords([optimistic, ...current]);
          await createRecord(draft);
          toast({ variant: "success", title: t("success"), description: t("toast.addSuccess") });
          closeFormDialog(false);
          await loadRecords();
          return;
        }

        const original = editingRecord;
        if (!original) {
          return;
        }

        const optimistic: DomainRecord = {
          ...original,
          RR: draft.rr,
          Type: draft.type,
          Value: draft.value,
          TTL: draft.ttl,
          Line: draft.line,
          Priority: draft.priority,
          UpdateTimestamp: now,
        };

        const current =
          previousState.status === "success"
            ? previousState.data
            : previousState.status === "empty"
              ? []
              : [];
        const index = current.findIndex((item) => item.RecordId === original.RecordId);
        const next = [...current];
        if (index >= 0) {
          next[index] = optimistic;
        } else {
          next.unshift(optimistic);
        }

        setRecords(next);
        await updateRecord(original.RecordId, draft);
        toast({ variant: "success", title: t("success"), description: t("toast.editSuccess") });
        closeFormDialog(false);
        await loadRecords();
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
      createRecord,
      domainName,
      editingRecord,
      formMode,
      loadRecords,
      setRecords,
      setSafeState,
      t,
      toast,
      updateRecord,
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
      setRecords(current.filter((item) => item.RecordId !== target.RecordId));

      await deleteRecord(target.RecordId);
      toast({ variant: "success", title: t("success"), description: t("toast.deleteSuccess") });
      closeDeleteDialog(false);
      await loadRecords();
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
  }, [
    closeDeleteDialog,
    deleteRecord,
    deleteTarget,
    loadRecords,
    setRecords,
    setSafeState,
    t,
    toast,
  ]);

  useEffect(() => {
    loadRecords(true);
    const interval = setInterval(() => {
      loadRecords();
    }, 30000);

    return () => clearInterval(interval);
  }, [loadRecords]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-end gap-2">
        <Button type="button" onClick={openAddDialog} disabled={isSubmitting || isDeleting}>
          <Plus className="h-4 w-4" />
          {t("addRecord")}
        </Button>
      </div>

      {state.status === "loading" ? <RecordListSkeleton /> : null}

      {state.status === "error" ? (
        <DataStateCard
          variant="error"
          title={t("error")}
          description={state.message}
          action={{
            label: t("retry"),
            onClick: () => loadRecords(true),
          }}
        />
      ) : null}

      {state.status === "empty" ? (
        <DataStateCard
          title={t("noRecords")}
          description={t("addRecord")}
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
              {state.data.map((record) => (
                <div
                  key={record.RecordId}
                  className="flex items-center justify-between gap-3 p-4 transition-colors hover:bg-muted/50"
                >
                  <div className="flex flex-1 flex-wrap items-center gap-4">
                    <div className="flex min-w-[150px] items-center gap-2">
                      <Globe className="h-4 w-4 text-primary" />
                      <span className="font-medium">{record.RR}</span>
                    </div>
                    <div className="text-muted-foreground flex items-center gap-2 text-sm">
                      <Shield className="h-4 w-4" />
                      <span>{record.Type}</span>
                    </div>
                    <div className="text-muted-foreground flex min-w-[180px] items-center gap-2 text-sm">
                      <LinkIcon className="h-4 w-4" />
                      <span className="truncate">{record.Value}</span>
                    </div>
                    <div className="text-muted-foreground flex items-center gap-2 text-sm">
                      <Clock className="h-4 w-4" />
                      <span>
                        {record.TTL} {t("seconds")}
                      </span>
                    </div>
                    <div className="text-muted-foreground flex items-center gap-2 text-sm">
                      <Network className="h-4 w-4" />
                      <span>{record.Line}</span>
                    </div>
                    {record.Priority ? (
                      <div className="text-muted-foreground flex items-center gap-2 text-sm">
                        <span>
                          {t("priority")}: {record.Priority}
                        </span>
                      </div>
                    ) : null}
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded-full px-2 py-1 text-xs font-medium ${
                        record.Status === "ENABLE"
                          ? "bg-emerald-500/10 text-emerald-700"
                          : "bg-destructive/10 text-destructive"
                      }`}
                    >
                      {record.Status === "ENABLE" ? t("enabled") : t("disabled")}
                    </span>

                    {record.Locked ? (
                      <span className="bg-muted text-muted-foreground inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium">
                        <Lock className="h-3 w-3" />
                        {t("locked")}
                      </span>
                    ) : null}

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
                            openEditDialog(record);
                          }}
                          disabled={record.Locked || isSubmitting || isDeleting}
                        >
                          {t("edit")}
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          variant="destructive"
                          onSelect={(event) => {
                            event.preventDefault();
                            requestDelete(record);
                          }}
                          disabled={record.Locked || isSubmitting || isDeleting}
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

      <DomainRecordFormDialog
        mode={formMode}
        open={formOpen}
        onOpenChange={closeFormDialog}
        initialValues={
          formMode === "edit" && editingRecord
            ? {
                rr: editingRecord.RR,
                type: editingRecord.Type as DomainRecordDraft["type"],
                value: editingRecord.Value,
                ttl: editingRecord.TTL,
                line: editingRecord.Line,
                priority: editingRecord.Priority,
              }
            : undefined
        }
        isSubmitting={isSubmitting}
        onSubmit={handleSubmit}
      />

      <DomainRecordDeleteDialog
        open={deleteOpen}
        onOpenChange={closeDeleteDialog}
        record={deleteTarget}
        isDeleting={isDeleting}
        onConfirm={confirmDelete}
      />
    </div>
  );
};

const RecordListSkeleton = () => {
  return (
    <Card>
      <CardContent className="p-0">
        <div className="divide-y">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center justify-between p-4">
              <div className="flex items-center gap-4 flex-1">
                <Skeleton className="h-4 w-[150px]" />
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-4 w-24" />
              </div>
              <Skeleton className="h-6 w-16" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export { RecordList };
