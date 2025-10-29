"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { API_ENDPOINTS } from "@/config/api";
import { UpnpMapping } from "@/types/upnp";
import { Network, Globe, Clock, Shield } from "lucide-react";
import { DataStateCard } from "@/components/common/data-state-card";
import { apiClient, getErrorMessage, isApiEnvelope, type ApiEnvelope } from "@/lib/api-client";
import type { AsyncState } from "@/lib/async-state";

export function UpnpMappingList() {
  const t = useTranslations("upnp");
  const [state, setState] = useState<AsyncState<UpnpMapping[]>>({ status: "loading" });
  const isUnmountedRef = useRef(false);

  useEffect(() => {
    isUnmountedRef.current = false;
    return () => {
      isUnmountedRef.current = true;
    };
  }, []);

  const setSafeState = useCallback(
    (value: AsyncState<UpnpMapping[]>) => {
      if (!isUnmountedRef.current) {
        setState(value);
      }
    },
    []
  );

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

  useEffect(() => {
    loadMappings(true);
    const interval = setInterval(() => {
      loadMappings();
    }, 30000);

    return () => clearInterval(interval);
  }, [loadMappings]);

  if (state.status === "loading") {
    return <MappingListSkeleton />;
  }

  if (state.status === "error") {
    return (
      <DataStateCard
        variant="error"
        title={t("error")}
        description={state.message}
        action={{
          label: t("retry"),
          onClick: () => loadMappings(true),
        }}
      />
    );
  }

  if (state.status === "empty") {
    return (
      <DataStateCard
        title={t("noMappings")}
        description={t("addMapping")}
      />
    );
  }

  const mappings = state.data;

  return (
    <Card>
      <CardContent className="p-0">
        <div className="divide-y">
          {mappings.map((mapping) => (
            <div key={`${mapping.internal_ip}-${mapping.internal_port}-${mapping.external_port}`} 
                 className="flex items-center justify-between p-4 hover:bg-muted/50 transition-colors">
              <div className="flex items-center gap-4 flex-1">
                <div className="flex items-center gap-2 min-w-[200px]">
                  <Network className="w-4 h-4 text-muted-foreground" />
                  <span className="font-medium">{mapping.description || t("noDescription")}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Globe className="w-4 h-4" />
                  <span>{mapping.internal_ip}:{mapping.internal_port}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Shield className="w-4 h-4" />
                  <span>{mapping.external_port}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Clock className="w-4 h-4" />
                  <span>{mapping.lease_duration === 0 ? t("permanent") : `${mapping.lease_duration} ${t("seconds")}`}</span>
                </div>
              </div>
              <span
                className={`px-2 py-1 rounded-full text-xs font-medium ${
                  mapping.enabled
                    ? "bg-green-100 text-green-800"
                    : "bg-red-100 text-red-800"
                }`}
              >
                {mapping.enabled ? t("enabled") : t("disabled")}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
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
