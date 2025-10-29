"use client"

import Link from "next/link";
import { useTranslations } from "next-intl";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/components/providers/auth-provider";

export function UserNav() {
  const { token, user, logout, isAuthenticating } = useAuth();
  const t = useTranslations("auth");

  if (!token) {
    return (
      <Button variant="ghost" asChild>
        <Link href="/login">{t("login")}</Link>
      </Button>
    );
  }

  const handleLogout = (event: Event) => {
    event.preventDefault();
    if (!isAuthenticating) {
      logout();
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="relative h-8 w-8 rounded-full">
          <span className="sr-only">{t("openMenu")}</span>
          <div className="h-8 w-8 rounded-full bg-muted" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="end" forceMount>
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">{user?.username ?? t("unknownUser")}</p>
            <p className="text-xs leading-none text-muted-foreground">{user?.email ?? ""}</p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={handleLogout}>
          {t("logout")}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
