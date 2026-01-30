"use client";

import { useTranslations } from "next-intl";
import { RecordList } from "@/components/domain/record-list";
import { Protected } from "@/components/auth/protected";

interface DomainRecordsPageProps {
  params: {
    domain: string;
  };
}

const DomainRecordsPage = ({ params }: DomainRecordsPageProps) => {
  const t = useTranslations("domain");
  const { domain } = params;

  return (
    <Protected>
      <div className="container mx-auto py-6">
        <h1 className="text-3xl font-bold mb-6">
          {domain} - {t("title")}
        </h1>
        <RecordList domainName={domain} />
      </div>
    </Protected>
  );
};

export default DomainRecordsPage;
