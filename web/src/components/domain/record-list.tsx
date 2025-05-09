"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { DomainRecord } from "@/types/domain";
import { API_ENDPOINTS } from "@/config/api";
import { Globe, Clock, Shield, Link as LinkIcon } from "lucide-react";

interface RecordListProps {
  domainName: string;
}

const RecordList = ({ domainName }: RecordListProps) => {
  const t = useTranslations("domain");
  const [records, setRecords] = useState<DomainRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  const fetchRecords = async () => {
    try {
      const response = await fetch(`${API_ENDPOINTS.domains}/${domainName}/records`);
      if (!response.ok) {
        throw new Error("Failed to fetch records");
      }
      const result = await response.json();
      if (result.code === 0) {
        const records = result.data?.DomainRecords?.Record || [];
        setRecords(Array.isArray(records) ? records : []);
        setError(null);
      } else {
        throw new Error(result.message || "Failed to fetch records");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch records");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setMounted(true);
    fetchRecords();
    const interval = setInterval(fetchRecords, 30000);
    return () => clearInterval(interval);
  }, [domainName]);

  if (!mounted) {
    return <RecordListSkeleton />;
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col items-center justify-center space-y-4">
            <p className="text-red-500">{error}</p>
            <Button onClick={fetchRecords}>{t("retry")}</Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (loading) {
    return <RecordListSkeleton />;
  }

  if (records.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col items-center justify-center space-y-4">
            <p className="text-muted-foreground">{t("noRecords")}</p>
            <Button>{t("addRecord")}</Button>
          </div>
        </CardContent>
      </Card>
    );
  }

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