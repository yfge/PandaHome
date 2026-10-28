import { createTranslator, useLocale } from "next-intl";
import { useMemo } from "react";

import en from "@/i18n/locales/p2p/en.json";
import zh from "@/i18n/locales/p2p/zh.json";

export function useP2pTranslations() {
  const locale = useLocale();
  return useMemo(() => createTranslator({ locale, messages: locale === "zh" ? zh : en }), [locale]);
}
