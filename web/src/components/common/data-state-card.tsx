"use client";

import { ReactNode } from "react";
import { Button, type ButtonProps } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type DataStateVariant = "error" | "empty";

interface DataStateAction extends Pick<ButtonProps, "variant" | "onClick"> {
  label: string;
}

interface DataStateCardProps {
  title: string;
  description?: string;
  variant?: DataStateVariant;
  action?: DataStateAction;
  children?: ReactNode;
}

export function DataStateCard({
  title,
  description,
  variant = "empty",
  action,
  children,
}: DataStateCardProps) {
  return (
    <Card className="text-center">
      <CardHeader>
        <CardTitle className={cn("text-base font-semibold", variant === "error" && "text-destructive")}>
          {title}
        </CardTitle>
        {description ? <CardDescription>{description}</CardDescription> : null}
      </CardHeader>
      {action || children ? (
        <CardContent>
          <div className="flex flex-col items-center justify-center gap-4">
            {children}
            {action ? (
              <Button
                variant={action.variant ?? (variant === "error" ? "destructive" : "default")}
                onClick={action.onClick}
              >
                {action.label}
              </Button>
            ) : null}
          </div>
        </CardContent>
      ) : null}
    </Card>
  );
}
