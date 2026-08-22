"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from "react";
import { useRouter } from "next/navigation";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  company_name: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name?: string;
  company_name?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (payload: RegisterPayload) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  updateProfile: (data: { full_name?: string; company_name?: string }) => Promise<{ success: boolean; error?: string }>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const fetchCurrentUser = useCallback(async (jwtToken: string): Promise<User | null> => {
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: {
          Authorization: `Bearer ${jwtToken}`,
        },
      });
      if (res.ok) {
        return await res.json();
      }
      return null;
    } catch (err) {
      console.warn("Error fetching current user:", err);
      return null;
    }
  }, []);

  const refreshSession = useCallback(async (): Promise<boolean> => {
    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      });

      if (res.ok) {
        const data = await res.json();
        setToken(data.access_token);
        if (typeof window !== "undefined") {
          localStorage.setItem("cm_access_token", data.access_token);
          localStorage.setItem("cm_user", JSON.stringify(data.user));
        }
        setUser(data.user);
        return true;
      }
      return false;
    } catch (err) {
      return false;
    }
  }, []);

  // Lightning-fast initialization
  useEffect(() => {
    let isMounted = true;

    async function initAuth() {
      try {
        if (typeof window !== "undefined") {
          const savedToken = localStorage.getItem("cm_access_token");
          const savedUserStr = localStorage.getItem("cm_user");

          // Fast optimistic recovery: restore user immediately if cached
          if (savedToken && savedUserStr) {
            try {
              const parsedUser = JSON.parse(savedUserStr);
              if (isMounted) {
                setUser(parsedUser);
                setToken(savedToken);
                setLoading(false); // Instantly unblock UI
              }

              // Background non-blocking verification
              fetchCurrentUser(savedToken).then((freshUser) => {
                if (isMounted) {
                  if (freshUser) {
                    setUser(freshUser);
                    localStorage.setItem("cm_user", JSON.stringify(freshUser));
                  } else {
                    // Token expired, clear cache
                    setUser(null);
                    setToken(null);
                    localStorage.removeItem("cm_access_token");
                    localStorage.removeItem("cm_user");
                  }
                }
              });
              return;
            } catch (e) {
              // Parse error fallback
            }
          }
        }

        // If no token, finish loading immediately
        if (isMounted) {
          setLoading(false);
        }
      } catch (err) {
        if (isMounted) setLoading(false);
      }
    }

    initAuth();

    return () => {
      isMounted = false;
    };
  }, [fetchCurrentUser]);

  const login = async (email: string, password: string) => {
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        return {
          success: false,
          error: data.detail || "Authentication failed. Please check your credentials.",
        };
      }

      setToken(data.access_token);
      setUser(data.user);
      if (typeof window !== "undefined") {
        localStorage.setItem("cm_access_token", data.access_token);
        localStorage.setItem("cm_user", JSON.stringify(data.user));
      }
      return { success: true };
    } catch (err) {
      return {
        success: false,
        error: "Unable to connect to the server. Please try again later.",
      };
    }
  };

  const register = async (payload: RegisterPayload) => {
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        return {
          success: false,
          error: Array.isArray(data.detail)
            ? data.detail.map((d: any) => d.msg).join(", ")
            : data.detail || "Registration failed. Please check your details.",
        };
      }

      setToken(data.access_token);
      setUser(data.user);
      if (typeof window !== "undefined") {
        localStorage.setItem("cm_access_token", data.access_token);
        localStorage.setItem("cm_user", JSON.stringify(data.user));
      }
      return { success: true };
    } catch (err) {
      return {
        success: false,
        error: "Unable to connect to the server. Please try again later.",
      };
    }
  };

  const logout = async () => {
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
    } catch (err) {
      console.error("Logout error:", err);
    } finally {
      setUser(null);
      setToken(null);
      if (typeof window !== "undefined") {
        localStorage.removeItem("cm_access_token");
        localStorage.removeItem("cm_user");
      }
      router.push("/login");
    }
  };

  const updateProfile = async (data: { full_name?: string; company_name?: string }) => {
    if (!token) return { success: false, error: "Not authenticated" };

    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      });

      const updatedUser = await res.json();
      if (!res.ok) {
        return {
          success: false,
          error: updatedUser.detail || "Failed to update profile",
        };
      }

      setUser(updatedUser);
      if (typeof window !== "undefined") {
        localStorage.setItem("cm_user", JSON.stringify(updatedUser));
      }
      return { success: true };
    } catch (err) {
      return { success: false, error: "Network error occurred." };
    }
  };

  const refreshUser = async () => {
    if (token) {
      const u = await fetchCurrentUser(token);
      if (u) {
        setUser(u);
        if (typeof window !== "undefined") {
          localStorage.setItem("cm_user", JSON.stringify(u));
        }
      }
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        logout,
        updateProfile,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
