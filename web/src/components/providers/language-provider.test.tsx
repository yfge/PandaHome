import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useTranslations } from "next-intl";
import { afterEach, describe, expect, it } from "vitest";

import { LanguageProvider, useLanguage } from "@/components/providers/language-provider";
import en from "@/i18n/locales/en.json";
import zh from "@/i18n/locales/zh.json";

function LanguageControls() {
  const { setLocale } = useLanguage();
  const t = useTranslations("common");
  return <>
    <p>{t("welcome")}</p>
    <button onClick={() => setLocale("en")}>English</button>
    <button onClick={() => setLocale("zh")}>中文</button>
  </>;
}

const preview = () => render(<LanguageProvider initialMessages={zh}><LanguageControls /></LanguageProvider>);

afterEach(() => {
  cleanup();
  localStorage.removeItem("locale");
  document.documentElement.lang = "zh";
});

describe("document language", () => {
  it("follows the visible language when switching in either direction", async () => {
    preview();
    fireEvent.click(screen.getByRole("button", { name: "English" }));
    await waitFor(() => expect(document.documentElement.lang).toBe("en"));
    await screen.findByText(en.common.welcome);
    fireEvent.click(screen.getByRole("button", { name: "中文" }));
    await waitFor(() => expect(document.documentElement.lang).toBe("zh"));
    await screen.findByText(zh.common.welcome);
  });

  it("restores the saved document language after reopening the page", async () => {
    localStorage.setItem("locale", "en");
    const first = preview();
    await waitFor(() => expect(document.documentElement.lang).toBe("en"));
    await screen.findByText(en.common.welcome);
    first.unmount();
    preview();
    await waitFor(() => expect(document.documentElement.lang).toBe("en"));
    await screen.findByText(en.common.welcome);
  });
});
