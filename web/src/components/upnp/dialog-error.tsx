"use client";

import { useEffect, useRef } from "react";
import { useTranslations } from "next-intl";

export type UpnpSubmissionError = { message: string };

export function UpnpDialogError({ error }: { error: UpnpSubmissionError | null }) {
  const t = useTranslations("upnp");
  const alertRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!error || !alertRef.current) return;
    const dialog = alertRef.current.closest('[role="dialog"]');
    // Reveal feedback inside the scrollable modal without moving the page.
    if (dialog) dialog.scrollTop = 0;
    alertRef.current.focus({ preventScroll: true });
  }, [error]);

  if (!error) return null;

  return (
    <div ref={alertRef} role="alert" tabIndex={-1}
      className="border-destructive/40 bg-destructive/10 text-destructive min-w-0 rounded-md border p-3 text-sm">
      <p className="font-medium">{t("failed")}</p>
      <p className="mt-1 break-words">{error.message}</p>
    </div>
  );
}
