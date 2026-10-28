"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { accessRequest } from "@/components/access/access-api";
import { ApiClientError, getErrorMessage } from "@/lib/api-client";
import type { AccessState } from "@/types/access";

export function useAccessState() {
  const [data, setData] = useState<AccessState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [permissionDenied, setPermissionDenied] = useState(false);
  const requestRef = useRef<AbortController | null>(null);
  const mountedRef = useRef(false);
  const intervalRef = useRef(30);

  const reload = useCallback(async () => {
    requestRef.current?.abort();
    const controller = new AbortController();
    requestRef.current = controller;
    try {
      const result = await accessRequest<AccessState>("/state", { signal: controller.signal });
      if (controller.signal.aborted || !mountedRef.current) return;
      intervalRef.current = Math.max(10, result.poll_interval_seconds || 30);
      setData(result);
      setError(null);
      setPermissionDenied(false);
    } catch (cause) {
      if (!controller.signal.aborted && mountedRef.current) {
        setError(getErrorMessage(cause));
        setPermissionDenied(cause instanceof ApiClientError && cause.status === 403);
      }
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      await reload();
      if (mountedRef.current) timer = setTimeout(poll, intervalRef.current * 1000);
    };
    void poll();
    return () => {
      mountedRef.current = false;
      clearTimeout(timer);
      requestRef.current?.abort();
    };
  }, [reload]);

  return { data, error, permissionDenied, reload };
}
