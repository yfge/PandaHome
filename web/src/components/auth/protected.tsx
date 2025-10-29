"use client";

import { ReactNode, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import { useTranslations } from "next-intl";

import { useAuth } from "@/components/providers/auth-provider";
import { DataStateCard } from "@/components/common/data-state-card";

interface ProtectedProps {
  children: ReactNode;
  fallback?: ReactNode;
}

export function Protected({ children, fallback }: ProtectedProps) {
  const { token, isBootstrapping } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const t = useTranslations("auth");

  useEffect(() => {
    if (isBootstrapping) {
      return;
    }
    if (!token) {
      const next = pathname ? `?next=${encodeURIComponent(pathname)}` : "";
      router.replace(`/login${next}`);
    }
  }, [isBootstrapping, token, router, pathname]);

  if (isBootstrapping) {
    return (
      <div className="flex min-h-[200px] items-center justify-center">
        <DataStateCard title={t("loading")} description={t("loadingDescription") ?? undefined} />
      </div>
    );
  }

  if (!token) {
    return fallback ?? null;
  }

  return <>{children}</>;
}
