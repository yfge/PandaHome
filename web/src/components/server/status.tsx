"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { API_ENDPOINTS } from "@/config/api";
import { DataStateCard } from "@/components/common/data-state-card";
import { apiClient, getErrorMessage, isApiEnvelope, type ApiEnvelope } from "@/lib/api-client";
import type { AsyncState } from "@/lib/async-state";

interface ServerStatus {
  cpu: {
    usage: number;
    cores: number;
  };
  memory: {
    total: number;
    used: number;
    free: number;
  };
  disk: {
    total: number;
    used: number;
    free: number;
  };
  uptime: number;
  services: {
    name: string;
    status: "running" | "stopped" | "error";
  }[];
}

export function ServerStatus() {
  const t = useTranslations();
  const [state, setState] = useState<AsyncState<ServerStatus>>({ status: "loading" });
  const isUnmountedRef = useRef(false);

  useEffect(() => {
    isUnmountedRef.current = false;
    return () => {
      isUnmountedRef.current = true;
    };
  }, []);

  const setSafeState = useCallback(
    (value: AsyncState<ServerStatus>) => {
      if (!isUnmountedRef.current) {
        setState(value);
      }
    },
    []
  );

  const loadStatus = useCallback(
    async (forceLoading = false) => {
      if (forceLoading) {
        setSafeState({ status: "loading" });
      }

      try {
        const response = await apiClient<ServerStatus | ApiEnvelope<ServerStatus>>(API_ENDPOINTS.status);
        let data: ServerStatus | undefined;

        if (isApiEnvelope<ServerStatus>(response)) {
          if (response.code !== 0) {
            throw new Error(response.message ?? t("server.error"));
          }
          data = response.data ?? undefined;
        } else {
          data = response;
        }

        if (!data) {
          setSafeState({ status: "empty" });
          return;
        }

        setSafeState({ status: "success", data });
      } catch (error) {
        setSafeState({
          status: "error",
          message: getErrorMessage(error, t("server.error")),
        });
      }
    },
    [setSafeState, t]
  );

  useEffect(() => {
    loadStatus(true);
    const interval = setInterval(() => {
      loadStatus();
    }, 30000);
    return () => clearInterval(interval);
  }, [loadStatus]);

  if (state.status === "loading") {
    return <StatusSkeleton />;
  }

  if (state.status === "error") {
    return (
      <DataStateCard
        variant="error"
        title={t("server.error")}
        description={state.message}
        action={{
          label: t("server.retry"),
          onClick: () => loadStatus(true),
        }}
      />
    );
  }

  if (state.status === "empty") {
    return (
      <DataStateCard
        title={t("server.empty")}
        description={t("server.statusDescription")}
      />
    );
  }

  const status = state.data;

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      <Card>
        <CardHeader>
          <CardTitle>CPU</CardTitle>
          <CardDescription>
            {t("server.cpuUsage", { usage: status.cpu.usage.toFixed(1) })}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>{t("server.cores")}</span>
              <span>{status.cpu.cores}</span>
            </div>
            <div className="w-full bg-secondary h-2 rounded-full">
              <div
                className="bg-primary h-2 rounded-full transition-all"
                style={{ width: `${status.cpu.usage}%` }}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("server.memory")}</CardTitle>
          <CardDescription>
            {t("server.memoryUsage", {
              used: formatBytes(status.memory.used),
              total: formatBytes(status.memory.total),
            })}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>{t("server.free")}</span>
              <span>{formatBytes(status.memory.free)}</span>
            </div>
            <div className="w-full bg-secondary h-2 rounded-full">
              <div
                className="bg-primary h-2 rounded-full transition-all"
                style={{
                  width: `${(status.memory.used / status.memory.total) * 100}%`,
                }}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("server.disk")}</CardTitle>
          <CardDescription>
            {t("server.diskUsage", {
              used: formatBytes(status.disk.used),
              total: formatBytes(status.disk.total),
            })}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>{t("server.free")}</span>
              <span>{formatBytes(status.disk.free)}</span>
            </div>
            <div className="w-full bg-secondary h-2 rounded-full">
              <div
                className="bg-primary h-2 rounded-full transition-all"
                style={{
                  width: `${(status.disk.used / status.disk.total) * 100}%`,
                }}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="md:col-span-2 lg:col-span-3">
        <CardHeader>
          <CardTitle>{t("server.services")}</CardTitle>
          <CardDescription>{t("server.serviceStatus")}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {status.services.map((service) => (
              <div
                key={service.name}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <span>{service.name}</span>
                <span
                  className={`px-2 py-1 rounded-full text-sm ${
                    service.status === "running"
                      ? "bg-green-100 text-green-800"
                      : service.status === "stopped"
                      ? "bg-yellow-100 text-yellow-800"
                      : "bg-red-100 text-red-800"
                  }`}
                >
                  {service.status}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function StatusSkeleton() {
  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {[1, 2, 3].map((i) => (
        <Card key={i}>
          <CardHeader>
            <Skeleton className="h-6 w-24" />
            <Skeleton className="h-4 w-32" />
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-2 w-full" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function formatBytes(bytes: number): string {
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes;
  let unitIndex = 0;

  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex++;
  }

  return `${value.toFixed(1)} ${units[unitIndex]}`;
} 
