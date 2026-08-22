"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import {
  analyzeLead,
  deleteLead,
  generateEmailDraft,
  getLeadById,
  getServices,
  updateLead,
} from "@/lib/api";
import {
  EmailDraftResponse,
  Lead,
  LeadAnalysisResponse,
  LeadSource,
  LeadStatus,
  LeadUpdate,
  Service,
} from "@/types";
import {
  ArrowLeft,
  Building,
  Mail,
  Phone,
  Globe,
  MapPin,
  ExternalLink,
  Layers,
  Sparkles,
  Clock,
  Trash2,
  Save,
  CheckCircle2,
  AlertCircle,
  Loader2,
  FileText,
  Sliders,
  DollarSign,
  User,
  Send,
  Copy,
  Check,
  Zap,
  Target,
  RefreshCw,
} from "lucide-react";

const STATUS_CONFIG: Record<
  LeadStatus,
  { label: string; bg: string; text: string; border: string }
> = {
  NEW: { label: "New", bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200" },
  QUALIFIED: { label: "Qualified", bg: "bg-indigo-50", text: "text-indigo-700", border: "border-indigo-200" },
  CONTACTED: { label: "Contacted", bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200" },
  REPLIED: { label: "Replied", bg: "bg-purple-50", text: "text-purple-700", border: "border-purple-200" },
  INTERESTED: { label: "Interested", bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-200" },
  DISCOVERY: { label: "Discovery", bg: "bg-cyan-50", text: "text-cyan-700", border: "border-cyan-200" },
  PROPOSAL: { label: "Proposal", bg: "bg-violet-50", text: "text-violet-700", border: "border-violet-200" },
  NEGOTIATION: { label: "Negotiation", bg: "bg-orange-50", text: "text-orange-700", border: "border-orange-200" },
  WON: { label: "Won", bg: "bg-green-100", text: "text-green-800", border: "border-green-300" },
  LOST: { label: "Lost", bg: "bg-rose-50", text: "text-rose-700", border: "border-rose-200" },
  NOT_A_FIT: { label: "Not a Fit", bg: "bg-slate-100", text: "text-slate-600", border: "border-slate-300" },
};

const ALL_STATUSES: LeadStatus[] = [
  "NEW",
  "QUALIFIED",
  "CONTACTED",
  "REPLIED",
  "INTERESTED",
  "DISCOVERY",
  "PROPOSAL",
  "NEGOTIATION",
  "WON",
  "LOST",
  "NOT_A_FIT",
];

export default function LeadDetailPage() {
  const params = useParams();
  const router = useRouter();
  const leadId = params?.id as string;
  const { token } = useAuth();

  const [lead, setLead] = useState<Lead | null>(null);
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  // Editable fields
  const [notes, setNotes] = useState("");
  const [intentScore, setIntentScore] = useState<number>(0);
  const [selectedServiceId, setSelectedServiceId] = useState<string>("");
  const [status, setStatus] = useState<LeadStatus>("NEW");

  // AI Intelligence States
  const [analyzingLead, setAnalyzingLead] = useState(false);
  const [aiAnalysis, setAiAnalysis] = useState<LeadAnalysisResponse | null>(null);
  const [aiError, setAiError] = useState<string | null>(null);

  const [showEmailModal, setShowEmailModal] = useState(false);
  const [generatingEmail, setGeneratingEmail] = useState(false);
  const [emailTone, setEmailTone] = useState("Professional");
  const [customInstructions, setCustomInstructions] = useState("");
  const [emailSubject, setEmailSubject] = useState("");
  const [emailBody, setEmailBody] = useState("");
  const [copiedEmail, setCopiedEmail] = useState(false);

  useEffect(() => {
    async function loadLeadAndServices() {
      if (!token || !leadId) return;
      try {
        setLoading(true);
        setError(null);
        const [leadData, servicesData] = await Promise.all([
          getLeadById(token, leadId),
          getServices(token),
        ]);
        setLead(leadData);
        setServices(servicesData);
        setNotes(leadData.notes || "");
        setIntentScore(leadData.intent_score || 0);
        setSelectedServiceId(leadData.matched_service_id || "");
        setStatus(leadData.status as LeadStatus);
      } catch (err: any) {
        setError(err.message || "Failed to load lead details");
      } finally {
        setLoading(false);
      }
    }

    loadLeadAndServices();
  }, [token, leadId]);

  const handleUpdate = async (updates: LeadUpdate) => {
    if (!token || !leadId) return;
    try {
      setSaving(true);
      setError(null);
      setSuccessMsg(null);
      const updated = await updateLead(token, leadId, updates);
      setLead(updated);
      setSuccessMsg("Lead updated successfully.");
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err: any) {
      setError(err.message || "Failed to update lead");
    } finally {
      setSaving(false);
    }
  };

  const handleSaveNotes = async () => {
    await handleUpdate({ notes });
  };

  const handleStatusChange = async (newStatus: LeadStatus) => {
    setStatus(newStatus);
    await handleUpdate({ status: newStatus });
  };

  const handleServiceChange = async (newServiceId: string) => {
    setSelectedServiceId(newServiceId);
    await handleUpdate({ matched_service_id: newServiceId || null });
  };

  const handleScoreChange = async (newScore: number) => {
    setIntentScore(newScore);
    await handleUpdate({ intent_score: newScore });
  };

  const handleDelete = async () => {
    if (!token || !leadId) return;
    try {
      await deleteLead(token, leadId);
      router.push("/leads");
    } catch (err: any) {
      alert("Failed to delete lead: " + err.message);
    }
  };

  // AI Operations
  const handleAnalyzeWithAI = async () => {
    if (!token || !lead) return;
    try {
      setAnalyzingLead(true);
      setAiError(null);
      const res = await analyzeLead(token, {
        lead_id: lead.id,
        lead_name: lead.name,
        lead_company: lead.company || undefined,
        lead_description: lead.description || undefined,
        source: typeof lead.source === "string" ? lead.source : undefined,
        detected_need: lead.detected_need || undefined,
      });
      setAiAnalysis(res);
    } catch (err: any) {
      setAiError(err.message || "Failed to analyze lead with AI");
    } finally {
      setAnalyzingLead(false);
    }
  };

  const handleApplyAIFindings = async () => {
    if (!aiAnalysis || !lead) return;
    const updates: LeadUpdate = {
      detected_need: aiAnalysis.detected_need,
      intent_score: aiAnalysis.intent_score,
    };
    if (aiAnalysis.matched_service_id) {
      updates.matched_service_id = aiAnalysis.matched_service_id;
      setSelectedServiceId(aiAnalysis.matched_service_id);
    }
    setIntentScore(aiAnalysis.intent_score);
    await handleUpdate(updates);
  };

  const handleGenerateEmail = async () => {
    if (!token || !lead) return;
    try {
      setGeneratingEmail(true);
      setAiError(null);
      const res = await generateEmailDraft(token, {
        lead_id: lead.id,
        lead_name: lead.name,
        lead_company: lead.company || undefined,
        lead_need: lead.detected_need || lead.description || undefined,
        matched_service_id: selectedServiceId || undefined,
        desired_tone: emailTone,
        custom_instructions: customInstructions || undefined,
      });
      setEmailSubject(res.subject);
      setEmailBody(res.body);
      setShowEmailModal(true);
    } catch (err: any) {
      alert("AI Email generation failed: " + (err.message || "Unknown error"));
    } finally {
      setGeneratingEmail(false);
    }
  };

  const handleCopyEmail = () => {
    const fullText = `Subject: ${emailSubject}\n\n${emailBody}`;
    navigator.clipboard.writeText(fullText);
    setCopiedEmail(true);
    setTimeout(() => setCopiedEmail(false), 2000);
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center rounded-2xl border border-slate-200 bg-white">
        <div className="text-center text-slate-400">
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-sky-500" />
          <p className="mt-2 text-sm font-medium">Loading lead profile...</p>
        </div>
      </div>
    );
  }

  if (error && !lead) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-8 text-center">
        <AlertCircle className="mx-auto h-10 w-10 text-red-500" />
        <h3 className="mt-3 text-lg font-bold text-red-800">Unable to Load Lead</h3>
        <p className="mt-1 text-sm text-red-600">{error}</p>
        <Link
          href="/leads"
          className="mt-5 inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-sm font-bold text-slate-700 shadow-sm border border-slate-200 hover:bg-slate-50"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Leads
        </Link>
      </div>
    );
  }

  if (!lead) return null;

  const currentStatusInfo =
    STATUS_CONFIG[status] || {
      label: status,
      bg: "bg-slate-100",
      text: "text-slate-700",
      border: "border-slate-200",
    };

  return (
    <div className="space-y-6">
      {/* Back Navigation & Breadcrumb */}
      <div className="flex items-center justify-between">
        <Link
          href="/leads"
          className="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-slate-900 transition"
        >
          <ArrowLeft className="h-4 w-4" /> Back to All Leads
        </Link>

        <div className="flex items-center gap-2">
          {saving && (
            <span className="inline-flex items-center gap-1.5 text-xs text-sky-600 font-medium">
              <Loader2 className="h-3.5 w-3.5 animate-spin" /> Saving changes...
            </span>
          )}
          {successMsg && (
            <span className="inline-flex items-center gap-1.5 text-xs text-emerald-600 font-semibold animate-in fade-in">
              <CheckCircle2 className="h-3.5 w-3.5" /> {successMsg}
            </span>
          )}
        </div>
      </div>

      {/* Hero Header Card */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-tr from-sky-500 to-indigo-600 text-white font-extrabold text-lg shadow-md shadow-sky-500/20">
              {lead.name.slice(0, 2).toUpperCase()}
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">{lead.name}</h1>
                <span className="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-700">
                  {lead.source}
                </span>
              </div>
              {lead.company && (
                <p className="flex items-center gap-1 text-sm text-slate-500 mt-0.5">
                  <Building className="h-3.5 w-3.5" /> {lead.company}
                </p>
              )}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* AI Action Buttons */}
            <button
              onClick={handleAnalyzeWithAI}
              disabled={analyzingLead}
              className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-sky-600 to-indigo-600 px-4 py-2 text-xs font-bold text-white shadow-sm hover:from-sky-500 hover:to-indigo-500 active:scale-95 disabled:opacity-50 transition"
            >
              {analyzingLead ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" /> Analyzing with Gemini...
                </>
              ) : (
                <>
                  <Sparkles className="h-3.5 w-3.5" /> Analyze Lead with AI
                </>
              )}
            </button>

            <button
              onClick={handleGenerateEmail}
              disabled={generatingEmail}
              className="inline-flex items-center gap-1.5 rounded-xl border border-sky-200 bg-sky-50 px-4 py-2 text-xs font-bold text-sky-700 hover:bg-sky-100 active:scale-95 disabled:opacity-50 transition"
            >
              {generatingEmail ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" /> Drafting...
                </>
              ) : (
                <>
                  <Mail className="h-3.5 w-3.5" /> Generate Email Draft
                </>
              )}
            </button>

            {/* Status Selector */}
            <div className="flex items-center gap-2 ml-2">
              <label className="text-xs font-bold text-slate-400 uppercase">Status:</label>
              <select
                value={status}
                onChange={(e) => handleStatusChange(e.target.value as LeadStatus)}
                className={`rounded-xl border px-3 py-1.5 text-xs font-bold outline-none cursor-pointer ${currentStatusInfo.bg} ${currentStatusInfo.text} ${currentStatusInfo.border}`}
              >
                {ALL_STATUSES.map((st) => (
                  <option key={st} value={st}>
                    {STATUS_CONFIG[st]?.label || st}
                  </option>
                ))}
              </select>
            </div>

            {lead.source_url && (
              <a
                href={lead.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-bold text-slate-700 hover:bg-slate-50 transition shadow-sm"
              >
                <span>Open Opportunity</span>
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            )}

            <button
              onClick={() => setShowDeleteModal(true)}
              className="rounded-xl border border-red-200 bg-red-50 p-2 text-red-600 hover:bg-red-100 transition ml-1"
              title="Delete Lead"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* AI Lead Analysis Insight Card (When Run) */}
      {aiAnalysis && (
        <div className="rounded-2xl border border-indigo-200 bg-gradient-to-br from-indigo-50/70 via-sky-50/40 to-white p-6 shadow-sm space-y-4 animate-in fade-in slide-in-from-top-2">
          <div className="flex items-center justify-between border-b border-indigo-100 pb-3">
            <div className="flex items-center gap-2">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-sm">
                <Sparkles className="h-4 w-4" />
              </span>
              <div>
                <h3 className="font-bold text-indigo-950 text-sm">Gemini AI Lead Intelligence Assessment</h3>
                <p className="text-[11px] text-indigo-700/80">Objective analysis based on active services</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 rounded-xl bg-white px-3 py-1 border border-indigo-100 shadow-xs">
                <Target className="h-3.5 w-3.5 text-indigo-600" />
                <span className="text-xs font-bold text-indigo-950">
                  Intent Score: <span className="text-indigo-600">{aiAnalysis.intent_score}/100</span>
                </span>
              </div>
              <button
                onClick={handleApplyAIFindings}
                className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-indigo-500 active:scale-95 shadow-sm transition"
              >
                <Check className="h-3.5 w-3.5" /> Apply Findings to Lead
              </button>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 text-xs">
            <div className="rounded-xl bg-white p-4 border border-indigo-100/80 shadow-xs space-y-1">
              <span className="font-bold text-slate-400 uppercase tracking-wider block text-[10px]">Detected Client Need</span>
              <p className="text-slate-800 font-medium leading-relaxed">{aiAnalysis.detected_need}</p>
            </div>

            <div className="rounded-xl bg-white p-4 border border-indigo-100/80 shadow-xs space-y-1">
              <span className="font-bold text-slate-400 uppercase tracking-wider block text-[10px]">Recommended Match</span>
              <p className="text-indigo-900 font-bold text-sm">
                {aiAnalysis.matched_service || "No direct service match found in catalog"}
              </p>
            </div>

            <div className="rounded-xl bg-white p-4 border border-indigo-100/80 shadow-xs space-y-1 sm:col-span-2">
              <span className="font-bold text-slate-400 uppercase tracking-wider block text-[10px]">Reasoning & Context</span>
              <p className="text-slate-700 leading-relaxed">{aiAnalysis.reasoning_summary}</p>
            </div>

            <div className="rounded-xl bg-indigo-100/50 p-4 border border-indigo-200/80 sm:col-span-2 flex items-start gap-2.5">
              <Zap className="h-4 w-4 text-indigo-700 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-indigo-950 block text-[11px]">Recommended Tactical Next Action</span>
                <p className="text-indigo-900 text-xs mt-0.5">{aiAnalysis.recommended_next_action}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {aiError && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-xs font-semibold text-red-700 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{aiError}</span>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left 2 Columns: Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Contact & Profile Overview */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2">
              <User className="h-4 w-4 text-sky-500" />
              Contact & Profile Details
            </h3>

            <div className="grid gap-4 sm:grid-cols-2 text-sm">
              <div className="flex items-start gap-3">
                <Mail className="h-4 w-4 text-slate-400 mt-0.5 shrink-0" />
                <div>
                  <span className="block text-xs font-semibold text-slate-400">Email</span>
                  {lead.email ? (
                    <a href={`mailto:${lead.email}`} className="font-medium text-sky-600 hover:underline">
                      {lead.email}
                    </a>
                  ) : (
                    <span className="italic text-slate-400">Not provided</span>
                  )}
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Phone className="h-4 w-4 text-slate-400 mt-0.5 shrink-0" />
                <div>
                  <span className="block text-xs font-semibold text-slate-400">Phone</span>
                  {lead.phone ? (
                    <a href={`tel:${lead.phone}`} className="font-medium text-slate-800">
                      {lead.phone}
                    </a>
                  ) : (
                    <span className="italic text-slate-400">Not provided</span>
                  )}
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Globe className="h-4 w-4 text-slate-400 mt-0.5 shrink-0" />
                <div>
                  <span className="block text-xs font-semibold text-slate-400">Website</span>
                  {lead.website ? (
                    <a
                      href={lead.website.startsWith("http") ? lead.website : `https://${lead.website}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-sky-600 hover:underline flex items-center gap-1"
                    >
                      {lead.website} <ExternalLink className="h-3 w-3" />
                    </a>
                  ) : (
                    <span className="italic text-slate-400">Not provided</span>
                  )}
                </div>
              </div>

              <div className="flex items-start gap-3">
                <MapPin className="h-4 w-4 text-slate-400 mt-0.5 shrink-0" />
                <div>
                  <span className="block text-xs font-semibold text-slate-400">Location</span>
                  <span className="font-medium text-slate-800">
                    {lead.location || <span className="italic text-slate-400">Not specified</span>}
                  </span>
                </div>
              </div>

              {lead.profile_url && (
                <div className="sm:col-span-2 flex items-start gap-3">
                  <ExternalLink className="h-4 w-4 text-slate-400 mt-0.5 shrink-0" />
                  <div>
                    <span className="block text-xs font-semibold text-slate-400">
                      Social / Profile URL ({lead.platform || "Direct"})
                    </span>
                    <a
                      href={lead.profile_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-sky-600 hover:underline break-all"
                    >
                      {lead.profile_url}
                    </a>
                  </div>
                </div>
              )}

              {lead.source_url && (
                <div className="sm:col-span-2 flex items-start gap-3">
                  <ExternalLink className="h-4 w-4 text-slate-400 mt-0.5 shrink-0" />
                  <div>
                    <span className="block text-xs font-semibold text-slate-400">Discovered Source URL</span>
                    <a
                      href={lead.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-sky-600 hover:underline break-all"
                    >
                      {lead.source_url}
                    </a>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Need & Opportunity */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-sky-500" />
              Need & Opportunity Assessment
            </h3>

            <div>
              <span className="block text-xs font-semibold text-slate-400 mb-1">Detected Need</span>
              <p className="rounded-xl bg-slate-50 p-3.5 text-sm text-slate-700 leading-relaxed border border-slate-100">
                {lead.detected_need || <span className="italic text-slate-400">No detected need specified. Use "Analyze Lead with AI" above.</span>}
              </p>
            </div>

            {lead.description && (
              <div>
                <span className="block text-xs font-semibold text-slate-400 mb-1">Prospect Description / Context</span>
                <p className="rounded-xl bg-slate-50 p-3.5 text-sm text-slate-700 leading-relaxed border border-slate-100">
                  {lead.description}
                </p>
              </div>
            )}
          </div>

          {/* Matched Service Card */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Layers className="h-4 w-4 text-sky-500" />
              Matched User Service
            </h3>

            <div className="space-y-3">
              <label className="block text-xs font-semibold text-slate-500">
                Assign to one of your configured services:
              </label>
              <select
                value={selectedServiceId}
                onChange={(e) => handleServiceChange(e.target.value)}
                className="w-full rounded-xl border border-slate-200 p-2.5 text-sm outline-none focus:border-sky-500 bg-white"
              >
                <option value="">-- No Matched Service (Unassigned) --</option>
                {services.map((svc) => (
                  <option key={svc.id} value={svc.id}>
                    {svc.name} {svc.pricing ? `(${svc.pricing})` : ""}
                  </option>
                ))}
              </select>

              {lead.matched_service && (
                <div className="mt-4 rounded-xl bg-sky-50/70 border border-sky-100 p-4">
                  <div className="flex items-center justify-between">
                    <h4 className="font-bold text-sky-900 text-sm">{lead.matched_service.name}</h4>
                    {lead.matched_service.pricing && (
                      <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700 bg-white rounded-lg px-2 py-0.5 border border-emerald-200">
                        <DollarSign className="h-3 w-3" />
                        {lead.matched_service.pricing}
                      </span>
                    )}
                  </div>
                  {lead.matched_service.description && (
                    <p className="mt-1.5 text-xs text-sky-800 leading-relaxed">{lead.matched_service.description}</p>
                  )}
                  {lead.matched_service.target_clients && (
                    <p className="mt-2 text-xs text-slate-500">
                      <strong>Target Clients:</strong> {lead.matched_service.target_clients}
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Intent Score & Notes */}
        <div className="space-y-6">
          {/* Intent Score */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                <Sliders className="h-4 w-4 text-sky-500" />
                Intent Score
              </h3>
              <span className="text-lg font-black text-slate-800">{intentScore} / 100</span>
            </div>

            <div className="space-y-3">
              <input
                type="range"
                min="0"
                max="100"
                value={intentScore}
                onChange={(e) => setIntentScore(parseFloat(e.target.value))}
                onMouseUp={() => handleScoreChange(intentScore)}
                onTouchEnd={() => handleScoreChange(intentScore)}
                className="w-full accent-sky-600 cursor-pointer"
              />

              <div className="flex justify-between text-[11px] font-semibold text-slate-400">
                <span>0 (Cold)</span>
                <span>50 (Warm)</span>
                <span>100 (Hot Intent)</span>
              </div>
            </div>
          </div>

          {/* Notes Section */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-3">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <FileText className="h-4 w-4 text-sky-500" />
              Notes & History
            </h3>

            <textarea
              rows={6}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add conversation notes, next steps, meeting outcomes..."
              className="w-full rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 resize-none"
            />

            <div className="flex justify-end">
              <button
                onClick={handleSaveNotes}
                disabled={saving}
                className="inline-flex items-center gap-2 rounded-xl bg-sky-600 px-4 py-2 text-xs font-bold text-white hover:bg-sky-500 active:scale-95 disabled:opacity-50 transition"
              >
                <Save className="h-3.5 w-3.5" />
                Save Notes
              </button>
            </div>
          </div>

          {/* Quick Status Advance */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-3">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <Clock className="h-4 w-4 text-sky-500" />
              Pipeline Actions
            </h3>

            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => handleStatusChange("CONTACTED")}
                className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
              >
                Mark Contacted
              </button>
              <button
                onClick={() => handleStatusChange("INTERESTED")}
                className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-800 hover:bg-emerald-100 transition"
              >
                Mark Interested
              </button>
              <button
                onClick={() => handleStatusChange("PROPOSAL")}
                className="rounded-xl border border-violet-200 bg-violet-50 px-3 py-2 text-xs font-semibold text-violet-800 hover:bg-violet-100 transition"
              >
                Send Proposal
              </button>
              <button
                onClick={() => handleStatusChange("WON")}
                className="rounded-xl border border-green-300 bg-green-100 px-3 py-2 text-xs font-bold text-green-900 hover:bg-green-200 transition"
              >
                Won Client 🎉
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* AI Email Draft Modal */}
      {showEmailModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-sky-100 text-sky-600">
                  <Mail className="h-4 w-4" />
                </span>
                <div>
                  <h3 className="font-bold text-slate-900 text-base">AI Generated Outreach Email Draft</h3>
                  <p className="text-xs text-slate-400">Advisory draft tailored to {lead.name} — Review before sending</p>
                </div>
              </div>

              <button
                onClick={() => setShowEmailModal(false)}
                className="text-slate-400 hover:text-slate-700 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 text-xs">
              <div>
                <label className="font-bold text-slate-500 uppercase tracking-wider block mb-1">Tone Adjustment</label>
                <select
                  value={emailTone}
                  onChange={(e) => setEmailTone(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 p-2 text-xs font-medium outline-none"
                >
                  <option value="Professional">Professional</option>
                  <option value="Warm & Consultative">Warm & Consultative</option>
                  <option value="Direct & Concise">Direct & Concise</option>
                  <option value="Enthusiastic">Enthusiastic</option>
                </select>
              </div>

              <div>
                <label className="font-bold text-slate-500 uppercase tracking-wider block mb-1">Custom Notes / Angle</label>
                <input
                  type="text"
                  value={customInstructions}
                  onChange={(e) => setCustomInstructions(e.target.value)}
                  placeholder="e.g. mention portfolio links or 20% discount"
                  className="w-full rounded-xl border border-slate-200 p-2 text-xs font-medium outline-none"
                />
              </div>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-bold text-slate-600 block mb-1">Subject Line</label>
                <input
                  type="text"
                  value={emailSubject}
                  onChange={(e) => setEmailSubject(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 p-2.5 text-sm font-semibold text-slate-900 outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-600 block mb-1">Email Body Draft (Editable)</label>
                <textarea
                  rows={8}
                  value={emailBody}
                  onChange={(e) => setEmailBody(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 p-3 text-sm text-slate-800 leading-relaxed outline-none focus:border-sky-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-between border-t border-slate-100 pt-3">
              <button
                onClick={handleGenerateEmail}
                disabled={generatingEmail}
                className="inline-flex items-center gap-1.5 text-xs font-bold text-sky-600 hover:text-sky-700 disabled:opacity-50"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${generatingEmail ? "animate-spin" : ""}`} /> Regenerate Draft
              </button>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleCopyEmail}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-slate-900 px-4 py-2 text-xs font-bold text-white hover:bg-slate-800 transition"
                >
                  {copiedEmail ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                  {copiedEmail ? "Copied to Clipboard!" : "Copy Subject & Body"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-slate-900">Delete Lead?</h3>
            <p className="mt-2 text-xs leading-relaxed text-slate-500">
              Are you sure you want to delete <strong className="text-slate-800">{lead.name}</strong>? This action cannot be undone.
            </p>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                className="rounded-xl bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-500"
              >
                Confirm Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
