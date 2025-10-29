"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { NextIntlClientProvider, type AbstractIntlMessages } from "next-intl";

const LanguageContext = createContext<{
  locale: string;
  setLocale: (locale: string) => void;
}>({
  locale: "zh",
  setLocale: () => {},
});

export function LanguageProvider({
  children,
  initialMessages,
}: {
  children: React.ReactNode;
  initialMessages: AbstractIntlMessages;
}) {
  const [locale, setLocale] = useState("zh");
  const [messages, setMessages] = useState<AbstractIntlMessages>(initialMessages);

  useEffect(() => {
    // 从 localStorage 获取保存的语言设置
    const savedLocale = localStorage.getItem("locale");
    if (savedLocale) {
      setLocale(savedLocale);
      // 动态加载语言文件
      import(`@/i18n/locales/${savedLocale}.json`).then((module) => {
        setMessages(module.default as AbstractIntlMessages);
      });
    }
  }, []);

  const handleSetLocale = async (newLocale: string) => {
    setLocale(newLocale);
    localStorage.setItem("locale", newLocale);
    // 动态加载新的语言文件
    const newMessages = await import(`@/i18n/locales/${newLocale}.json`);
    setMessages(newMessages.default as AbstractIntlMessages);
  };

  return (
    <LanguageContext.Provider value={{ locale, setLocale: handleSetLocale }}>
      <NextIntlClientProvider locale={locale} messages={messages}>
        {children}
      </NextIntlClientProvider>
    </LanguageContext.Provider>
  );
}

export const useLanguage = () => useContext(LanguageContext); 
