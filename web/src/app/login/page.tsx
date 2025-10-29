"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";

import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const LOGIN_REDIRECT_DEFAULT = "/status";

export default function LoginPage() {
  const t = useTranslations("auth");
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextPath = searchParams?.get("next") || LOGIN_REDIRECT_DEFAULT;

  const { token, login, error, isAuthenticating } = useAuth();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (token) {
      router.replace(nextPath || LOGIN_REDIRECT_DEFAULT);
    }
  }, [token, router, nextPath]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError(null);
    const result = await login(username.trim(), password);
    if (result.success) {
      router.replace(nextPath || LOGIN_REDIRECT_DEFAULT);
    } else if (result.message) {
      setFormError(result.message);
    }
  };

  if (token) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-muted/10 px-4 py-10">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>{t("redirecting")}</CardTitle>
            <CardDescription>{t("redirectingDescription")}</CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-muted/10 px-4 py-10">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>{t("title")}</CardTitle>
          <CardDescription>{t("description")}</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="username">
                {t("username")}
              </label>
              <Input
                id="username"
                name="username"
                autoComplete="username"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="password">
                {t("password")}
              </label>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </div>
            {(formError ?? error) ? (
              <p className="text-sm text-destructive">{formError ?? error}</p>
            ) : null}
            <Button className="w-full" type="submit" disabled={isAuthenticating}>
              {isAuthenticating ? t("loggingIn") : t("submit")}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex items-center justify-between text-sm text-muted-foreground">
          <span>{t("noAccountPrompt")}</span>
          <Link href="/" className="text-primary hover:underline">
            {t("backHome")}
          </Link>
        </CardFooter>
      </Card>
    </div>
  );
}
