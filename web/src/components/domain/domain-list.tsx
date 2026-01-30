"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { API_ENDPOINTS } from "@/config/api";
import { Domain } from "@/types/domain";
import Link from "next/link";
import { Globe, Shield, ExternalLink } from "lucide-react";
import { DataStateCard } from "@/components/common/data-state-card";
import { apiClient, getErrorMessage, isApiEnvelope, type ApiEnvelope } from "@/lib/api-client";
import type { AsyncState } from "@/lib/async-state";
import { Button } from "@/components/ui/button";

export function DomainList() {
  const t = useTranslations("domain");
  const [state, setState] = useState<AsyncState<Domain[]>>({ status: "loading" });
  const isUnmountedRef = useRef(false);

  useEffect(() => {
    isUnmountedRef.current = false;
    return () => {
      isUnmountedRef.current = true;
    };
  }, []);

  const setSafeState = useCallback(
    (value: AsyncState<Domain[]>) => {
      if (!isUnmountedRef.current) {
        setState(value);
      }
    },
    []
  );

  const loadDomains = useCallback(
    async (forceLoading = false) => {
      if (forceLoading) {
        setSafeState({ status: "loading" });
      }

      try {
        const response = await apiClient<Domain[] | ApiEnvelope<Domain[]>>(API_ENDPOINTS.domains);
        let data: Domain[] = [];

        if (isApiEnvelope<Domain[]>(response)) {
          if (response.code !== 0) {
            throw new Error(response.message ?? t("failed"));
          }
          if (Array.isArray(response.data)) {
            data = response.data;
          }
        } else if (Array.isArray(response)) {
          data = response;
        }

        if (data.length === 0) {
          setSafeState({ status: "empty" });
          return;
        }

        setSafeState({ status: "success", data });
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
    loadDomains(true);
    const interval = setInterval(() => {
      loadDomains();
    }, 30000);

    return () => clearInterval(interval);
  }, [loadDomains]);

  if (state.status === "loading") {
    return <DomainListSkeleton />;
  }

  if (state.status === "error") {
    return (
      <DataStateCard
        variant="error"
        title={t("error")}
        description={state.message}
        action={{
          label: t("retry"),
          onClick: () => loadDomains(true),
        }}
      />
    );
  }

  if (state.status === "empty") {
    return (
      <DataStateCard
        title={t("noDomains")}
        description={t("addDomain")}
      />
    );
  }

  const domains = state.data;

  return (
    <Card>
      <CardContent className="p-0">
        <div className="divide-y">
          {domains.map((domain) => (
            <div key={domain.id} className="flex items-center justify-between p-4 hover:bg-muted/50 transition-colors">
              <div className="flex items-center gap-4 flex-1">
                <div className="flex items-center gap-2 min-w-[200px]">
                  <Globe className="w-4 h-4 text-primary" />
                  <span className="font-medium">{domain.domain}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Shield className="w-4 h-4" />
                  <span>{t("id")}: {domain.id}</span>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span
                  className={`px-2 py-1 rounded-full text-xs font-medium ${
                    domain.status === "ENABLE"
                      ? "bg-green-100 text-green-800"
                      : "bg-red-100 text-red-800"
                  }`}
                >
                  {domain.status}
                </span>
                <Link href={`/domains/${domain.domain}/records`}>
                  <Button variant="outline" size="sm">
                    <ExternalLink className="w-4 h-4 mr-2" />
                    {t("viewRecords")}
                  </Button>
                </Link>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function DomainListSkeleton() {
  return (
    <Card>
      <CardContent className="p-0">
        <div className="divide-y">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center justify-between p-4">
              <div className="flex items-center gap-4 flex-1">
                <Skeleton className="h-4 w-[200px]" />
                <Skeleton className="h-4 w-32" />
              </div>
              <div className="flex items-center gap-4">
                <Skeleton className="h-6 w-16" />
                <Skeleton className="h-9 w-24" />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
