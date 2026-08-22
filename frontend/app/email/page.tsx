"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import {
  associateLeadToConversation,
  disconnectEmailAccount,
  generateAIDraft,
  getEmailAccounts,
  getEmailConversation,
  getEmailConversations,
  getLeads,
  getServices,
  handleProgrammaticEmailCallback,
  initiateEmailConnect,
  sendApprovedEmail,
  syncEmailInbox,
} from "@/lib/api";
import {
  EmailAccountConnection,
  EmailConversation,
  EmailDraftGenerateResponse,
  Lead,
  Service,
} from "@/types";
import {
  Mail,
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
  ChevronRight,
  ShieldCheck,
  User,
  Clock,
  Inbox,
  ArrowRight,
  Check,
  Building,
  Target,
} from "lucide-react";

export default function EmailPage() {
  const { token, user } = useAuth();

  // State
  const [emailAccounts, setEmailAccounts] = useState<EmailAccountConnection[]>([]);
  const [conversations, setConversations] = useState<EmailConversation[]>([]);
  const [selectedConv, setSelectedConv] = useState<EmailConversation | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [services, setServices] = useState<Service[]>([]);

  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [actionBusy, setActionBusy] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Composer Modal State
  const [showComposer, setShowComposer] = useState(false);
  const [composerRecipient, setComposerRecipient] = useState("");
  const [composerSubject, setComposerSubject] = useState("");
  const [composerBody, setComposerBody] = useState("");
  const [composerLeadId, setComposerLeadId] = useState<string>("");
  const [composerServiceId, setComposerServiceId] = useState<string>("");
  const [composerTone, setComposerTone] = useState("Professional, helpful, and concise");
  const [composerNotes, setComposerNotes] = useState("");
  const [generatingDraft, setGeneratingDraft] = useState(false);
  const [sendingEmail, setSendingEmail] = useState(false);

  // Quick reply state
  const [replyBody, setReplyBody] = useState("");
  const [sendingReply, setSendingReply] = useState(false);

  // Load Data
  const loadInitialData = async () => {
    if (!token) return;
    try {
      setLoading(true);
      setErrorMsg(null);

      const [accountsData, convsData, leadsData, servicesData] = await Promise.all([
        getEmailAccounts(token).catch(() => []),
        getEmailConversations(token).catch(() => []),
        getLeads(token).catch(() => []),
        getServices(token, true).catch(() => []),
      ]);

      setEmailAccounts(accountsData);
      setConversations(convsData);
      setLeads(leadsData);
      setServices(servicesData);

      if (convsData.length > 0 && !selectedConv) {
        setSelectedConv(convsData[0]);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load email data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, [token]);

  // Handle Gmail Connect
  const handleConnectGmail = async () => {
    if (!token) return;
    try {
      setActionBusy(true);
      setErrorMsg(null);
      setSuccessMsg(null);

      const initRes = await initiateEmailConnect(token, "gmail");
      if (initRes.authorization_url.includes("mock_gmail_auth_code")) {
        const urlObj = new URL(initRes.authorization_url, "http://localhost");
        const code = urlObj.searchParams.get("code") || "mock_code";
        const state = urlObj.searchParams.get("state") || initRes.state;

        const connected = await handleProgrammaticEmailCallback(token, code, state);
        setSuccessMsg(`Successfully connected Gmail account (${connected.email_address})!`);
        await loadInitialData();
      } else {
        window.location.href = initRes.authorization_url;
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to connect Gmail.");
    } finally {
      setActionBusy(false);
    }
  };

  // Handle Disconnect
  const handleDisconnect = async (accountId: string) => {
    if (!token) return;
    if (!confirm("Are you sure you want to disconnect your Gmail account?")) return;
    try {
      setActionBusy(true);
      await disconnectEmailAccount(token, accountId);
      setSuccessMsg("Successfully disconnected Gmail account.");
      await loadInitialData();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to disconnect Gmail.");
    } finally {
      setActionBusy(false);
    }
  };

  // Handle Sync Inbox
  const handleSyncInbox = async () => {
    if (!token) return;
    try {
      setSyncing(true);
      setErrorMsg(null);
      const res = await syncEmailInbox(token);
      setSuccessMsg(res.message);
      const convsData = await getEmailConversations(token);
      setConversations(convsData);
      if (selectedConv) {
        const updated = await getEmailConversation(token, selectedConv.id);
        setSelectedConv(updated);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to sync inbox.");
    } finally {
      setSyncing(false);
    }
  };

  // Select Conversation
  const handleSelectConversation = async (conv: EmailConversation) => {
    if (!token) return;
    try {
      const fullConv = await getEmailConversation(token, conv.id);
      setSelectedConv(fullConv);
      // Update unread state in local list
      setConversations((prev) =>
        prev.map((c) => (c.id === conv.id ? { ...c, unread_count: 0 } : c))
      );
    } catch (err: any) {
      setSelectedConv(conv);
    }
  };

  // Associate Lead
  const handleAssociateLead = async (leadId: string) => {
    if (!token || !selectedConv) return;
    try {
      const updated = await associateLeadToConversation(
        token,
        selectedConv.id,
        leadId ? leadId : null
      );
      setSelectedConv(updated);
      setConversations((prev) =>
        prev.map((c) => (c.id === selectedConv.id ? updated : c))
      );
      setSuccessMsg("Updated conversation lead association.");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to associate lead.");
    }
  };

  // Generate AI Draft
  const handleGenerateAIDraft = async () => {
    if (!token || !composerLeadId) {
      alert("Please select a target Lead to generate a personalized draft.");
      return;
    }
    try {
      setGeneratingDraft(true);
      setErrorMsg(null);
      const draftRes: EmailDraftGenerateResponse = await generateAIDraft(token, {
        lead_id: composerLeadId,
        service_id: composerServiceId || undefined,
        tone: composerTone,
        context_notes: composerNotes || undefined,
      });

      setComposerRecipient(draftRes.recipient);
      setComposerSubject(draftRes.subject);
      setComposerBody(draftRes.body);
      setSuccessMsg("AI draft generated successfully with Gemini!");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to generate AI draft.");
    } finally {
      setGeneratingDraft(false);
    }
  };

  // Send Approved Email
  const handleSendApprovedEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    if (!composerRecipient || !composerSubject.trim() || !composerBody.trim()) {
      alert("Recipient, Subject, and Body are required.");
      return;
    }

    try {
      setSendingEmail(true);
      setErrorMsg(null);
      const res = await sendApprovedEmail(token, {
        recipient: composerRecipient.trim(),
        subject: composerSubject.trim(),
        body: composerBody.trim(),
        lead_id: composerLeadId || undefined,
      });

      setSuccessMsg(`Email dispatched successfully to ${res.recipient}!`);
      setShowComposer(false);
      setComposerRecipient("");
      setComposerSubject("");
      setComposerBody("");
      setComposerLeadId("");
      setComposerNotes("");

      // Reload conversations
      const updatedConvs = await getEmailConversations(token);
      setConversations(updatedConvs);
      if (res.conversation_id) {
        const fullConv = await getEmailConversation(token, res.conversation_id);
        setSelectedConv(fullConv);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to send email.");
    } finally {
      setSendingEmail(false);
    }
  };

  // Send Quick Reply in Active Thread
  const handleSendReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !selectedConv || !replyBody.trim()) return;

    const recipient = selectedConv.lead?.email || selectedConv.external_conversation_id || "";
    if (!recipient) {
      alert("No valid recipient email on this thread.");
      return;
    }

    try {
      setSendingReply(true);
      setErrorMsg(null);
      const res = await sendApprovedEmail(token, {
        recipient: recipient,
        subject: selectedConv.subject?.startsWith("Re:") ? selectedConv.subject : `Re: ${selectedConv.subject || "Inquiry"}`,
        body: replyBody.trim(),
        conversation_id: selectedConv.id,
        lead_id: selectedConv.lead_id || undefined,
      });

      setReplyBody("");
      setSuccessMsg("Reply dispatched successfully!");
      const updated = await getEmailConversation(token, selectedConv.id);
      setSelectedConv(updated);
      setConversations((prev) =>
        prev.map((c) => (c.id === selectedConv.id ? updated : c))
      );
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to send reply.");
    } finally {
      setSendingReply(false);
    }
  };

  const connectedAccount = emailAccounts.find((a) => a.connection_status === "CONNECTED");

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
      {/* Header & Gmail Connection Bar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Mail className="h-7 w-7 text-indigo-600" />
            Email Inbox & Outreach Hub
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Personalized, human-approved client communication via official Gmail integration.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {connectedAccount ? (
            <div className="flex items-center gap-2 rounded-xl bg-emerald-50 px-3.5 py-2 border border-emerald-200">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs font-bold text-emerald-800">{connectedAccount.email_address}</span>
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
              onClick={handleConnectGmail}
              disabled={actionBusy}
              className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-xs font-bold text-white hover:bg-slate-800 shadow-sm"
            >
              {actionBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <LinkIcon className="h-4 w-4" />}
              Connect Gmail Account
            </button>
          )}

          <button
            onClick={handleSyncInbox}
            disabled={syncing || !connectedAccount}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${syncing ? "animate-spin" : ""}`} />
            Sync Inbox
          </button>

          <button
            onClick={() => setShowComposer(true)}
            className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-700 shadow-sm"
          >
            <Plus className="h-4 w-4" />
            Compose Approved Email
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

      {/* 2-Pane Email Interface */}
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
                placeholder="Search conversations, subjects, emails..."
                className="w-full rounded-xl border border-slate-200 bg-white py-2 pl-9 pr-3 text-xs outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
            {loading ? (
              <div className="p-8 text-center text-xs text-slate-400">
                <Loader2 className="h-5 w-5 animate-spin mx-auto mb-2 text-indigo-500" />
                Loading conversations...
              </div>
            ) : filteredConversations.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">
                <Inbox className="h-8 w-8 mx-auto mb-2 text-slate-300" />
                No email conversations yet. Sync inbox or compose an outreach email to start.
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
                        ? "bg-indigo-50/80 border-l-4 border-l-indigo-600"
                        : "hover:bg-slate-50/80"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 font-bold text-xs text-slate-900 truncate max-w-[200px]">
                        {conv.unread_count > 0 && (
                          <span className="h-2 w-2 rounded-full bg-indigo-600 flex-shrink-0" />
                        )}
                        <span>{conv.lead?.name || conv.external_conversation_id || "Prospect"}</span>
                      </div>
                      <span className="text-[10px] text-slate-400 font-medium whitespace-nowrap">
                        {conv.last_message_at
                          ? new Date(conv.last_message_at).toLocaleDateString([], { month: "short", day: "numeric" })
                          : "Recently"}
                      </span>
                    </div>

                    <p className="text-xs font-semibold text-slate-800 truncate">
                      {conv.subject || "No Subject"}
                    </p>

                    <p className="text-[11px] text-slate-500 line-clamp-1">
                      {lastMsg?.message_content || "No message content recorded"}
                    </p>

                    <div className="flex items-center gap-2 mt-1">
                      {conv.lead ? (
                        <span className="rounded bg-indigo-100/70 px-1.5 py-0.5 text-[10px] font-medium text-indigo-700">
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
              {/* Thread Header */}
              <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="font-bold text-slate-900 text-sm">{selectedConv.subject || "Email Conversation"}</h3>
                  <span className="text-xs text-slate-500">
                    With: <strong className="text-slate-700">{selectedConv.lead?.email || selectedConv.external_conversation_id}</strong>
                  </span>
                </div>

                {/* Lead Association Selector */}
                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-slate-400 font-medium">Lead:</span>
                  <select
                    value={selectedConv.lead_id || ""}
                    onChange={(e) => handleAssociateLead(e.target.value)}
                    className="rounded-lg border border-slate-200 bg-white py-1 px-2 text-xs font-semibold text-slate-700 outline-none"
                  >
                    <option value="">-- Associate Lead --</option>
                    {leads.map((l) => (
                      <option key={l.id} value={l.id}>
                        {l.name} ({l.company || l.email || "No company"})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Message List */}
              <div className="flex-1 p-5 overflow-y-auto space-y-4 bg-slate-50/30">
                {selectedConv.messages.length === 0 ? (
                  <div className="text-center py-12 text-xs text-slate-400">
                    No messages in this conversation thread.
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
                          {isOutbound ? "✓ Sent & Approved" : "Received via Gmail"}
                        </span>
                      </div>
                    );
                  })
                )}
              </div>

              {/* Quick Reply Composer */}
              <form onSubmit={handleSendReply} className="p-3.5 border-t border-slate-100 bg-white">
                <div className="flex gap-2">
                  <textarea
                    rows={2}
                    value={replyBody}
                    onChange={(e) => setReplyBody(e.target.value)}
                    placeholder="Type your approved reply..."
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
              </form>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-slate-400 p-8 text-center">
              <Mail className="h-10 w-10 text-slate-300 mb-2" />
              <p className="text-sm font-semibold text-slate-600">Select a conversation</p>
              <p className="text-xs text-slate-400 mt-1">Choose a conversation from the left to view message history or reply.</p>
            </div>
          )}
        </div>
      </div>

      {/* AI Outreach Composer Modal */}
      {showComposer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-xs animate-in fade-in">
          <div className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-2xl border border-slate-100 max-h-[90vh] overflow-y-auto space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 border border-indigo-100">
                  <Sparkles className="h-4 w-4" />
                </span>
                <div>
                  <h3 className="font-bold text-slate-900 text-sm">Approved Email Outreach Composer</h3>
                  <p className="text-[11px] text-slate-400">AI-assisted drafting with explicit human approval before dispatch</p>
                </div>
              </div>
              <button
                onClick={() => setShowComposer(false)}
                className="text-slate-400 hover:text-slate-600 font-bold text-lg"
              >
                ✕
              </button>
            </div>

            {/* AI Auto-Drafter Section */}
            <div className="rounded-xl border border-indigo-100 bg-indigo-50/40 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-indigo-900 flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
                  Generate Draft with Gemini AI
                </span>
                <span className="text-[10px] text-indigo-600 font-medium">Context-Aware Drafter</span>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="text-[11px] font-bold text-slate-600 block mb-1">Target Lead *</label>
                  <select
                    value={composerLeadId}
                    onChange={(e) => {
                      setComposerLeadId(e.target.value);
                      const sel = leads.find((l) => l.id === e.target.value);
                      if (sel && sel.email) setComposerRecipient(sel.email);
                    }}
                    className="w-full rounded-lg border border-slate-200 bg-white p-2 text-xs font-semibold outline-none"
                  >
                    <option value="">-- Select Prospect Lead --</option>
                    {leads.map((l) => (
                      <option key={l.id} value={l.id}>
                        {l.name} ({l.company || l.email || "No email"})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-[11px] font-bold text-slate-600 block mb-1">Service Pitch</label>
                  <select
                    value={composerServiceId}
                    onChange={(e) => setComposerServiceId(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 bg-white p-2 text-xs font-semibold outline-none"
                  >
                    <option value="">-- Default Matched Service --</option>
                    {services.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="text-[11px] font-bold text-slate-600 block mb-1">Tone</label>
                  <select
                    value={composerTone}
                    onChange={(e) => setComposerTone(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 bg-white p-2 text-xs font-semibold outline-none"
                  >
                    <option value="Professional, helpful, and concise">Professional & Consultative</option>
                    <option value="Direct, value-driven, and bold">Direct & ROI-Focused</option>
                    <option value="Friendly, warm, and conversational">Warm & Collaborative</option>
                  </select>
                </div>

                <div>
                  <label className="text-[11px] font-bold text-slate-600 block mb-1">Custom Context Notes</label>
                  <input
                    type="text"
                    value={composerNotes}
                    onChange={(e) => setComposerNotes(e.target.value)}
                    placeholder="e.g. mention our modern Next.js portfolio"
                    className="w-full rounded-lg border border-slate-200 bg-white p-2 text-xs outline-none"
                  />
                </div>
              </div>

              <button
                type="button"
                onClick={handleGenerateAIDraft}
                disabled={generatingDraft || !composerLeadId}
                className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 py-2 text-xs font-bold text-white hover:bg-indigo-700 disabled:opacity-50 transition"
              >
                {generatingDraft ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin" /> Generating Draft with Gemini...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-3.5 w-3.5" /> Generate Personalized Draft
                  </>
                )}
              </button>
            </div>

            {/* Email Form */}
            <form onSubmit={handleSendApprovedEmail} className="space-y-4">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Recipient Email *</label>
                <input
                  type="email"
                  required
                  value={composerRecipient}
                  onChange={(e) => setComposerRecipient(e.target.value)}
                  placeholder="prospect@company.com"
                  className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Subject Line *</label>
                <input
                  type="text"
                  required
                  value={composerSubject}
                  onChange={(e) => setComposerSubject(e.target.value)}
                  placeholder="e.g. Tailored Website & Automation solutions for Acme"
                  className="w-full rounded-xl border border-slate-200 p-2.5 text-xs font-semibold outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Email Body *</label>
                <textarea
                  rows={8}
                  required
                  value={composerBody}
                  onChange={(e) => setComposerBody(e.target.value)}
                  placeholder="Review, edit, and tailor your email body before sending..."
                  className="w-full rounded-xl border border-slate-200 p-3 text-xs leading-relaxed outline-none focus:border-indigo-500 font-sans"
                />
              </div>

              {/* Safety & Compliance Notice */}
              <div className="rounded-lg bg-slate-50 p-3 border border-slate-100 flex items-center gap-2 text-[11px] text-slate-500">
                <ShieldCheck className="h-4 w-4 text-emerald-600 flex-shrink-0" />
                <span>
                  Anti-spam check active: Opt-out registry and 60-second duplicate prevention are checked automatically.
                </span>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowComposer(false)}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  disabled={sendingEmail || !composerRecipient || !composerSubject || !composerBody}
                  className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2 text-xs font-bold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50 transition"
                >
                  {sendingEmail ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" /> Dispatching Email...
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4" /> Approve & Send Email
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
