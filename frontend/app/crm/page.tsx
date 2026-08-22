"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import {
  convertLeadToClient,
  getCRMDashboard,
  getLeads,
  getServices,
  updateLeadStage,
} from "@/lib/api";
import {
  CRMDashboardMetrics,
  Lead,
  LeadStage,
  ServiceItem,
} from "@/types";
import {
  Briefcase,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  ArrowRight,
  User,
  Plus,
  RefreshCw,
  Sparkles,
  Phone,
  Mail,
  ShieldCheck,
  Check,
  Loader2,
  DollarSign,
  ChevronRight,
  Filter,
} from "lucide-react";

const PIPELINE_STAGES: { key: LeadStage; label: string; color: string; bg: string }[] = [
  { key: "NEW", label: "New Leads", color: "text-slate-700", bg: "bg-slate-100" },
  { key: "QUALIFIED", label: "Qualified", color: "text-indigo-700", bg: "bg-indigo-50" },
  { key: "CONTACTED", label: "Contacted", color: "text-sky-700", bg: "bg-sky-50" },
  { key: "REPLIED", label: "Replied", color: "text-emerald-700", bg: "bg-emerald-50" },
  { key: "INTERESTED", label: "Interested", color: "text-teal-700", bg: "bg-teal-50" },
  { key: "DISCOVERY", label: "Discovery", color: "text-amber-700", bg: "bg-amber-50" },
  { key: "PROPOSAL", label: "Proposal Sent", color: "text-purple-700", bg: "bg-purple-50" },
  { key: "NEGOTIATION", label: "Negotiation", color: "text-orange-700", bg: "bg-orange-50" },
  { key: "WON", label: "Deals Won 🎉", color: "text-emerald-800", bg: "bg-emerald-100" },
  { key: "LOST", label: "Lost Deals", color: "text-rose-700", bg: "bg-rose-50" },
];

export default function CRMPage() {
  const { token } = useAuth();

  // State
  const [leads, setLeads] = useState<Lead[]>([]);
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [metrics, setMetrics] = useState<CRMDashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionBusy, setActionBusy] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Conversion Modal
  const [showConvertModal, setShowConvertModal] = useState(false);
  const [selectedLeadForConvert, setSelectedLeadForConvert] = useState<Lead | null>(null);
  const [convertServiceId, setConvertServiceId] = useState("");
  const [convertNotes, setConvertNotes] = useState("");

  // Transition Note Modal
  const [showStageModal, setShowStageModal] = useState(false);
  const [activeLead, setActiveLead] = useState<Lead | null>(null);
  const [targetStage, setTargetStage] = useState<LeadStage>("QUALIFIED");
  const [stageNotes, setStageNotes] = useState("");

  const loadData = async () => {
    if (!token) return;
    try {
      setLoading(true);
      setErrorMsg(null);

      const [leadsData, metricsData, servicesData] = await Promise.all([
        getLeads(token).catch(() => []),
        getCRMDashboard(token).catch(() => null),
        getServices(token).catch(() => []),
      ]);

      setLeads(leadsData);
      setMetrics(metricsData);
      setServices(servicesData);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load CRM data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token]);

  // Stage Update Handler
  const handleStageSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !activeLead) return;

    try {
      setActionBusy(true);
      setErrorMsg(null);
      await updateLeadStage(token, activeLead.id, targetStage, stageNotes.trim() || undefined);
      setSuccessMsg(`Lead stage updated to ${targetStage}`);
      setShowStageModal(false);
      setActiveLead(null);
      setStageNotes("");
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to update lead stage.");
    } finally {
      setActionBusy(false);
    }
  };

  // Convert to Client Handler
  const handleConvertSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !selectedLeadForConvert) return;

    try {
      setActionBusy(true);
      setErrorMsg(null);
      await convertLeadToClient(token, selectedLeadForConvert.id, {
        service_id: convertServiceId || undefined,
        notes: convertNotes.trim() || undefined,
        status: "ACTIVE",
      });
      setSuccessMsg(`Lead '${selectedLeadForConvert.name}' successfully converted to Client!`);
      setShowConvertModal(false);
      setSelectedLeadForConvert(null);
      setConvertNotes("");
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to convert lead to client.");
    } finally {
      setActionBusy(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header & KPI Summary */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Briefcase className="h-7 w-7 text-indigo-600" />
            CRM Lead Pipeline & Deal Flow
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Visual 9-stage sales pipeline with automated state tracking and instant Client conversion.
          </p>
        </div>

        <button
          onClick={loadData}
          className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-sm self-start sm:self-auto"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh Pipeline
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

      {/* KPI Cards */}
      {metrics && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
          <div className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-xs">
            <span className="text-[11px] font-semibold text-slate-400 block">Total Leads</span>
            <span className="text-xl font-bold text-slate-900">{metrics.total_leads}</span>
          </div>
          <div className="rounded-xl border border-indigo-100 bg-indigo-50/40 p-3.5 shadow-xs">
            <span className="text-[11px] font-semibold text-indigo-600 block">Qualified</span>
            <span className="text-xl font-bold text-indigo-950">{metrics.qualified_leads}</span>
          </div>
          <div className="rounded-xl border border-sky-100 bg-sky-50/40 p-3.5 shadow-xs">
            <span className="text-[11px] font-semibold text-sky-600 block">Conversations</span>
            <span className="text-xl font-bold text-sky-950">{metrics.active_conversations}</span>
          </div>
          <div className="rounded-xl border border-amber-100 bg-amber-50/40 p-3.5 shadow-xs">
            <span className="text-[11px] font-semibold text-amber-700 block">Follow-ups Due</span>
            <span className="text-xl font-bold text-amber-950">{metrics.follow_ups_due}</span>
          </div>
          <div className="rounded-xl border border-emerald-100 bg-emerald-50/40 p-3.5 shadow-xs">
            <span className="text-[11px] font-semibold text-emerald-700 block">Active Clients</span>
            <span className="text-xl font-bold text-emerald-950">{metrics.active_clients}</span>
          </div>
          <div className="rounded-xl border border-emerald-200 bg-emerald-100/60 p-3.5 shadow-xs">
            <span className="text-[11px] font-semibold text-emerald-800 block">Won Deals 🎉</span>
            <span className="text-xl font-bold text-emerald-950">{metrics.won_deals}</span>
          </div>
          <div className="rounded-xl border border-rose-100 bg-rose-50/40 p-3.5 shadow-xs">
            <span className="text-[11px] font-semibold text-rose-600 block">Lost Deals</span>
            <span className="text-xl font-bold text-rose-950">{metrics.lost_deals}</span>
          </div>
        </div>
      )}

      {/* Horizontal Scrollable Pipeline Kanban Board */}
      <div className="flex gap-4 overflow-x-auto pb-6 min-h-[600px]">
        {PIPELINE_STAGES.map((col) => {
          const stageLeads = leads.filter((l) => (l.status || "NEW").toUpperCase() === col.key);

          return (
            <div
              key={col.key}
              className="flex-shrink-0 w-72 rounded-2xl border border-slate-200 bg-slate-50/70 p-3.5 flex flex-col justify-between space-y-3"
            >
              {/* Column Header */}
              <div className="flex items-center justify-between border-b border-slate-200/80 pb-2.5">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded-lg text-xs font-bold ${col.bg} ${col.color}`}>
                    {col.label}
                  </span>
                </div>
                <span className="text-xs font-bold text-slate-400">{stageLeads.length}</span>
              </div>

              {/* Lead Cards List */}
              <div className="flex-1 overflow-y-auto space-y-3 pr-1">
                {stageLeads.length === 0 ? (
                  <div className="text-center py-10 text-[11px] text-slate-400 border border-dashed border-slate-200 rounded-xl">
                    No leads in this stage
                  </div>
                ) : (
                  stageLeads.map((lead) => (
                    <div
                      key={lead.id}
                      className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-xs space-y-2.5 hover:shadow-md transition"
                    >
                      <div className="flex items-center justify-between">
                        <h4 className="font-bold text-xs text-slate-900 truncate">{lead.name}</h4>
                        <span className="text-[10px] font-bold text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded">
                          {Math.round(lead.intent_score * 100)}% Match
                        </span>
                      </div>

                      {lead.company && (
                        <p className="text-[11px] font-medium text-slate-500 truncate">
                          🏢 {lead.company}
                        </p>
                      )}

                      {lead.detected_need && (
                        <p className="text-[11px] text-slate-600 line-clamp-2 leading-relaxed">
                          {lead.detected_need}
                        </p>
                      )}

                      <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-100">
                        <span className="capitalize">{lead.source || "Manual"}</span>
                        <span>{new Date(lead.created_at).toLocaleDateString([], { month: "short", day: "numeric" })}</span>
                      </div>

                      {/* Action Stage Buttons */}
                      <div className="flex items-center justify-between pt-1 gap-1.5">
                        <button
                          onClick={() => {
                            setActiveLead(lead);
                            setTargetStage(col.key);
                            setShowStageModal(true);
                          }}
                          className="flex-1 rounded-lg border border-slate-200 py-1 text-[10px] font-semibold text-slate-600 hover:bg-slate-50 flex items-center justify-center gap-1"
                        >
                          Move Stage <ChevronRight className="h-3 w-3" />
                        </button>

                        {col.key === "WON" && (
                          <button
                            onClick={() => {
                              setSelectedLeadForConvert(lead);
                              setConvertServiceId(lead.matched_service_id || "");
                              setShowConvertModal(true);
                            }}
                            className="rounded-lg bg-emerald-600 px-2 py-1 text-[10px] font-bold text-white hover:bg-emerald-700 shadow-xs"
                          >
                            Convert
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Move Stage Modal */}
      {showStageModal && activeLead && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-xs animate-in fade-in">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl border border-slate-100 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 text-sm">Update Lead Stage</h3>
              <button
                onClick={() => setShowStageModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleStageSubmit} className="space-y-3.5">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Lead</label>
                <input
                  type="text"
                  disabled
                  value={`${activeLead.name} (${activeLead.company || "Direct"})`}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-xs text-slate-600"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Target Pipeline Stage *</label>
                <select
                  value={targetStage}
                  onChange={(e) => setTargetStage(e.target.value as LeadStage)}
                  className="w-full rounded-xl border border-slate-200 p-2.5 text-xs font-semibold outline-none focus:border-indigo-500"
                >
                  {PIPELINE_STAGES.map((s) => (
                    <option key={s.key} value={s.key}>
                      {s.label} ({s.key})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Transition Rationale / Notes</label>
                <textarea
                  rows={3}
                  value={stageNotes}
                  onChange={(e) => setStageNotes(e.target.value)}
                  placeholder="e.g. Sent official pricing proposal after Zoom discovery call..."
                  className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowStageModal(false)}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionBusy}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-700 shadow-sm"
                >
                  {actionBusy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />}
                  Confirm Transition
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Convert to Client Modal */}
      {showConvertModal && selectedLeadForConvert && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-xs animate-in fade-in">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl border border-slate-100 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 text-sm">Convert Won Deal to Client</h3>
              <button
                onClick={() => setShowConvertModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleConvertSubmit} className="space-y-3.5">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Client Name</label>
                <input
                  type="text"
                  disabled
                  value={selectedLeadForConvert.name}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-xs text-slate-600"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Purchased Service</label>
                <select
                  value={convertServiceId}
                  onChange={(e) => setConvertServiceId(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 p-2.5 text-xs font-semibold outline-none focus:border-emerald-500"
                >
                  <option value="">-- Select Purchased Service --</option>
                  {services.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Client Onboarding Notes</label>
                <textarea
                  rows={3}
                  value={convertNotes}
                  onChange={(e) => setConvertNotes(e.target.value)}
                  placeholder="e.g. Kickoff scheduled for next Monday, 50% deposit received."
                  className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowConvertModal(false)}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionBusy}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-bold text-white hover:bg-emerald-700 shadow-sm"
                >
                  {actionBusy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />}
                  Create Client Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
