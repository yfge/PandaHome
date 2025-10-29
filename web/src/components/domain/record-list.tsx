"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { DomainRecord } from "@/types/domain";
import { API_ENDPOINTS } from "@/config/api";
import { Globe, Clock, Shield, Link as LinkIcon } from "lucide-react";
import { DataStateCard } from "@/components/common/data-state-card";
import { apiClient, getErrorMessage, isApiEnvelope, type ApiEnvelope } from "@/lib/api-client";
import type { AsyncState } from "@/lib/async-state";

interface DomainRecordsPayload {
  DomainRecords?: {
    Record?: DomainRecord[] | DomainRecord;
  };
}

const extractRecords = (payload?: DomainRecordsPayload): DomainRecord[] => {
  if (!payload || typeof payload !== "object") {
    return [];
  }

  const records = payload.DomainRecords?.Record;
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

  useEffect(() => {
    isUnmountedRef.current = false;
    return () => {
      isUnmountedRef.current = true;
    };
  }, []);

  const setSafeState = useCallback(
    (value: AsyncState<DomainRecord[]>) => {
      if (!isUnmountedRef.current) {
        setState(value);
      }
    },
    []
  );

  const loadRecords = useCallback(
    async (forceLoading = false) => {
      if (forceLoading) {
        setSafeState({ status: "loading" });
      }

      try {
        const endpoint = `${API_ENDPOINTS.domains}/${domainName}/records`;
        const response = await apiClient<DomainRecordsPayload | ApiEnvelope<DomainRecordsPayload>>(endpoint);

        let records: DomainRecord[] = [];
        if (isApiEnvelope<DomainRecordsPayload>(response)) {
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

  useEffect(() => {
    loadRecords(true);
    const interval = setInterval(() => {
      loadRecords();
    }, 30000);

    return () => clearInterval(interval);
  }, [loadRecords]);

  if (state.status === "loading") {
    return <RecordListSkeleton />;
  }

  if (state.status === "error") {
    return (
      <DataStateCard
        variant="error"
        title={t("error")}
        description={state.message}
        action={{
          label: t("retry"),
          onClick: () => loadRecords(true),
        }}
      />
    );
  }

  if (state.status === "empty") {
    return (
      <DataStateCard
        title={t("noRecords")}
        description={t("addRecord")}
      />
    );
  }

  const records = state.data;

  return (
    <Card>
      <CardContent className="p-0">
        <div className="divide-y">
          {records.map((record) => (
            <div key={record.RecordId} className="flex items-center justify-between p-4 hover:bg-muted/50 transition-colors">
              <div className="flex items-center gap-4 flex-1">
                <div className="flex items-center gap-2 min-w-[150px]">
                  <Globe className="w-4 h-4 text-primary" />
                  <span className="font-medium">{record.RR}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Shield className="w-4 h-4" />
                  <span>{record.Type}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <LinkIcon className="w-4 h-4" />
                  <span>{record.Value}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Clock className="w-4 h-4" />
                  <span>{record.TTL} {t("seconds")}</span>
                </div>
              </div>
              <span
                className={`px-2 py-1 rounded-full text-xs font-medium ${
                  record.Status === "ENABLE"
                    ? "bg-green-100 text-green-800"
                    : "bg-red-100 text-red-800"
                }`}
              >
                {record.Status === "ENABLE" ? t("enabled") : t("disabled")}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
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
