"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import {
  getConversationSummary,
  getSuggestedReply,
  getUnifiedConversation,
  getUnifiedConversations,
  sendApprovedEmail,
  sendApprovedWhatsAppMessage,
} from "@/lib/api";
import {
  ConversationSummary,
  SuggestedReply,
  UnifiedConversation,
} from "@/types";
import {
  MessageSquare,
  Sparkles,
  FileText,
  Send,
  Loader2,
  Check,
  Search,
  CheckCircle2,
  AlertCircle,
  Inbox,
  Clock,
  ShieldCheck,
  Bot,
  Mail,
  Phone,
  Share2,
  RefreshCw,
  Tag,
  TrendingUp,
} from "lucide-react";

export default function MessagesPage() {
  const { token } = useAuth();

  // State
  const [conversations, setConversations] = useState<UnifiedConversation[]>([]);
  const [selectedConv, setSelectedConv] = useState<UnifiedConversation | null>(null);
  const [platformFilter, setPlatformFilter] = useState<string>("all");
  const [unreadOnly, setUnreadOnly] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState("");

  const [loading, setLoading] = useState(true);
  const [actionBusy, setActionBusy] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // AI States
  const [summarizing, setSummarizing] = useState(false);
  const [aiSummary, setAiSummary] = useState<ConversationSummary | null>(null);
  const [suggesting, setSuggesting] = useState(false);
  const [aiReply, setAiReply] = useState<SuggestedReply | null>(null);

  // Composer
  const [replyBody, setReplyBody] = useState("");
  const [sendingReply, setSendingReply] = useState(false);

  // Load Data
  const loadConversations = async () => {
    if (!token) return;
    try {
      setLoading(true);
      setErrorMsg(null);

      const convsData = await getUnifiedConversations(token, {
        platform: platformFilter !== "all" ? platformFilter : undefined,
        unread_only: unreadOnly || undefined,
        q: searchQuery.trim() || undefined,
      });

      setConversations(convsData);
      if (convsData.length > 0 && !selectedConv) {
        setSelectedConv(convsData[0]);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load unified conversations.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConversations();
  }, [token, platformFilter, unreadOnly]);

  // Select Thread
  const handleSelectConversation = async (conv: UnifiedConversation) => {
    if (!token) return;
    try {
      setAiSummary(null);
      setAiReply(null);
      const fullConv = await getUnifiedConversation(token, conv.id);
      setSelectedConv(fullConv);
      // Update unread count locally
      setConversations((prev) =>
        prev.map((c) => (c.id === conv.id ? { ...c, unread_count: 0 } : c))
      );
    } catch (err: any) {
      setSelectedConv(conv);
    }
  };

  // AI Summarize
  const handleSummarize = async () => {
    if (!token || !selectedConv) return;
    try {
      setSummarizing(true);
      setErrorMsg(null);
      const summaryRes = await getConversationSummary(token, selectedConv.id);
      setAiSummary(summaryRes);
      setSuccessMsg("AI conversation summary generated!");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to summarize conversation.");
    } finally {
      setSummarizing(false);
    }
  };

  // AI Suggest Reply
  const handleSuggestReply = async () => {
    if (!token || !selectedConv) return;
    try {
      setSuggesting(true);
      setErrorMsg(null);
      const replyRes = await getSuggestedReply(token, selectedConv.id);
      setAiReply(replyRes);
      setReplyBody(replyRes.suggested_reply);
      setSuccessMsg("AI reply drafted with Gemini! Review and edit before sending.");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to suggest reply.");
    } finally {
      setSuggesting(false);
    }
  };

  // Send Approved Response
  const handleSendResponse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !selectedConv || !replyBody.trim()) return;

    try {
      setSendingReply(true);
      setErrorMsg(null);

      if (selectedConv.platform === "whatsapp") {
        const phone = selectedConv.external_conversation_id || selectedConv.lead?.phone;
        if (!phone) {
          throw new Error("No recipient phone number on this conversation.");
        }
        await sendApprovedWhatsAppMessage(token, {
          recipient_phone: phone,
          message_text: replyBody.trim(),
          conversation_id: selectedConv.id,
          lead_id: selectedConv.lead_id || undefined,
        });
      } else {
        // Default to email channel
        const recipientEmail = selectedConv.lead?.email || selectedConv.external_conversation_id;
        if (!recipientEmail) {
          throw new Error("No recipient email on this conversation.");
        }
        await sendApprovedEmail(token, {
          recipient: recipientEmail,
          subject: selectedConv.subject?.startsWith("Re:") ? selectedConv.subject : `Re: ${selectedConv.subject || "Inquiry"}`,
          body: replyBody.trim(),
          conversation_id: selectedConv.id,
          lead_id: selectedConv.lead_id || undefined,
        });
      }

      setReplyBody("");
      setAiReply(null);
      setSuccessMsg("Response dispatched successfully!");
      const updated = await getUnifiedConversation(token, selectedConv.id);
      setSelectedConv(updated);
      setConversations((prev) =>
        prev.map((c) => (c.id === selectedConv.id ? updated : c))
      );
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to send message.");
    } finally {
      setSendingReply(false);
    }
  };

  const getPlatformIcon = (plat: string) => {
    switch (plat.toLowerCase()) {
      case "email":
        return <Mail className="h-3.5 w-3.5 text-indigo-500" />;
      case "whatsapp":
        return <Phone className="h-3.5 w-3.5 text-emerald-500" />;
      case "facebook":
      case "instagram":
      case "x":
      case "linkedin":
        return <Share2 className="h-3.5 w-3.5 text-sky-500" />;
      default:
        return <MessageSquare className="h-3.5 w-3.5 text-slate-400" />;
    }
  };

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Inbox className="h-7 w-7 text-indigo-600" />
            Unified Communication Inbox
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Omnichannel conversation management across Email, WhatsApp, and Social with Gemini AI copilot.
          </p>
        </div>

        <button
          onClick={loadConversations}
          className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-sm self-start sm:self-auto"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh Inbox
        </button>
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

      {/* Platform Filter Bar */}
      <div className="flex items-center justify-between gap-2 overflow-x-auto pb-1">
        <div className="flex items-center gap-1.5 flex-wrap">
          {["all", "email", "whatsapp", "facebook", "instagram", "x", "linkedin"].map((p) => (
            <button
              key={p}
              onClick={() => setPlatformFilter(p)}
              className={`rounded-xl px-3.5 py-1.5 text-xs font-bold capitalize transition ${
                platformFilter === p
                  ? "bg-indigo-600 text-white shadow-xs"
                  : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
              }`}
            >
              {p === "all" ? "All Channels" : p}
            </button>
          ))}
        </div>

        <button
          onClick={() => setUnreadOnly(!unreadOnly)}
          className={`rounded-xl px-3 py-1.5 text-xs font-bold border transition ${
            unreadOnly
              ? "bg-indigo-50 text-indigo-700 border-indigo-200"
              : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
          }`}
        >
          Unread Only
        </button>
      </div>

      {/* 2-Pane Unified Inbox */}
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
                onKeyDown={(e) => e.key === "Enter" && loadConversations()}
                placeholder="Search subject, name, email or phone..."
                className="w-full rounded-xl border border-slate-200 bg-white py-2 pl-9 pr-3 text-xs outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
            {loading ? (
              <div className="p-8 text-center text-xs text-slate-400">
                <Loader2 className="h-5 w-5 animate-spin mx-auto mb-2 text-indigo-500" />
                Loading unified inbox...
              </div>
            ) : conversations.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">
                <Inbox className="h-8 w-8 mx-auto mb-2 text-slate-300" />
                No conversations match the current channel filter.
              </div>
            ) : (
              conversations.map((conv) => {
                const isSelected = selectedConv?.id === conv.id;
                const lastMsg = conv.messages && conv.messages.length > 0 ? conv.messages[conv.messages.length - 1] : null;

                return (
                  <button
                    key={conv.id}
                    onClick={() => handleSelectConversation(conv)}
                    className={`w-full text-left p-4 transition-all flex flex-col gap-1.5 ${
                      isSelected
                        ? "bg-indigo-50/80 border-l-4 border-l-indigo-600"
                        : "hover:bg-slate-50/80"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 font-bold text-xs text-slate-900 truncate">
                        {conv.unread_count > 0 && (
                          <span className="h-2 w-2 rounded-full bg-indigo-600 flex-shrink-0" />
                        )}
                        <span className="flex items-center gap-1">
                          {getPlatformIcon(conv.platform)}
                          {conv.lead?.name || conv.external_conversation_id || "Prospect"}
                        </span>
                      </div>
                      <span className="text-[10px] text-slate-400 font-medium">
                        {conv.last_message_at
                          ? new Date(conv.last_message_at).toLocaleDateString([], { month: "short", day: "numeric" })
                          : "Recently"}
                      </span>
                    </div>

                    <p className="text-xs font-semibold text-slate-800 truncate">
                      {conv.subject || "Inquiry"}
                    </p>

                    <p className="text-[11px] text-slate-500 line-clamp-1">
                      {lastMsg?.message_content || "No message body"}
                    </p>

                    <div className="flex items-center gap-2 mt-1">
                      <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[9px] font-bold uppercase text-slate-600">
                        {conv.platform}
                      </span>
                      {conv.lead && (
                        <span className="rounded bg-indigo-100/70 px-1.5 py-0.5 text-[9px] font-medium text-indigo-700">
                          🎯 {conv.lead.status}
                        </span>
                      )}
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Right Pane: Thread View & AI Intelligence */}
        <div className="lg:col-span-7 flex flex-col bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          {selectedConv ? (
            <>
              {/* Thread Header */}
              <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                    {getPlatformIcon(selectedConv.platform)}
                    {selectedConv.subject || "Conversation Thread"}
                  </h3>
                  <span className="text-xs text-slate-500">
                    Contact: <strong className="text-slate-700">{selectedConv.lead?.name || selectedConv.external_conversation_id}</strong>
                    {selectedConv.lead?.company && ` (${selectedConv.lead.company})`}
                  </span>
                </div>

                {/* Gemini AI Intelligence Actions */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleSummarize}
                    disabled={summarizing}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-slate-700 hover:bg-slate-50 shadow-xs disabled:opacity-50"
                  >
                    {summarizing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <FileText className="h-3.5 w-3.5 text-indigo-600" />}
                    AI Summary
                  </button>

                  <button
                    onClick={handleSuggestReply}
                    disabled={suggesting}
                    className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-indigo-700 shadow-xs disabled:opacity-50"
                  >
                    {suggesting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
                    Suggest Reply
                  </button>
                </div>
              </div>

              {/* AI Summary Banner */}
              {aiSummary && (
                <div className="border-b border-indigo-100 bg-indigo-50/70 p-4 space-y-2 text-xs animate-in fade-in">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-indigo-950 flex items-center gap-1.5">
                      <Sparkles className="h-3.5 w-3.5 text-indigo-600" /> Gemini Conversation Summary
                    </span>
                    {aiSummary.lead_status_suggestion && (
                      <span className="rounded bg-indigo-200/70 px-2 py-0.5 text-[10px] font-bold text-indigo-900">
                        Suggested Status: {aiSummary.lead_status_suggestion}
                      </span>
                    )}
                  </div>
                  <p className="text-indigo-900 leading-relaxed">{aiSummary.summary}</p>
                  <div className="text-[11px] text-indigo-800 pt-1">
                    <strong>Recommended Next Action:</strong> {aiSummary.next_action}
                  </div>
                </div>
              )}

              {/* Messages Thread */}
              <div className="flex-1 p-5 overflow-y-auto space-y-4 bg-slate-50/30">
                {selectedConv.messages.length === 0 ? (
                  <div className="text-center py-12 text-xs text-slate-400">
                    No messages recorded in this conversation.
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
                          className={`max-w-[85%] rounded-2xl p-4 shadow-xs text-xs leading-relaxed space-y-1.5 ${
                            isOutbound
                              ? "bg-indigo-600 text-white rounded-br-none"
                              : "bg-white border border-slate-200 text-slate-900 rounded-bl-none"
                          }`}
                        >
                          <div
                            className={`flex items-center justify-between gap-4 text-[10px] ${
                              isOutbound ? "text-indigo-200" : "text-slate-400"
                            }`}
                          >
                            <span>{isOutbound ? `To: ${msg.recipient}` : `From: ${msg.sender}`}</span>
                            <span>{new Date(msg.sent_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                          </div>
                          <div className="whitespace-pre-wrap">{msg.message_content}</div>
                        </div>

                        <span className="text-[10px] text-slate-400 mt-1 px-1">
                          {isOutbound ? `✓ Sent via ${msg.platform}` : `Received on ${msg.platform}`}
                        </span>
                      </div>
                    );
                  })
                )}
              </div>

              {/* Channel-Aware Response Composer */}
              <form onSubmit={handleSendResponse} className="p-3.5 border-t border-slate-100 bg-white space-y-2">
                <div className="flex gap-2">
                  <textarea
                    rows={2}
                    value={replyBody}
                    onChange={(e) => setReplyBody(e.target.value)}
                    placeholder={`Reply via approved ${selectedConv.platform.toUpperCase()} connection...`}
                    className="flex-1 rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-indigo-500"
                  />
                  <button
                    type="submit"
                    disabled={sendingReply || !replyBody.trim()}
                    className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-700 disabled:opacity-50 transition"
                  >
                    {sendingReply ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                    Send
                  </button>
                </div>

                <div className="flex items-center justify-between text-[10px] text-slate-400">
                  <span className="flex items-center gap-1">
                    <ShieldCheck className="h-3 w-3 text-emerald-600" />
                    Opt-out & anti-duplicate checks enforced automatically.
                  </span>
                  <span className="font-semibold uppercase text-slate-500">
                    Channel: {selectedConv.platform}
                  </span>
                </div>
              </form>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-slate-400 p-8 text-center">
              <Inbox className="h-10 w-10 text-slate-300 mb-2" />
              <p className="text-sm font-semibold text-slate-600">Select a conversation</p>
              <p className="text-xs text-slate-400 mt-1">Choose a cross-channel thread on the left to read and respond.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
