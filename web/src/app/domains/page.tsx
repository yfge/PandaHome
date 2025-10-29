"use client";

import { useTranslations } from "next-intl";
import { DomainList } from "@/components/domain/domain-list";
import { Protected } from "@/components/auth/protected";

export default function DomainsPage() {
  const t = useTranslations("domain");

  return (
    <Protected>
      <div className="container mx-auto py-6">
        <h1 className="text-3xl font-bold mb-6">{t("title")}</h1>
        <DomainList />
      </div>
    </Protected>
  );
}
