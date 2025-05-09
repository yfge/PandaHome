"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { API_ENDPOINTS } from "@/config/api";
import { UpnpMapping } from "@/types/upnp";
import { Network, Globe, Clock, Shield } from "lucide-react";

export function UpnpMappingList() {
  const t = useTranslations("upnp");
  const [mappings, setMappings] = useState<UpnpMapping[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  const fetchMappings = async () => {
    try {
      setLoading(true);
      const response = await fetch(API_ENDPOINTS.upnpMappings);
      if (!response.ok) {
        throw new Error("Failed to fetch UPnP mappings");
      }
      const result = await response.json();
      if (result.code === 0 && result.data?.mappings) {
        setMappings(result.data.mappings);
        setError(null);
      } else {
        throw new Error(result.message || "Failed to fetch UPnP mappings");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setMounted(true);
    fetchMappings();
    const interval = setInterval(fetchMappings, 30000);
    return () => clearInterval(interval);
  }, []);

  if (!mounted) {
    return <MappingListSkeleton />;
  }

  if (loading) {
    return <MappingListSkeleton />;
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col items-center justify-center space-y-4">
            <p className="text-red-500">{error}</p>
            <Button onClick={fetchMappings}>{t("retry")}</Button>
          </div>
        </CardContent>
      </Card>
    );
  }

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