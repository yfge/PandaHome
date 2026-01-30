import { Suspense } from "react";

import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

import { LoginClient } from "./login-client";

function LoginFallback() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-muted/10 px-4 py-10">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Loading</CardTitle>
          <CardDescription>Preparing sign-in...</CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<LoginFallback />}>
      <LoginClient />
    </Suspense>
  );
}
