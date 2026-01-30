"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { XIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type ToastVariant = "default" | "success" | "error";

export interface ToastOptions {
  title: string;
  description?: string;
  variant?: ToastVariant;
  durationMs?: number;
}

interface ToastItem extends Required<Pick<ToastOptions, "title">> {
  id: string;
  description?: string;
  variant: ToastVariant;
  durationMs: number;
}

interface ToastContextValue {
  toast: (options: ToastOptions) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

function createToastId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function getVariantClasses(variant: ToastVariant): string {
  switch (variant) {
    case "success":
      return "border-emerald-500/20 bg-emerald-500/10";
    case "error":
      return "border-destructive/30 bg-destructive/10";
    default:
      return "";
  }
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const timeoutsRef = useRef<Map<string, number>>(new Map());

  const dismiss = useCallback((id: string) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
    const timeoutId = timeoutsRef.current.get(id);
    if (timeoutId) {
      window.clearTimeout(timeoutId);
      timeoutsRef.current.delete(id);
    }
  }, []);

  const toast = useCallback(
    ({ title, description, variant = "default", durationMs = 4000 }: ToastOptions) => {
      const id = createToastId();
      const item: ToastItem = { id, title, description, variant, durationMs };
      setToasts((current) => [...current, item]);

      const timeoutId = window.setTimeout(() => {
        dismiss(id);
      }, durationMs);
      timeoutsRef.current.set(id, timeoutId);
    },
    [dismiss],
  );

  useEffect(() => {
    const timeouts = timeoutsRef.current;
    return () => {
      timeouts.forEach((timeoutId) => window.clearTimeout(timeoutId));
      timeouts.clear();
    };
  }, []);

  const value = useMemo<ToastContextValue>(() => ({ toast }), [toast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed top-4 right-4 z-50 flex w-[calc(100%-2rem)] max-w-sm flex-col gap-2">
        {toasts.map((item) => (
          <div
            key={item.id}
            role="status"
            className={cn(
              "bg-card text-card-foreground animate-in fade-in slide-in-from-top-2 rounded-lg border p-4 shadow-lg",
              getVariantClasses(item.variant),
            )}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="font-medium leading-none">{item.title}</p>
                {item.description ? (
                  <p className="text-muted-foreground mt-1 text-sm">{item.description}</p>
                ) : null}
              </div>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-7 w-7 shrink-0"
                onClick={() => dismiss(item.id)}
                aria-label="Dismiss"
              >
                <XIcon className="h-4 w-4" />
              </Button>
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}
