"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import {
  connectWhatsAppAccount,
  disconnectWhatsAppAccount,
  getLeads,
  getUnifiedConversation,
  getUnifiedConversations,
  getWhatsAppAccounts,
  sendApprovedWhatsAppMessage,
  suggestWhatsAppReply,
} from "@/lib/api";
import {
  Lead,
  UnifiedConversation,
  WhatsAppAccount,
} from "@/types";
import {
  MessageSquare,
  Sparkles,
  Send,
  RefreshCw,
  Search,
  CheckCircle2,
  AlertCircle,
  Link as LinkIcon,
  Unlink,
  Plus,
  Loader2,
  ShieldCheck,
  Phone,
  User,
  Clock,
  Inbox,
  Building,
} from "lucide-react";

export default function WhatsAppPage() {
  const { token } = useAuth();

  // State
  const [accounts, setAccounts] = useState<WhatsAppAccount[]>([]);
  const [conversations, setConversations] = useState<UnifiedConversation[]>([]);
  const [selectedConv, setSelectedConv] = useState<UnifiedConversation | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);

  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [actionBusy, setActionBusy] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Connection Modal State
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [phoneId, setPhoneId] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [accessToken, setAccessToken] = useState("");

  // Reply State
  const [replyText, setReplyText] = useState("");
  const [sendingReply, setSendingReply] = useState(false);
  const [suggestingReply, setSuggestingReply] = useState(false);

  // Load Data
  const loadData = async () => {
    if (!token) return;
    try {
      setLoading(true);
      setErrorMsg(null);

      const [accountsData, convsData, leadsData] = await Promise.all([
        getWhatsAppAccounts(token).catch(() => []),
        getUnifiedConversations(token, { platform: "whatsapp" }).catch(() => []),
        getLeads(token).catch(() => []),
      ]);

      setAccounts(accountsData);
      setConversations(convsData);
      setLeads(leadsData);

      if (convsData.length > 0 && !selectedConv) {
        setSelectedConv(convsData[0]);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load WhatsApp data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token]);

  // Handle Connect
  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !phoneId.trim() || !phoneNumber.trim() || !accessToken.trim()) return;

    try {
      setActionBusy(true);
      setErrorMsg(null);
      await connectWhatsAppAccount(token, {
        phone_number_id: phoneId.trim(),
        phone_number: phoneNumber.trim(),
        display_name: displayName.trim() || undefined,
        access_token: accessToken.trim(),
      });

      setSuccessMsg("WhatsApp Business Account successfully connected!");
      setShowConnectModal(false);
      setPhoneId("");
      setPhoneNumber("");
      setAccessToken("");
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to connect WhatsApp account.");
    } finally {
      setActionBusy(false);
    }
  };

  // Handle Disconnect
  const handleDisconnect = async (accountId: string) => {
    if (!token) return;
    if (!confirm("Are you sure you want to disconnect this WhatsApp Business account?")) return;
    try {
      setActionBusy(true);
      await disconnectWhatsAppAccount(token, accountId);
      setSuccessMsg("WhatsApp Business account disconnected.");
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to disconnect account.");
    } finally {
      setActionBusy(false);
    }
  };

  // Select Conversation
  const handleSelectConversation = async (conv: UnifiedConversation) => {
    if (!token) return;
    try {
      const fullConv = await getUnifiedConversation(token, conv.id);
      setSelectedConv(fullConv);
      setConversations((prev) =>
        prev.map((c) => (c.id === conv.id ? { ...c, unread_count: 0 } : c))
      );
    } catch (err: any) {
      setSelectedConv(conv);
    }
  };

  // AI Suggest Reply
  const handleSuggestReply = async () => {
    if (!token || !selectedConv) return;
    try {
      setSuggestingReply(true);
      setErrorMsg(null);
      const res = await suggestWhatsAppReply(token, selectedConv.id);
      setReplyText(res.suggested_reply);
      setSuccessMsg("AI reply suggestion generated with Gemini!");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to suggest reply.");
    } finally {
      setSuggestingReply(false);
    }
  };

  // Send Approved Reply
  const handleSendReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !selectedConv || !replyText.trim()) return;

    const recipientPhone = selectedConv.external_conversation_id || selectedConv.lead?.phone;
    if (!recipientPhone) {
      alert("No valid recipient phone number for this conversation.");
      return;
    }

    try {
      setSendingReply(true);
      setErrorMsg(null);
      await sendApprovedWhatsAppMessage(token, {
        recipient_phone: recipientPhone,
        message_text: replyText.trim(),
        conversation_id: selectedConv.id,
        lead_id: selectedConv.lead_id || undefined,
      });

      setSuccessMsg("WhatsApp message dispatched successfully!");
      setReplyText("");
      const updated = await getUnifiedConversation(token, selectedConv.id);
      setSelectedConv(updated);
      setConversations((prev) =>
        prev.map((c) => (c.id === selectedConv.id ? updated : c))
      );
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to send WhatsApp message.");
    } finally {
      setSendingReply(false);
    }
  };

  const connectedAccount = accounts.find((a) => a.connection_status === "CONNECTED");

  const filteredConversations = conversations.filter((c) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      (c.subject && c.subject.toLowerCase().includes(q)) ||
      (c.lead && c.lead.name.toLowerCase().includes(q)) ||
      (c.external_conversation_id && c.external_conversation_id.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header & Connection Bar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <MessageSquare className="h-7 w-7 text-emerald-600" />
            WhatsApp Business Hub
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Official Meta WhatsApp Business Cloud API integration with AI reply suggestions and 24h compliance.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {connectedAccount ? (
            <div className="flex items-center gap-2 rounded-xl bg-emerald-50 px-3.5 py-2 border border-emerald-200">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs font-bold text-emerald-800">
                {connectedAccount.display_name || connectedAccount.phone_number}
              </span>
              <button
                onClick={() => handleDisconnect(connectedAccount.id)}
                disabled={actionBusy}
                className="ml-2 text-[11px] font-semibold text-rose-600 hover:text-rose-800 underline"
              >
                Disconnect
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowConnectModal(true)}
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-xs font-bold text-white hover:bg-emerald-700 shadow-sm"
            >
              <Phone className="h-4 w-4" />
              Connect WhatsApp Business API
            </button>
          )}

          <button
            onClick={loadData}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-sm"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
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

      {/* 2-Pane WhatsApp Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[720px]">
        {/* Left Pane: Conversation List */}
        <div className="lg:col-span-5 flex flex-col bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-3.5 border-b border-slate-100 bg-slate-50/50">
            <div className="relative">
              <Search className="h-4 w-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search WhatsApp phone numbers or leads..."
                className="w-full rounded-xl border border-slate-200 bg-white py-2 pl-9 pr-3 text-xs outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
            {loading ? (
              <div className="p-8 text-center text-xs text-slate-400">
                <Loader2 className="h-5 w-5 animate-spin mx-auto mb-2 text-emerald-500" />
                Loading WhatsApp conversations...
              </div>
            ) : filteredConversations.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">
                <Inbox className="h-8 w-8 mx-auto mb-2 text-slate-300" />
                No WhatsApp conversations recorded yet. Connect a number or trigger a webhook to start.
              </div>
            ) : (
              filteredConversations.map((conv) => {
                const isSelected = selectedConv?.id === conv.id;
                const lastMsg = conv.messages && conv.messages.length > 0 ? conv.messages[conv.messages.length - 1] : null;

                return (
                  <button
                    key={conv.id}
                    onClick={() => handleSelectConversation(conv)}
                    className={`w-full text-left p-4 transition-all flex flex-col gap-1.5 ${
                      isSelected
                        ? "bg-emerald-50/80 border-l-4 border-l-emerald-600"
                        : "hover:bg-slate-50/80"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 font-bold text-xs text-slate-900 truncate">
                        {conv.unread_count > 0 && (
                          <span className="h-2 w-2 rounded-full bg-emerald-600 flex-shrink-0" />
                        )}
                        <span>{conv.lead?.name || conv.external_conversation_id}</span>
                      </div>
                      <span className="text-[10px] text-slate-400 font-medium">
                        {conv.last_message_at
                          ? new Date(conv.last_message_at).toLocaleDateString([], { month: "short", day: "numeric" })
                          : "Recently"}
                      </span>
                    </div>

                    <p className="text-[11px] text-slate-600 line-clamp-1">
                      {lastMsg?.message_content || "No message recorded"}
                    </p>

                    <div className="flex items-center gap-2 mt-1">
                      {conv.lead ? (
                        <span className="rounded bg-emerald-100/70 px-1.5 py-0.5 text-[10px] font-medium text-emerald-800">
                          🎯 {conv.lead.name}
                        </span>
                      ) : (
                        <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-500">
                          Unlinked Lead
                        </span>
                      )}
                      <span className="text-[10px] text-slate-400">
                        {conv.messages?.length || 0} msgs
                      </span>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Right Pane: Thread View */}
        <div className="lg:col-span-7 flex flex-col bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          {selectedConv ? (
            <>
              {/* Header */}
              <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                    <Phone className="h-4 w-4 text-emerald-600" />
                    {selectedConv.lead?.name || selectedConv.external_conversation_id}
                  </h3>
                  <span className="text-xs text-slate-500">
                    Phone: <strong className="text-slate-700">{selectedConv.external_conversation_id}</strong>
                  </span>
                </div>

                <button
                  type="button"
                  onClick={handleSuggestReply}
                  disabled={suggestingReply}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-700 border border-emerald-200 hover:bg-emerald-100"
                >
                  {suggestingReply ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Sparkles className="h-3.5 w-3.5 text-emerald-600" />
                  )}
                  Suggest AI Reply
                </button>
              </div>

              {/* Messages Container */}
              <div className="flex-1 p-5 overflow-y-auto space-y-4 bg-emerald-50/20">
                {selectedConv.messages.length === 0 ? (
                  <div className="text-center py-12 text-xs text-slate-400">
                    No messages in this WhatsApp thread.
                  </div>
                ) : (
                  selectedConv.messages.map((msg) => {
                    const isOutbound = msg.direction === "outbound";
                    return (
                      <div
                        key={msg.id}
                        className={`flex flex-col ${isOutbound ? "items-end" : "items-start"}`}
                      >
                        <div
                          className={`max-w-[85%] rounded-2xl p-3.5 shadow-xs text-xs leading-relaxed space-y-1 ${
                            isOutbound
                              ? "bg-emerald-600 text-white rounded-br-none"
                              : "bg-white border border-slate-200 text-slate-900 rounded-bl-none"
                          }`}
                        >
                          <div className="whitespace-pre-wrap">{msg.message_content}</div>
                          <div
                            className={`text-[9px] text-right ${
                              isOutbound ? "text-emerald-200" : "text-slate-400"
                            }`}
                          >
                            {new Date(msg.sent_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          </div>
                        </div>
                        <span className="text-[10px] text-slate-400 mt-1 px-1">
                          {isOutbound ? "✓ Approved & Sent" : "Incoming via WhatsApp"}
                        </span>
                      </div>
                    );
                  })
                )}
              </div>

              {/* Manual Send Form */}
              <form onSubmit={handleSendReply} className="p-3.5 border-t border-slate-100 bg-white space-y-2">
                <div className="flex gap-2">
                  <textarea
                    rows={2}
                    value={replyText}
                    onChange={(e) => setReplyText(e.target.value)}
                    placeholder="Type your approved WhatsApp reply..."
                    className="flex-1 rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-emerald-500"
                  />
                  <button
                    type="submit"
                    disabled={sendingReply || !replyText.trim()}
                    className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-bold text-white hover:bg-emerald-700 disabled:opacity-50 transition"
                  >
                    {sendingReply ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                    Send
                  </button>
                </div>

                <div className="flex items-center gap-1 text-[10px] text-slate-400">
                  <ShieldCheck className="h-3 w-3 text-emerald-600" />
                  <span>Opt-out & 60s duplicate protections enforced on dispatch.</span>
                </div>
              </form>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-slate-400 p-8 text-center">
              <MessageSquare className="h-10 w-10 text-slate-300 mb-2" />
              <p className="text-sm font-semibold text-slate-600">Select a conversation</p>
              <p className="text-xs text-slate-400 mt-1">Choose a WhatsApp thread on the left to review messages.</p>
            </div>
          )}
        </div>
      </div>

      {/* Connect Modal */}
      {showConnectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-xs animate-in fade-in">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl border border-slate-100 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 text-sm">Connect Meta WhatsApp Business Cloud API</h3>
              <button
                onClick={() => setShowConnectModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleConnect} className="space-y-3.5">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Phone Number ID *</label>
                <input
                  type="text"
                  required
                  value={phoneId}
                  onChange={(e) => setPhoneId(e.target.value)}
                  placeholder="e.g. 100928374650123"
                  className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Phone Number (E.164) *</label>
                <input
                  type="text"
                  required
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  placeholder="+14155552671"
                  className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Display Name</label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="Client Magnet Support"
                  className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">System User Access Token *</label>
                <input
                  type="password"
                  required
                  value={accessToken}
                  onChange={(e) => setAccessToken(e.target.value)}
                  placeholder="EAAB..."
                  className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowConnectModal(false)}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionBusy}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-bold text-white hover:bg-emerald-700 shadow-sm"
                >
                  {actionBusy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Phone className="h-3.5 w-3.5" />}
                  Connect Account
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
