"use client"

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";

import { useAuth } from "@/components/providers/auth-provider";
import { cn } from "@/lib/utils";

export function MainNav() {
  const pathname = usePathname();
  const t = useTranslations("common");
  const { token } = useAuth();

  return (
    <nav aria-label={t("navigation")} className="flex min-w-0 flex-1 items-center gap-4 overflow-x-auto py-3 pr-4 whitespace-nowrap lg:gap-6">
      <Link
        href="/"
        className={cn(
          "text-sm font-medium transition-colors hover:text-primary",
          pathname === "/" ? "text-primary" : "text-muted-foreground"
        )}
      >
        {t("home")}
      </Link>
      {token ? (
        <>
          <Link
            href="/access"
            className={cn(
              "text-sm font-medium transition-colors hover:text-primary",
              pathname === "/access" ? "text-primary" : "text-muted-foreground"
            )}
          >
            {t("access")}
          </Link>
          <Link
            href="/status"
            className={cn(
              "text-sm font-medium transition-colors hover:text-primary",
              pathname === "/status" ? "text-primary" : "text-muted-foreground"
            )}
          >
            {t("status")}
          </Link>
          <Link
            href="/upnp"
            className={cn(
              "text-sm font-medium transition-colors hover:text-primary",
              pathname === "/upnp" ? "text-primary" : "text-muted-foreground"
            )}
          >
            {t("upnp")}
          </Link>
          <Link
            href="/domains"
            className={cn(
              "text-sm font-medium transition-colors hover:text-primary",
              pathname === "/domains" ? "text-primary" : "text-muted-foreground"
            )}
          >
            {t("domains")}
          </Link>
        </>
      ) : null}
    </nav>
  )
}
