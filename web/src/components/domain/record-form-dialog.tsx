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
import { Input } from "@/components/ui/input";

type RecordType = "A" | "AAAA" | "CNAME" | "TXT";

export interface DomainRecordDraft {
  rr: string;
  type: RecordType;
  value: string;
  ttl: number;
  line: string;
  priority?: number;
}

type FormMode = "add" | "edit";

interface DomainRecordFormDialogProps {
  mode: FormMode;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initialValues?: DomainRecordDraft;
  isSubmitting?: boolean;
  onSubmit: (values: DomainRecordDraft) => Promise<void> | void;
}

function getDefaultValues(): DomainRecordDraft {
  return {
    rr: "",
    type: "A",
    value: "",
    ttl: 600,
    line: "default",
    priority: undefined,
  };
}

function validate(values: DomainRecordDraft, t: ReturnType<typeof useTranslations>): Record<string, string> {
  const errors: Record<string, string> = {};

  if (!values.rr.trim()) {
    errors.rr = t("form.required");
  }

  if (!values.value.trim()) {
    errors.value = t("form.required");
  }

  if (!Number.isInteger(values.ttl) || values.ttl < 1) {
    errors.ttl = t("form.invalidTtl");
  }

  if (!values.line.trim()) {
    errors.line = t("form.required");
  }

  if (values.priority !== undefined && (!Number.isInteger(values.priority) || values.priority < 1)) {
    errors.priority = t("form.invalidPriority");
  }

  return errors;
}

export function DomainRecordFormDialog({
  mode,
  open,
  onOpenChange,
  initialValues,
  isSubmitting = false,
  onSubmit,
}: DomainRecordFormDialogProps) {
  const t = useTranslations("domain");
  const [values, setValues] = useState<DomainRecordDraft>(() => initialValues ?? getDefaultValues());
  const [errors, setErrors] = useState<Record<string, string>>({});

  const title = mode === "add" ? t("addRecord") : t("editRecord");
  const submitLabel = mode === "add" ? t("add") : t("save");

  const description = useMemo(() => {
    return mode === "add" ? t("form.addDescription") : t("form.editDescription");
  }, [mode, t]);

  useEffect(() => {
    if (!open) {
      return;
    }
    // Reset local draft state when the dialog opens.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setValues(initialValues ?? getDefaultValues());
    setErrors({});
  }, [initialValues, open]);

  const submit = async () => {
    const nextErrors = validate(values, t);
    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      return;
    }

    await onSubmit({
      ...values,
      rr: values.rr.trim(),
      value: values.value.trim(),
      line: values.line.trim(),
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        <div className="grid gap-4">
          <div className="grid gap-2">
            <label htmlFor="domain-rr" className="text-sm font-medium">
              {t("form.rr")}
            </label>
            <Input
              id="domain-rr"
              value={values.rr}
              onChange={(event) => setValues((current) => ({ ...current, rr: event.target.value }))}
              placeholder={t("form.rrPlaceholder")}
              disabled={isSubmitting}
              aria-invalid={Boolean(errors.rr)}
            />
            {errors.rr ? <p className="text-destructive text-xs">{errors.rr}</p> : null}
          </div>

          <div className="grid gap-2">
            <label htmlFor="domain-type" className="text-sm font-medium">
              {t("recordType")}
            </label>
            <select
              id="domain-type"
              value={values.type}
              onChange={(event) =>
                setValues((current) => ({ ...current, type: (event.target.value as RecordType) || "A" }))
              }
              disabled={isSubmitting}
              className="bg-background border-input focus-visible:ring-primary/70 ring-offset-background flex h-10 w-full rounded-md border px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="A">A</option>
              <option value="AAAA">AAAA</option>
              <option value="CNAME">CNAME</option>
              <option value="TXT">TXT</option>
            </select>
          </div>

          <div className="grid gap-2">
            <label htmlFor="domain-value" className="text-sm font-medium">
              {t("value")}
            </label>
            <Input
              id="domain-value"
              value={values.value}
              onChange={(event) => setValues((current) => ({ ...current, value: event.target.value }))}
              placeholder={t("form.valuePlaceholder")}
              disabled={isSubmitting}
              aria-invalid={Boolean(errors.value)}
            />
            {errors.value ? <p className="text-destructive text-xs">{errors.value}</p> : null}
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="grid gap-2">
              <label htmlFor="domain-ttl" className="text-sm font-medium">
                {t("ttl")}
              </label>
              <Input
                id="domain-ttl"
                type="number"
                inputMode="numeric"
                min={1}
                value={Number.isFinite(values.ttl) ? values.ttl : 600}
                onChange={(event) =>
                  setValues((current) => ({
                    ...current,
                    ttl: Number.parseInt(event.target.value || "0", 10),
                  }))
                }
                disabled={isSubmitting}
                aria-invalid={Boolean(errors.ttl)}
              />
              {errors.ttl ? <p className="text-destructive text-xs">{errors.ttl}</p> : null}
            </div>
            <div className="grid gap-2">
              <label htmlFor="domain-line" className="text-sm font-medium">
                {t("line")}
              </label>
              <Input
                id="domain-line"
                value={values.line}
                onChange={(event) => setValues((current) => ({ ...current, line: event.target.value }))}
                placeholder={t("form.linePlaceholder")}
                disabled={isSubmitting}
                aria-invalid={Boolean(errors.line)}
              />
              {errors.line ? <p className="text-destructive text-xs">{errors.line}</p> : null}
            </div>
          </div>

          <div className="grid gap-2">
            <label htmlFor="domain-priority" className="text-sm font-medium">
              {t("priority")}
            </label>
            <Input
              id="domain-priority"
              type="number"
              inputMode="numeric"
              min={1}
              value={values.priority ?? ""}
              onChange={(event) => {
                const raw = event.target.value;
                setValues((current) => ({
                  ...current,
                  priority: raw === "" ? undefined : Number.parseInt(raw, 10),
                }));
              }}
              disabled={isSubmitting}
              aria-invalid={Boolean(errors.priority)}
            />
            {errors.priority ? <p className="text-destructive text-xs">{errors.priority}</p> : null}
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={isSubmitting}>
            {t("cancel")}
          </Button>
          <Button type="button" onClick={submit} disabled={isSubmitting}>
            {submitLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
