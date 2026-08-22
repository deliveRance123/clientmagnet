"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import {
  disconnectSocialAccount,
  getSocialAccounts,
  handleProgrammaticOAuthCallback,
  initiateSocialConnect,
  refreshSocialAccountToken,
} from "@/lib/api";
import { SocialAccountConnection, SocialConnectionStatus } from "@/types";
import {
  Share2,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Unlink,
  Link as LinkIcon,
  ShieldCheck,
  ExternalLink,
  Loader2,
  Sparkles,
  Info,
  ChevronRight,
  Shield,
  Layers,
  Lock,
} from "lucide-react";

interface PlatformMeta {
  id: string;
  name: string;
  category: string;
  color: string;
  border: string;
  bg: string;
  iconText: string;
  description: string;
  requiredScopes: string[];
}

const PLATFORMS_META: PlatformMeta[] = [
  {
    id: "FACEBOOK",
    name: "Facebook Page",
    category: "Meta Business",
    color: "text-blue-600",
    border: "border-blue-200",
    bg: "bg-blue-50/50",
    iconText: "FB",
    description: "Manage client inquiries, organic posts, and business page interactions.",
    requiredScopes: ["pages_show_list", "pages_read_engagement", "pages_manage_posts"],
  },
  {
    id: "INSTAGRAM",
    name: "Instagram Professional",
    category: "Meta Business",
    color: "text-pink-600",
    border: "border-pink-200",
    bg: "bg-pink-50/50",
    iconText: "IG",
    description: "Connect Instagram Creator / Business accounts for content and direct inquiries.",
    requiredScopes: ["instagram_basic", "instagram_manage_comments"],
  },
  {
    id: "X",
    name: "X (Twitter)",
    category: "X Developer API v2",
    color: "text-slate-900",
    border: "border-slate-300",
    bg: "bg-slate-50",
    iconText: "X",
    description: "Official OAuth 2.0 PKCE connection for tweet scouting and brand engagement.",
    requiredScopes: ["tweet.read", "tweet.write", "users.read", "offline.access"],
  },
  {
    id: "LINKEDIN",
    name: "LinkedIn",
    category: "LinkedIn Official API",
    color: "text-sky-700",
    border: "border-sky-200",
    bg: "bg-sky-50/50",
    iconText: "IN",
    description: "B2B client engagement, executive outreach, and company page posts.",
    requiredScopes: ["openid", "profile", "email", "w_member_social"],
  },
  {
    id: "TIKTOK",
    name: "TikTok",
    category: "TikTok Login Kit",
    color: "text-rose-600",
    border: "border-rose-200",
    bg: "bg-rose-50/50",
    iconText: "TT",
    description: "Short-form video creator profile connection and audience interactions.",
    requiredScopes: ["user.info.basic", "video.list"],
  },
];

export default function SocialConnectedAccountsPage() {
  const { token, user } = useAuth();
  const [accounts, setAccounts] = useState<SocialAccountConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchAccounts = async () => {
    if (!token) return;
    try {
      setLoading(true);
      setErrorMsg(null);
      const data = await getSocialAccounts(token);
      setAccounts(data);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load connected social accounts.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, [token]);

  // Handle Connect Click
  const handleConnect = async (platformId: string) => {
    if (!token) return;
    try {
      setActionLoading(platformId);
      setErrorMsg(null);
      setSuccessMsg(null);

      const initData = await initiateSocialConnect(token, platformId);

      // In mock mode or dev, execute programmatic exchange immediately
      if (initData.authorization_url.includes("mock_oauth_code")) {
        const urlObj = new URL(initData.authorization_url, "http://localhost");
        const code = urlObj.searchParams.get("code") || "mock_code";
        const state = urlObj.searchParams.get("state") || initData.state;

        const connected = await handleProgrammaticOAuthCallback(token, platformId, code, state);
        setSuccessMsg(`Successfully connected ${platformId} account (${connected.account_name})!`);
        await fetchAccounts();
      } else {
        // Redirect to real OAuth platform dialog
        window.location.href = initData.authorization_url;
      }
    } catch (err: any) {
      setErrorMsg(err.message || `Failed to connect ${platformId}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Handle Disconnect
  const handleDisconnect = async (accountId: string, platformName: string) => {
    if (!token) return;
    if (!confirm(`Are you sure you want to disconnect your ${platformName} account?`)) return;

    try {
      setActionLoading(accountId);
      setErrorMsg(null);
      setSuccessMsg(null);
      await disconnectSocialAccount(token, accountId);
      setSuccessMsg(`Successfully disconnected ${platformName} account.`);
      await fetchAccounts();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to disconnect account.");
    } finally {
      setActionLoading(null);
    }
  };

  // Handle Refresh Token
  const handleRefresh = async (accountId: string, platformName: string) => {
    if (!token) return;
    try {
      setActionLoading(`refresh_${accountId}`);
      setErrorMsg(null);
      setSuccessMsg(null);
      const res = await refreshSocialAccountToken(token, accountId);
      setSuccessMsg(`Successfully refreshed tokens for ${platformName}!`);
      await fetchAccounts();
    } catch (err: any) {
      setErrorMsg(err.message || `Failed to refresh token: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const getAccountForPlatform = (platformId: string): SocialAccountConnection | undefined => {
    return accounts.find((a) => a.platform.toUpperCase() === platformId.toUpperCase() && a.connection_status === "CONNECTED");
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Share2 className="h-7 w-7 text-indigo-600" />
            Connected Social Accounts
          </h1>
          <p className="text-sm text-slate-500">
            Securely authorize and manage official platform integrations for Facebook, Instagram, X, LinkedIn, and TikTok.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/settings"
            className="rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-sm"
          >
            Settings
          </Link>
          <button
            onClick={fetchAccounts}
            disabled={loading}
            className="rounded-lg bg-slate-900 px-3.5 py-2 text-xs font-semibold text-white hover:bg-slate-800 shadow-sm flex items-center gap-1.5"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh Status
          </button>
        </div>
      </div>

      {/* Notifications */}
      {successMsg && (
        <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-xs font-semibold text-emerald-800 animate-in fade-in">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs font-semibold text-rose-800 animate-in fade-in">
          <AlertCircle className="h-4 w-4 text-rose-600 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Security & Compliance Banner */}
      <div className="rounded-xl border border-indigo-100 bg-indigo-50/50 p-4 text-xs text-indigo-900 flex items-start gap-3 shadow-sm">
        <ShieldCheck className="h-5 w-5 text-indigo-600 flex-shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-bold">Enterprise OAuth 2.0 & Token Encryption</p>
          <p className="text-indigo-700 leading-relaxed">
            Client Magnet exclusively utilizes official platform OAuth dialogs. Your passwords and credentials are never handled by our servers. All granted access tokens are encrypted at rest with AES-256 Fernet encryption and are never exposed to browser frontends.
          </p>
        </div>
      </div>

      {/* Platform Cards Grid */}
      <div className="grid gap-5 md:grid-cols-2">
        {PLATFORMS_META.map((meta) => {
          const connectedAccount = getAccountForPlatform(meta.id);
          const isConnected = !!connectedAccount;
          const isActionBusy = actionLoading === meta.id || actionLoading === connectedAccount?.id || actionLoading === `refresh_${connectedAccount?.id}`;

          return (
            <div
              key={meta.id}
              className={`rounded-2xl border bg-white p-6 shadow-sm flex flex-col justify-between transition-all ${
                isConnected ? "border-emerald-200 ring-1 ring-emerald-500/20" : "border-slate-200 hover:border-slate-300"
              }`}
            >
              <div className="space-y-4">
                {/* Platform Header & Badge */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className={`flex h-11 w-11 items-center justify-center rounded-xl font-black text-sm shadow-sm ${meta.bg} ${meta.color} ${meta.border} border`}
                    >
                      {meta.iconText}
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-900 text-base">{meta.name}</h3>
                      <span className="text-[11px] font-medium text-slate-400">{meta.category}</span>
                    </div>
                  </div>

                  <span
                    className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-bold border ${
                      isConnected
                        ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                        : "bg-slate-100 text-slate-600 border-slate-200"
                    }`}
                  >
                    {isConnected ? (
                      <>
                        <CheckCircle2 className="h-3 w-3 text-emerald-600" /> Connected
                      </>
                    ) : (
                      "Not Connected"
                    )}
                  </span>
                </div>

                <p className="text-xs text-slate-500 leading-relaxed">{meta.description}</p>

                {/* Connected Account Details */}
                {connectedAccount && (
                  <div className="rounded-xl bg-slate-50 p-3.5 border border-slate-100 space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500 font-medium">Account Profile:</span>
                      <span className="font-bold text-slate-900">{connectedAccount.account_name}</span>
                    </div>
                    {connectedAccount.account_username && (
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500 font-medium">Username / Handle:</span>
                        <span className="font-mono text-slate-700">{connectedAccount.account_username}</span>
                      </div>
                    )}
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500 font-medium">Connected On:</span>
                      <span className="text-slate-600">
                        {new Date(connectedAccount.created_at).toLocaleDateString()}
                      </span>
                    </div>

                    {/* Scopes Badges */}
                    {connectedAccount.scopes && connectedAccount.scopes.length > 0 && (
                      <div className="pt-1.5 border-t border-slate-200/60">
                        <span className="text-[11px] text-slate-400 font-medium block mb-1">
                          Authorized Permissions:
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {connectedAccount.scopes.map((scope, idx) => (
                            <span
                              key={idx}
                              className="rounded bg-white px-1.5 py-0.5 text-[10px] font-mono text-slate-600 border border-slate-200"
                            >
                              {scope}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="pt-5 mt-4 border-t border-slate-100 flex items-center justify-between">
                {isConnected ? (
                  <div className="flex items-center gap-2 w-full justify-between">
                    <button
                      onClick={() => handleRefresh(connectedAccount.id, meta.name)}
                      disabled={isActionBusy}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                      title="Verify and refresh token"
                    >
                      {actionLoading === `refresh_${connectedAccount.id}` ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <RefreshCw className="h-3.5 w-3.5" />
                      )}
                      Refresh Token
                    </button>

                    <button
                      onClick={() => handleDisconnect(connectedAccount.id, meta.name)}
                      disabled={isActionBusy}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs font-bold text-rose-700 hover:bg-rose-100 disabled:opacity-50"
                    >
                      {actionLoading === connectedAccount.id ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Unlink className="h-3.5 w-3.5" />
                      )}
                      Disconnect
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => handleConnect(meta.id)}
                    disabled={isActionBusy}
                    className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-xs font-bold text-white hover:bg-slate-800 disabled:opacity-50 transition shadow-sm"
                  >
                    {isActionBusy ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <LinkIcon className="h-4 w-4" />
                    )}
                    {isActionBusy ? `Authorizing ${meta.name}...` : `Connect ${meta.name}`}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
