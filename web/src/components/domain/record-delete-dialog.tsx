"use client";

import { useMemo } from "react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { DomainRecord } from "@/types/domain";

interface DomainRecordDeleteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  record: DomainRecord | null;
  isDeleting?: boolean;
  onConfirm: () => Promise<void> | void;
}

export function DomainRecordDeleteDialog({
  open,
  onOpenChange,
  record,
  isDeleting = false,
  onConfirm,
}: DomainRecordDeleteDialogProps) {
  const t = useTranslations("domain");

  const summary = useMemo(() => {
    if (!record) {
      return "";
    }

    return t("recordDescription", {
      rr: record.RR,
      type: record.Type,
      value: record.Value,
    });
  }, [record, t]);

  const confirm = async () => {
    await onConfirm();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("confirmDelete")}</DialogTitle>
          <DialogDescription>
            {t("deleteRecordConfirmMessage")}
            {summary ? <div className="text-muted-foreground mt-2 text-sm">{summary}</div> : null}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={isDeleting}>
            {t("cancel")}
          </Button>
          <Button type="button" variant="destructive" onClick={confirm} disabled={!record || isDeleting}>
            {t("delete")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
