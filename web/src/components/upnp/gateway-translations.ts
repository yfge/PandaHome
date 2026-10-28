import { createTranslator, useLocale } from "next-intl";
import { useMemo } from "react";

import en from "@/i18n/locales/upnp-gateways/en.json";
import zh from "@/i18n/locales/upnp-gateways/zh.json";

export function useGatewayTranslations() {
  const locale = useLocale();
  return useMemo(() => createTranslator({ locale, messages: locale === "zh" ? zh : en }), [locale]);
}
