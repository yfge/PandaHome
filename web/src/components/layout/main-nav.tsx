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
    <nav className="flex items-center space-x-4 lg:space-x-6">
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
