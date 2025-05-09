import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/layout/header";
import { LanguageProvider } from "@/components/providers/language-provider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Self Host Server",
  description: "Self Host Server Dashboard",
};

async function getInitialMessages() {
  // 默认使用中文
  return (await import("@/i18n/locales/zh.json")).default;
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const initialMessages = await getInitialMessages();

  return (
    <html lang="zh">
      <body className={inter.className}>
        <LanguageProvider initialMessages={initialMessages}>
          <div className="relative flex min-h-screen flex-col">
            <Header />
            <main className="flex-1">{children}</main>
          </div>
        </LanguageProvider>
      </body>
    </html>
  );
} 