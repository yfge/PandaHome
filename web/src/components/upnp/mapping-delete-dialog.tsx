"use client";

import { useEffect, useMemo, useState } from "react";
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
import { UpnpDialogError, type UpnpSubmissionError } from "@/components/upnp/dialog-error";
import { getErrorMessage } from "@/lib/api-client";

interface UpnpMappingDeleteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mapping: UpnpMapping | null;
  isDeleting?: boolean;
  onCloseAutoFocus?: (event: Event) => void;
  onConfirm: () => Promise<void> | void;
}

export function UpnpMappingDeleteDialog({
  open,
  onOpenChange,
  mapping,
  isDeleting = false,
  onCloseAutoFocus,
  onConfirm,
}: UpnpMappingDeleteDialogProps) {
  const t = useTranslations("upnp");
  const [submissionError, setSubmissionError] = useState<UpnpSubmissionError | null>(null);

  useEffect(() => {
    if (open) {
      // Reset feedback for a newly opened confirmation.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSubmissionError(null);
    }
  }, [open]);

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
    setSubmissionError(null);
    try {
      await onConfirm();
    } catch (error) {
      setSubmissionError({ message: getErrorMessage(error, t("failed")) });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[calc(100dvh-2rem)] overflow-y-auto" onCloseAutoFocus={onCloseAutoFocus}>
        <DialogHeader>
          <DialogTitle>{t("confirmDelete")}</DialogTitle>
          <DialogDescription>
            {t("deleteConfirmMessage")}
            {summary ? <span className="text-muted-foreground mt-2 block text-sm">{summary}</span> : null}
          </DialogDescription>
        </DialogHeader>
        <UpnpDialogError error={submissionError} />
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
