import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/layout/header";
import { LanguageProvider } from "@/components/providers/language-provider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: {
    template: "%s | PandaHome",
    default: "PandaHome - 懒人开发者的家庭服务器",
  },
  description: "一个懒人开发者的家庭服务器管理解决方案，集成了阿里云 DNS API 动态 DDNS 和 UPnP 自动端口映射功能。",

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