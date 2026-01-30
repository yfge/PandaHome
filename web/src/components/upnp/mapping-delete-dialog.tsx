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
import type { UpnpMapping } from "@/types/upnp";

interface UpnpMappingDeleteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mapping: UpnpMapping | null;
  isDeleting?: boolean;
  onConfirm: () => Promise<void> | void;
}

export function UpnpMappingDeleteDialog({
  open,
  onOpenChange,
  mapping,
  isDeleting = false,
  onConfirm,
}: UpnpMappingDeleteDialogProps) {
  const t = useTranslations("upnp");

  const summary = useMemo(() => {
    if (!mapping) {
      return "";
    }
    return t("mappingDescription", {
      protocol: mapping.protocol,
      internal_ip: mapping.internal_ip,
      internal_port: mapping.internal_port,
      external_port: mapping.external_port,
    });
  }, [mapping, t]);

  const confirm = async () => {
    await onConfirm();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("confirmDelete")}</DialogTitle>
          <DialogDescription>
            {t("deleteConfirmMessage")}
            {summary ? <div className="text-muted-foreground mt-2 text-sm">{summary}</div> : null}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={isDeleting}>
            {t("cancel")}
          </Button>
          <Button type="button" variant="destructive" onClick={confirm} disabled={!mapping || isDeleting}>
            {t("delete")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
