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
import type { UpnpMapping } from "@/types/upnp";

type FormMode = "add" | "edit";

export type UpnpMappingDraft = Pick<
  UpnpMapping,
  "description" | "internal_ip" | "internal_port" | "external_port" | "protocol" | "lease_duration"
>;

interface UpnpMappingFormDialogProps {
  mode: FormMode;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initialValues?: UpnpMappingDraft;
  isSubmitting?: boolean;
  onSubmit: (values: UpnpMappingDraft) => Promise<void> | void;
}

function getDefaultValues(): UpnpMappingDraft {
  return {
    description: "",
    internal_ip: "",
    internal_port: 0,
    external_port: 0,
    protocol: "TCP",
    lease_duration: 0,
  };
}

function validate(values: UpnpMappingDraft, t: ReturnType<typeof useTranslations>): Partial<Record<keyof UpnpMappingDraft, string>> {
  const errors: Partial<Record<keyof UpnpMappingDraft, string>> = {};

  const withinPortRange = (port: number) => Number.isInteger(port) && port >= 1 && port <= 65535;

  if (!values.internal_ip.trim()) {
    errors.internal_ip = t("form.required");
  }

  if (!withinPortRange(values.internal_port)) {
    errors.internal_port = t("form.invalidPort");
  }

  if (!withinPortRange(values.external_port)) {
    errors.external_port = t("form.invalidPort");
  }

  if (!Number.isInteger(values.lease_duration) || values.lease_duration < 0) {
    errors.lease_duration = t("form.invalidLease");
  }

  return errors;
}

export function UpnpMappingFormDialog({
  mode,
  open,
  onOpenChange,
  initialValues,
  isSubmitting = false,
  onSubmit,
}: UpnpMappingFormDialogProps) {
  const t = useTranslations("upnp");
  const [values, setValues] = useState<UpnpMappingDraft>(() => initialValues ?? getDefaultValues());
  const [errors, setErrors] = useState<Partial<Record<keyof UpnpMappingDraft, string>>>({});

  const title = mode === "add" ? t("addMapping") : t("editMapping");
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
      description: values.description.trim(),
      internal_ip: values.internal_ip.trim(),
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
            <label htmlFor="upnp-description" className="text-sm font-medium">
              {t("description")}
            </label>
            <Input
              id="upnp-description"
              value={values.description}
              onChange={(event) => setValues((current) => ({ ...current, description: event.target.value }))}
              placeholder={t("form.descriptionPlaceholder")}
              disabled={isSubmitting}
            />
          </div>

          <div className="grid gap-2">
            <label htmlFor="upnp-protocol" className="text-sm font-medium">
              {t("form.protocol")}
            </label>
            <select
              id="upnp-protocol"
              value={values.protocol}
              onChange={(event) =>
                setValues((current) => ({ ...current, protocol: event.target.value === "UDP" ? "UDP" : "TCP" }))
              }
              disabled={isSubmitting}
              className="bg-background border-input focus-visible:ring-primary/70 ring-offset-background flex h-10 w-full rounded-md border px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="TCP">TCP</option>
              <option value="UDP">UDP</option>
            </select>
          </div>

          <div className="grid gap-2">
            <label htmlFor="upnp-internal-ip" className="text-sm font-medium">
              {t("form.internalIp")}
            </label>
            <Input
              id="upnp-internal-ip"
              value={values.internal_ip}
              onChange={(event) => setValues((current) => ({ ...current, internal_ip: event.target.value }))}
              placeholder="192.168.1.10"
              disabled={isSubmitting}
              aria-invalid={Boolean(errors.internal_ip)}
            />
            {errors.internal_ip ? <p className="text-destructive text-xs">{errors.internal_ip}</p> : null}
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="grid gap-2">
              <label htmlFor="upnp-internal-port" className="text-sm font-medium">
                {t("form.internalPort")}
              </label>
              <Input
                id="upnp-internal-port"
                type="number"
                inputMode="numeric"
                min={1}
                max={65535}
                value={values.internal_port || ""}
                onChange={(event) =>
                  setValues((current) => ({
                    ...current,
                    internal_port: Number.parseInt(event.target.value || "0", 10),
                  }))
                }
                disabled={isSubmitting}
                aria-invalid={Boolean(errors.internal_port)}
              />
              {errors.internal_port ? <p className="text-destructive text-xs">{errors.internal_port}</p> : null}
            </div>
            <div className="grid gap-2">
              <label htmlFor="upnp-external-port" className="text-sm font-medium">
                {t("form.externalPort")}
              </label>
              <Input
                id="upnp-external-port"
                type="number"
                inputMode="numeric"
                min={1}
                max={65535}
                value={values.external_port || ""}
                onChange={(event) =>
                  setValues((current) => ({
                    ...current,
                    external_port: Number.parseInt(event.target.value || "0", 10),
                  }))
                }
                disabled={isSubmitting}
                aria-invalid={Boolean(errors.external_port)}
              />
              {errors.external_port ? <p className="text-destructive text-xs">{errors.external_port}</p> : null}
            </div>
          </div>

          <div className="grid gap-2">
            <label htmlFor="upnp-lease-duration" className="text-sm font-medium">
              {t("leaseDuration")}
            </label>
            <Input
              id="upnp-lease-duration"
              type="number"
              inputMode="numeric"
              min={0}
              value={Number.isFinite(values.lease_duration) ? values.lease_duration : 0}
              onChange={(event) =>
                setValues((current) => ({
                  ...current,
                  lease_duration: Number.parseInt(event.target.value || "0", 10),
                }))
              }
              disabled={isSubmitting}
              aria-invalid={Boolean(errors.lease_duration)}
            />
            {errors.lease_duration ? <p className="text-destructive text-xs">{errors.lease_duration}</p> : null}
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
