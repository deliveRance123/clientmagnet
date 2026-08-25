"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from "react";
import { useRouter } from "next/navigation";
import { getApiBase, resilientFetch } from "./api-config";

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
  otp?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (payload: RegisterPayload) => Promise<{ success: boolean; error?: string }>;
  loginWithGoogle: (payload: { code?: string; state?: string; redirect_uri?: string; id_token?: string }) => Promise<{ success: boolean; error?: string }>;
  initiateGoogleLogin: (customRedirectUri?: string) => Promise<void>;
  sendOTP: (email: string, purpose?: string) => Promise<{ success: boolean; message?: string; error?: string }>;
  verifyOTP: (email: string, otp: string, purpose?: string) => Promise<{ success: boolean; message?: string; error?: string }>;
  loginWithOTP: (email: string, otp: string) => Promise<{ success: boolean; error?: string }>;
  forgotPassword: (email: string) => Promise<{ success: boolean; message?: string; error?: string }>;
  resetPasswordWithOTP: (payload: { email: string; otp: string; new_password: string }) => Promise<{ success: boolean; message?: string; error?: string }>;
  setDirectAuth: (token: string, user: User) => void;
  logout: () => Promise<void>;
  updateProfile: (data: { full_name?: string; company_name?: string }) => Promise<{ success: boolean; error?: string }>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Non-blocking user fetch with unauthorized detection
  const fetchCurrentUser = useCallback(async (jwtToken: string): Promise<{ user: User | null; unauthorized: boolean }> => {
    try {
      const res = await resilientFetch("/auth/me", {
        headers: {
          Authorization: `Bearer ${jwtToken}`,
        },
      });
      if (res.ok) {
        const u = await res.json();
        return { user: u, unauthorized: false };
      }
      if (res.status === 401 || res.status === 403) {
        return { user: null, unauthorized: true };
      }
      return { user: null, unauthorized: false };
    } catch (err) {
      console.warn("Error fetching current user:", err);
      return { user: null, unauthorized: false };
    }
  }, []);

  const refreshSession = useCallback(async (): Promise<boolean> => {
    try {
      const res = await resilientFetch("/auth/refresh", {
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

  // Fast initialization
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
              fetchCurrentUser(savedToken).then(({ user: freshUser, unauthorized }) => {
                if (isMounted) {
                  if (freshUser) {
                    setUser(freshUser);
                    localStorage.setItem("cm_user", JSON.stringify(freshUser));
                  } else if (unauthorized) {
                    // Only log out if the server explicitly returned 401/403
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
      const res = await resilientFetch("/auth/login", {
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
        error: "Unable to connect to the backend server. If running on Render Free tier, please wait 30-40s for the server to wake up and try again.",
      };
    }
  };

  const register = async (payload: RegisterPayload) => {
    try {
      const res = await resilientFetch("/auth/register", {
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
        error: "Unable to connect to the backend server. Please try again in a moment.",
      };
    }
  };

  const initiateGoogleLogin = async (customRedirectUri?: string) => {
    try {
      const redirectUri =
        customRedirectUri ||
        (typeof window !== "undefined"
          ? `${window.location.origin}/auth/callback`
          : "http://localhost:3000/auth/callback");

      const res = await resilientFetch(
        `/auth/google/url?redirect_uri=${encodeURIComponent(redirectUri)}`
      );

      if (res.ok) {
        const data = await res.json();
        if (data.authorization_url && typeof window !== "undefined") {
          window.location.href = data.authorization_url;
        }
      } else {
        // Direct mock fallback for local dev
        if (typeof window !== "undefined") {
          window.location.href = `${redirectUri}?code=mock_google_auth_code_999`;
        }
      }
    } catch (err) {
      console.warn("Failed to initiate Google OAuth, falling back to callback:", err);
      if (typeof window !== "undefined") {
        window.location.href = `${window.location.origin}/auth/callback?code=mock_google_auth_code_999`;
      }
    }
  };

  const loginWithGoogle = async (payload: {
    code?: string;
    state?: string;
    redirect_uri?: string;
    id_token?: string;
  }) => {
    try {
      const redirectUri =
        payload.redirect_uri ||
        (typeof window !== "undefined"
          ? `${window.location.origin}/auth/callback`
          : "http://localhost:3000/auth/callback");

      const res = await resilientFetch("/auth/google", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          ...payload,
          redirect_uri: redirectUri,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        return {
          success: false,
          error: data.detail || "Google authentication failed. Please try again.",
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
        error: "Unable to connect to backend server during Google authentication.",
      };
    }
  };

  const sendOTP = async (email: string, purpose: string = "registration") => {
    try {
      const res = await resilientFetch("/auth/otp/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), purpose }),
      });
      const data = await res.json();
      if (!res.ok) {
        return {
          success: false,
          error: data.detail || "Failed to send verification code. Please try again.",
        };
      }
      return { success: true, message: data.message };
    } catch (err) {
      return {
        success: false,
        error: "Unable to reach server. Please check your network connection.",
      };
    }
  };

  const verifyOTP = async (email: string, otp: string, purpose: string = "registration") => {
    try {
      const res = await resilientFetch("/auth/otp/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), otp: otp.trim(), purpose }),
      });
      const data = await res.json();
      if (!res.ok) {
        return {
          success: false,
          error: data.detail || "Invalid verification code. Please try again.",
        };
      }
      return { success: true, message: data.message };
    } catch (err) {
      return {
        success: false,
        error: "Unable to reach server. Please check your network connection.",
      };
    }
  };

  const loginWithOTP = async (email: string, otp: string) => {
    try {
      const res = await resilientFetch("/auth/otp/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email: email.trim(), otp: otp.trim() }),
      });
      const data = await res.json();
      if (!res.ok) {
        return {
          success: false,
          error: data.detail || "Authentication failed. Please verify your OTP code.",
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
        error: "Unable to reach server. Please check your network connection.",
      };
    }
  };

  const forgotPassword = async (email: string) => {
    try {
      const res = await resilientFetch("/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim() }),
      });
      const data = await res.json();
      if (!res.ok) {
        return {
          success: false,
          error: data.detail || "Failed to send reset code.",
        };
      }
      return { success: true, message: data.message };
    } catch (err) {
      return {
        success: false,
        error: "Unable to reach server. Please check your network connection.",
      };
    }
  };

  const resetPasswordWithOTP = async (payload: { email: string; otp: string; new_password: string }) => {
    try {
      const res = await resilientFetch("/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: payload.email.trim(),
          otp: payload.otp.trim(),
          new_password: payload.new_password,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        return {
          success: false,
          error: data.detail || "Failed to reset password. Please try again.",
        };
      }
      return { success: true, message: data.message };
    } catch (err) {
      return {
        success: false,
        error: "Unable to reach server. Please check your network connection.",
      };
    }
  };

  const setDirectAuth = (jwtToken: string, authUser: User) => {
    setToken(jwtToken);
    setUser(authUser);
    if (typeof window !== "undefined") {
      localStorage.setItem("cm_access_token", jwtToken);
      localStorage.setItem("cm_user", JSON.stringify(authUser));
    }
  };

  const logout = async () => {
    try {
      await resilientFetch("/auth/logout", {
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
      const res = await resilientFetch("/auth/me", {
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
      const { user: u } = await fetchCurrentUser(token);
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
        loginWithGoogle,
        initiateGoogleLogin,
        sendOTP,
        verifyOTP,
        loginWithOTP,
        forgotPassword,
        resetPasswordWithOTP,
        setDirectAuth,
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
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
