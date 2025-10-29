"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";

import {
  apiClient,
  getErrorMessage,
  isApiEnvelope,
  setAuthToken,
  type ApiEnvelope,
} from "@/lib/api-client";

const TOKEN_STORAGE_KEY = "pandahome.auth.token";

export type AuthRole = "admin" | "user" | "guest";

export interface AuthUser {
  username: string;
  email: string;
  role: AuthRole;
}

interface AuthContextValue {
  token: string | null;
  user: AuthUser | null;
  isBootstrapping: boolean;
  isAuthenticating: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<{ success: boolean; message?: string }>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

async function fetchCurrentUser(): Promise<AuthUser> {
  const response = await apiClient<AuthUser | ApiEnvelope<AuthUser>>("/api/users/me");
  if (isApiEnvelope<AuthUser>(response)) {
    if (response.code !== 0) {
      throw new Error(response.message ?? "Failed to load user");
    }
    if (!response.data) {
      throw new Error("Missing user payload");
    }
    return response.data;
  }
  return response;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [token, setTokenState] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [isAuthenticating, setIsAuthenticating] = useState(false);

  const applyToken = useCallback((value: string | null) => {
    setTokenState(value);
    setAuthToken(value);
    if (value) {
      localStorage.setItem(TOKEN_STORAGE_KEY, value);
    } else {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
    }
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const profile = await fetchCurrentUser();
      setUser(profile);
    } catch (err) {
      const message = getErrorMessage(err, "Failed to load user");
      setError(message);
      applyToken(null);
      setUser(null);
      throw err;
    }
  }, [applyToken]);

  useEffect(() => {
    const stored = typeof window !== "undefined" ? localStorage.getItem(TOKEN_STORAGE_KEY) : null;
    if (!stored) {
      setIsBootstrapping(false);
      return;
    }

    applyToken(stored);

    fetchCurrentUser()
      .then((profile) => {
        setUser(profile);
        setIsBootstrapping(false);
      })
      .catch(() => {
        applyToken(null);
        setUser(null);
        setIsBootstrapping(false);
      });
  }, [applyToken]);

  const login = useCallback(
    async (username: string, password: string) => {
      setIsAuthenticating(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        params.set("username", username);
        params.set("password", password);

        const response = await apiClient<{ access_token: string; token_type: string }>(
          "/api/auth/token",
          {
            method: "POST",
            body: params,
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            includeAuth: false,
          },
        );

        const accessToken = response.access_token;
        if (!accessToken) {
          throw new Error("Missing access token");
        }

        applyToken(accessToken);
        await refreshUser();
        return { success: true as const };
      } catch (err) {
        const message = getErrorMessage(err, "登录失败");
        setError(message);
        applyToken(null);
        setUser(null);
        return { success: false as const, message };
      } finally {
        setIsAuthenticating(false);
      }
    },
    [applyToken, refreshUser],
  );

  const logout = useCallback(() => {
    applyToken(null);
    setUser(null);
    setError(null);
    router.replace("/login");
  }, [applyToken, router]);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user,
      error,
      isBootstrapping,
      isAuthenticating,
      login,
      logout,
      refreshUser,
    }),
    [token, user, error, isBootstrapping, isAuthenticating, login, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
