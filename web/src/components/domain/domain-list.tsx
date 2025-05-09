"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { API_ENDPOINTS } from "@/config/api";
import { Domain } from "@/types/domain";
import Link from "next/link";
import { Globe, Shield, ExternalLink } from "lucide-react";

export function DomainList() {
  const t = useTranslations("domain");
  const [domains, setDomains] = useState<Domain[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  const fetchDomains = async () => {
    try {
      setLoading(true);
      const response = await fetch(API_ENDPOINTS.domains);
      if (!response.ok) {
        throw new Error("Failed to fetch domains");
      }
      const result = await response.json();
      if (result.code === 0 && result.data) {
        setDomains(result.data);
        setError(null);
      } else {
        throw new Error(result.message || "Failed to fetch domains");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setMounted(true);
    fetchDomains();
    const interval = setInterval(fetchDomains, 30000);
    return () => clearInterval(interval);
  }, []);

  if (!mounted) {
    return <DomainListSkeleton />;
  }

  if (loading) {
    return <DomainListSkeleton />;
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col items-center justify-center space-y-4">
            <p className="text-red-500">{error}</p>
            <Button onClick={fetchDomains}>{t("retry")}</Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (domains.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col items-center justify-center space-y-4">
            <p className="text-muted-foreground">{t("noDomains")}</p>
            <Button>{t("addDomain")}</Button>
          </div>
        </CardContent>
      </Card>
    );
  }

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