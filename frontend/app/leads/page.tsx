"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import {
  createDiscoverySource,
  createLead,
  deleteDiscoverySource,
  deleteLead,
  getDiscoveryRuns,
  getDiscoverySources,
  getLeads,
  getServices,
  importCSVLeads,
  importManualLead,
  runLeadDiscovery,
  updateDiscoverySource,
  updateLead,
} from "@/lib/api";
import {
  CSVImportResult,
  DiscoveryRun,
  DiscoverySource,
  Lead,
  LeadCreate,
  LeadSource,
  LeadStatus,
  ManualLeadImportRequest,
  Service,
} from "@/types";
import {
  Users,
  Plus,
  Search,
  Filter,
  ArrowUpDown,
  ExternalLink,
  Trash2,
  CheckCircle,
  Clock,
  Sparkles,
  TrendingUp,
  AlertCircle,
  Loader2,
  ChevronRight,
  Layers,
  ShieldCheck,
  Compass,
  UploadCloud,
  FileSpreadsheet,
  Settings,
  History,
  Check,
  X,
  Flame,
  Radio,
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

const ALL_SOURCES: LeadSource[] = [
  "MANUAL",
  "WEBSITE",
  "EMAIL",
  "FACEBOOK",
  "INSTAGRAM",
  "X",
  "LINKEDIN",
  "TIKTOK",
  "OTHER",
];

function getIntentBadge(score?: number | null) {
  if (score === undefined || score === null) {
    return { label: "UNSCORED", bg: "bg-slate-100", text: "text-slate-600", border: "border-slate-200" };
  }
  if (score >= 80) {
    return { label: `HOT (${score.toFixed(0)})`, bg: "bg-rose-50", text: "text-rose-700", border: "border-rose-200", icon: Flame };
  }
  if (score >= 60) {
    return { label: `HIGH (${score.toFixed(0)})`, bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200", icon: TrendingUp };
  }
  if (score >= 40) {
    return { label: `MEDIUM (${score.toFixed(0)})`, bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200", icon: Sparkles };
  }
  if (score >= 20) {
    return { label: `LOW (${score.toFixed(0)})`, bg: "bg-slate-100", text: "text-slate-600", border: "border-slate-200" };
  }
  return { label: `VERY LOW (${score.toFixed(0)})`, bg: "bg-gray-100", text: "text-gray-500", border: "border-gray-200" };
}

export default function LeadsPage() {
  const { user, token } = useAuth();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [sources, setSources] = useState<DiscoverySource[]>([]);
  const [runs, setRuns] = useState<DiscoveryRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Search
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [sourceFilter, setSourceFilter] = useState<string>("");
  const [serviceFilter, setServiceFilter] = useState<string>("");
  const [intentCategoryFilter, setIntentCategoryFilter] = useState<string>("");
  const [sortBy, setSortBy] = useState<string>("created_at");
  const [sortDir, setSortDir] = useState<string>("desc");

  // Discovery Action State
  const [discovering, setDiscovering] = useState(false);
  const [discoverySuccessMsg, setDiscoverySuccessMsg] = useState<string | null>(null);

  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showSourcesModal, setShowSourcesModal] = useState(false);
  const [showRunsModal, setShowRunsModal] = useState(false);
  const [deletingLeadId, setDeletingLeadId] = useState<string | null>(null);

  // Import State
  const [importMode, setImportMode] = useState<"csv" | "manual">("csv");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [csvResult, setCsvResult] = useState<CSVImportResult | null>(null);
  const [manualForm, setManualForm] = useState<ManualLeadImportRequest>({
    name: "",
    company: "",
    email: "",
    phone: "",
    website: "",
    location: "",
    description: "",
    source: "MANUAL",
    analyze_with_ai: true,
  });

  // Source Creation State
  const [newSourceName, setNewSourceName] = useState("");
  const [newSourceType, setNewSourceType] = useState<"JOB_BOARD" | "RSS" | "API" | "MOCK">("JOB_BOARD");
  const [newSourceUrl, setNewSourceUrl] = useState("");
  const [creatingSource, setCreatingSource] = useState(false);

  // Form (Direct Add Lead)
  const [formData, setFormData] = useState<LeadCreate>({
    name: "",
    company: "",
    email: "",
    phone: "",
    website: "",
    platform: "",
    location: "",
    source: "MANUAL",
    source_url: "",
    description: "",
    detected_need: "",
    matched_service_id: "",
    intent_score: 50,
    status: "NEW",
    notes: "",
  });

  const fetchData = async () => {
    if (!token) return;
    try {
      setLoading(true);
      setError(null);
      const [leadsData, servicesData, sourcesData] = await Promise.all([
        getLeads(token, {
          search: searchTerm || undefined,
          status: statusFilter || undefined,
          source: sourceFilter || undefined,
          matched_service_id: serviceFilter || undefined,
          sort_by: sortBy,
          sort_dir: sortDir,
        }),
        getServices(token),
        getDiscoverySources(token).catch(() => []),
      ]);
      setLeads(leadsData);
      setServices(servicesData);
      setSources(sourcesData);
    } catch (err: any) {
      setError(err.message || "Failed to load leads data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [token, searchTerm, statusFilter, sourceFilter, serviceFilter, sortBy, sortDir]);

  // Handle Trigger Discovery
  const handleTriggerDiscovery = async (sourceId?: string) => {
    if (!token) return;
    try {
      setDiscovering(true);
      setDiscoverySuccessMsg(null);
      const resultRuns = await runLeadDiscovery(token, {
        source_id: sourceId || null,
        analyze_with_ai: true,
      });

      const totalFound = resultRuns.reduce((acc, r) => acc + r.total_discovered, 0);
      const totalAccepted = resultRuns.reduce((acc, r) => acc + r.accepted_count, 0);
      const totalDup = resultRuns.reduce((acc, r) => acc + r.duplicate_count, 0);

      setDiscoverySuccessMsg(
        `Scout complete! Discovered ${totalFound} opportunities: ${totalAccepted} new leads added, ${totalDup} duplicates skipped.`
      );
      await fetchData();
    } catch (err: any) {
      setError(err.message || "Failed to run discovery scout");
    } finally {
      setDiscovering(false);
    }
  };

  // Handle CSV Import
  const handleCSVUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !selectedFile) return;
    try {
      setImporting(true);
      setCsvResult(null);
      const res = await importCSVLeads(token, selectedFile);
      setCsvResult(res);
      await fetchData();
    } catch (err: any) {
      setError(err.message || "Failed to import CSV");
    } finally {
      setImporting(false);
    }
  };

  // Handle Manual Lead Import
  const handleManualImport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    try {
      setImporting(true);
      await importManualLead(token, manualForm);
      setShowImportModal(false);
      setManualForm({
        name: "",
        company: "",
        email: "",
        phone: "",
        website: "",
        location: "",
        description: "",
        source: "MANUAL",
        analyze_with_ai: true,
      });
      await fetchData();
    } catch (err: any) {
      setError(err.message || "Failed to import manual lead");
    } finally {
      setImporting(false);
    }
  };

  // Handle Add Discovery Source
  const handleCreateSource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !newSourceName) return;
    try {
      setCreatingSource(true);
      const src = await createDiscoverySource(token, {
        name: newSourceName.trim(),
        source_type: newSourceType,
        feed_url: newSourceUrl.trim() || undefined,
        frequency: "DAILY",
        is_active: true,
      });
      setSources((prev) => [src, ...prev]);
      setNewSourceName("");
      setNewSourceUrl("");
    } catch (err: any) {
      setError(err.message || "Failed to create discovery source");
    } finally {
      setCreatingSource(false);
    }
  };

  // Handle Toggle Source Active
  const handleToggleSource = async (source: DiscoverySource) => {
    if (!token) return;
    try {
      const updated = await updateDiscoverySource(token, source.id, {
        is_active: !source.is_active,
      });
      setSources((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
    } catch (err: any) {
      setError(err.message || "Failed to update source");
    }
  };

  // Handle Delete Source
  const handleDeleteSource = async (sourceId: string) => {
    if (!token) return;
    try {
      await deleteDiscoverySource(token, sourceId);
      setSources((prev) => prev.filter((s) => s.id !== sourceId));
    } catch (err: any) {
      setError(err.message || "Failed to delete source");
    }
  };

  // Open Discovery Runs Drawer
  const handleOpenRuns = async () => {
    if (!token) return;
    try {
      const runsData = await getDiscoveryRuns(token);
      setRuns(runsData);
      setShowRunsModal(true);
    } catch (err: any) {
      setError(err.message || "Failed to load discovery history");
    }
  };

  // Handle Direct Lead Creation
  const handleCreateLead = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    try {
      await createLead(token, {
        ...formData,
        matched_service_id: formData.matched_service_id || undefined,
      });
      setShowAddModal(false);
      setFormData({
        name: "",
        company: "",
        email: "",
        phone: "",
        website: "",
        platform: "",
        location: "",
        source: "MANUAL",
        source_url: "",
        description: "",
        detected_need: "",
        matched_service_id: "",
        intent_score: 50,
        status: "NEW",
        notes: "",
      });
      await fetchData();
    } catch (err: any) {
      setError(err.message || "Failed to create lead");
    }
  };

  // Filter leads by intent category client-side
  const filteredLeads = leads.filter((lead) => {
    if (!intentCategoryFilter) return true;
    const score = lead.intent_score ?? 0;
    if (intentCategoryFilter === "HOT") return score >= 80;
    if (intentCategoryFilter === "HIGH") return score >= 60 && score < 80;
    if (intentCategoryFilter === "MEDIUM") return score >= 40 && score < 60;
    if (intentCategoryFilter === "LOW") return score >= 20 && score < 40;
    if (intentCategoryFilter === "VERY_LOW") return score < 20;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Top Header & Scout Action Toolbar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Compass className="h-7 w-7 text-indigo-600" />
            Lead Discovery & Pipeline
          </h1>
          <p className="text-sm text-slate-500">
            Scout legitimate global opportunities, analyze buyer intent with Gemini, and organize your client pipeline.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Scout Now Button */}
          <button
            onClick={() => handleTriggerDiscovery()}
            disabled={discovering}
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            {discovering ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            {discovering ? "Scouting Global Feeds..." : "Run Discovery Scout"}
          </button>

          {/* Import Button */}
          <button
            onClick={() => {
              setCsvResult(null);
              setShowImportModal(true);
            }}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 shadow-sm"
          >
            <UploadCloud className="h-4 w-4 text-slate-500" />
            Import (CSV / Manual)
          </button>

          {/* Sources Config */}
          <button
            onClick={() => setShowSourcesModal(true)}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 shadow-sm"
            title="Manage Discovery Sources"
          >
            <Settings className="h-4 w-4 text-slate-500" />
            Sources ({sources.filter((s) => s.is_active).length})
          </button>

          {/* History */}
          <button
            onClick={handleOpenRuns}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 shadow-sm"
            title="Discovery Run History"
          >
            <History className="h-4 w-4 text-slate-500" />
            Logs
          </button>

          {/* New Lead Manual */}
          <button
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-3.5 py-2 text-sm font-semibold text-white hover:bg-slate-800 shadow-sm"
          >
            <Plus className="h-4 w-4" />
            Add Lead
          </button>
        </div>
      </div>

      {/* Discovery Feedback Banner */}
      {discoverySuccessMsg && (
        <div className="flex items-center justify-between rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-emerald-600 flex-shrink-0" />
            <span>{discoverySuccessMsg}</span>
          </div>
          <button
            onClick={() => setDiscoverySuccessMsg(null)}
            className="text-emerald-600 hover:text-emerald-900"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 flex items-center gap-2">
          <AlertCircle className="h-5 w-5 text-rose-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Quick Metrics Bar */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-6">
        <div className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-sm">
          <p className="text-xs font-medium text-slate-500">Total Leads</p>
          <p className="mt-1 text-2xl font-bold text-slate-900">{leads.length}</p>
        </div>
        <div className="rounded-xl border border-rose-200 bg-rose-50/50 p-3.5 shadow-sm">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-rose-700">
            <Flame className="h-3.5 w-3.5" />
            Hot Opportunities
          </div>
          <p className="mt-1 text-2xl font-bold text-rose-900">
            {leads.filter((l) => (l.intent_score ?? 0) >= 80).length}
          </p>
        </div>
        <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-3.5 shadow-sm">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-700">
            <TrendingUp className="h-3.5 w-3.5" />
            High Intent
          </div>
          <p className="mt-1 text-2xl font-bold text-amber-900">
            {leads.filter((l) => (l.intent_score ?? 0) >= 60 && (l.intent_score ?? 0) < 80).length}
          </p>
        </div>
        <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-3.5 shadow-sm">
          <p className="text-xs font-medium text-blue-700">New Discovered</p>
          <p className="mt-1 text-2xl font-bold text-blue-900">
            {leads.filter((l) => l.status === "NEW").length}
          </p>
        </div>
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-3.5 shadow-sm">
          <p className="text-xs font-medium text-emerald-700">Won Clients</p>
          <p className="mt-1 text-2xl font-bold text-emerald-900">
            {leads.filter((l) => l.status === "WON").length}
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-sm">
          <p className="text-xs font-medium text-slate-500">Active Sources</p>
          <p className="mt-1 text-2xl font-bold text-slate-900">
            {sources.filter((s) => s.is_active).length}
          </p>
        </div>
      </div>

      {/* Filters & Intent Score Categorizer */}
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm space-y-3">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search leads, needs, company..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full rounded-lg border border-slate-300 pl-9 pr-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          {/* Service Filter */}
          <select
            value={serviceFilter}
            onChange={(e) => setServiceFilter(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">All Services</option>
            {services.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">All Pipeline Stages</option>
            {ALL_STATUSES.map((st) => (
              <option key={st} value={st}>
                {STATUS_CONFIG[st].label}
              </option>
            ))}
          </select>

          {/* Intent Score Tier Filter */}
          <select
            value={intentCategoryFilter}
            onChange={(e) => setIntentCategoryFilter(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-medium"
          >
            <option value="">All Intent Levels</option>
            <option value="HOT">🔥 HOT (80 - 100)</option>
            <option value="HIGH">📈 HIGH (60 - 79)</option>
            <option value="MEDIUM">⚡ MEDIUM (40 - 59)</option>
            <option value="LOW">LOW (20 - 39)</option>
            <option value="VERY_LOW">VERY LOW (0 - 19)</option>
          </select>

          {/* Sort */}
          <select
            value={`${sortBy}_${sortDir}`}
            onChange={(e) => {
              const [sb, sd] = e.target.value.split("_");
              setSortBy(sb);
              setSortDir(sd);
            }}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="intent_score_desc">Highest Intent Score</option>
            <option value="created_at_desc">Newest Discovered</option>
            <option value="created_at_asc">Oldest Discovered</option>
            <option value="name_asc">Name (A-Z)</option>
          </select>
        </div>
      </div>

      {/* Leads Table / Cards */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
          </div>
        ) : filteredLeads.length === 0 ? (
          <div className="p-12 text-center">
            <Compass className="mx-auto h-12 w-12 text-slate-300" />
            <h3 className="mt-4 text-base font-semibold text-slate-900">No opportunities found</h3>
            <p className="mt-1 text-sm text-slate-500">
              Run the discovery scout or import leads from a CSV file.
            </p>
            <div className="mt-6 flex justify-center gap-3">
              <button
                onClick={() => handleTriggerDiscovery()}
                className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
              >
                <Sparkles className="h-4 w-4" />
                Run Discovery Scout
              </button>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-4 py-3">Lead & Company</th>
                  <th className="px-4 py-3">Detected Need / Service</th>
                  <th className="px-4 py-3">Intent Score</th>
                  <th className="px-4 py-3">Source & Link</th>
                  <th className="px-4 py-3">Stage</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {filteredLeads.map((lead) => {
                  const statusInfo = STATUS_CONFIG[lead.status as LeadStatus] || STATUS_CONFIG.NEW;
                  const intentInfo = getIntentBadge(lead.intent_score);

                  return (
                    <tr key={lead.id} className="hover:bg-slate-50/80 transition-colors">
                      {/* Name & Company */}
                      <td className="px-4 py-3.5">
                        <Link
                          href={`/leads/${lead.id}`}
                          className="font-semibold text-indigo-600 hover:text-indigo-900 flex items-center gap-1.5"
                        >
                          {lead.name}
                          <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
                        </Link>
                        <p className="text-xs text-slate-500">{lead.company || "Independent Prospect"}</p>
                        {lead.location && (
                          <span className="mt-0.5 inline-block text-[11px] text-slate-400">
                            📍 {lead.location}
                          </span>
                        )}
                      </td>

                      {/* Detected Need & Matched Service */}
                      <td className="px-4 py-3.5 max-w-xs">
                        <div className="text-xs font-medium text-slate-900 line-clamp-2">
                          {lead.detected_need || lead.description || "No need analyzed yet"}
                        </div>
                        {lead.matched_service && (
                          <span className="mt-1 inline-flex items-center gap-1 rounded bg-indigo-50 px-1.5 py-0.5 text-[11px] font-medium text-indigo-700 border border-indigo-200">
                            🎯 {lead.matched_service.name}
                          </span>
                        )}
                      </td>

                      {/* Intent Score */}
                      <td className="px-4 py-3.5">
                        <span
                          className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${intentInfo.bg} ${intentInfo.text} ${intentInfo.border}`}
                        >
                          {intentInfo.icon && <intentInfo.icon className="h-3 w-3" />}
                          {intentInfo.label}
                        </span>
                      </td>

                      {/* Source & Opportunity Link */}
                      <td className="px-4 py-3.5">
                        <div className="text-xs font-medium text-slate-700">{lead.source}</div>
                        {lead.source_url ? (
                          <a
                            href={lead.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="mt-0.5 inline-flex items-center gap-1 text-xs text-indigo-600 hover:underline"
                          >
                            <span>Open Post</span>
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        ) : (
                          <span className="text-[11px] text-slate-400">Direct Scout</span>
                        )}
                      </td>

                      {/* Stage Dropdown */}
                      <td className="px-4 py-3.5">
                        <select
                          value={lead.status}
                          onChange={async (e) => {
                            if (!token) return;
                            const newStatus = e.target.value as LeadStatus;
                            await updateLead(token, lead.id, { status: newStatus });
                            setLeads((prev) =>
                              prev.map((l) => (l.id === lead.id ? { ...l, status: newStatus } : l))
                            );
                          }}
                          className={`rounded border px-2 py-1 text-xs font-semibold ${statusInfo.bg} ${statusInfo.text} ${statusInfo.border} focus:outline-none`}
                        >
                          {ALL_STATUSES.map((st) => (
                            <option key={st} value={st}>
                              {STATUS_CONFIG[st].label}
                            </option>
                          ))}
                        </select>
                      </td>

                      {/* Actions */}
                      <td className="px-4 py-3.5 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Link
                            href={`/leads/${lead.id}`}
                            className="rounded p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-800"
                            title="View Lead Details"
                          >
                            <ChevronRight className="h-4 w-4" />
                          </Link>
                          <button
                            onClick={async () => {
                              if (!token || !confirm("Delete this lead?")) return;
                              await deleteLead(token, lead.id);
                              setLeads((prev) => prev.filter((l) => l.id !== lead.id));
                            }}
                            className="rounded p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600"
                            title="Delete Lead"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal: Import Leads (CSV & Manual) */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <UploadCloud className="h-5 w-5 text-indigo-600" />
                Import Prospective Leads
              </h3>
              <button onClick={() => setShowImportModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Mode Switcher */}
            <div className="flex rounded-lg bg-slate-100 p-1">
              <button
                type="button"
                onClick={() => setImportMode("csv")}
                className={`flex-1 rounded-md py-1.5 text-xs font-semibold ${
                  importMode === "csv" ? "bg-white text-indigo-700 shadow-sm" : "text-slate-600"
                }`}
              >
                CSV File Upload
              </button>
              <button
                type="button"
                onClick={() => setImportMode("manual")}
                className={`flex-1 rounded-md py-1.5 text-xs font-semibold ${
                  importMode === "manual" ? "bg-white text-indigo-700 shadow-sm" : "text-slate-600"
                }`}
              >
                Manual Entry
              </button>
            </div>

            {/* CSV Upload Mode */}
            {importMode === "csv" && (
              <form onSubmit={handleCSVUpload} className="space-y-4">
                <div className="rounded-xl border-2 border-dashed border-slate-300 p-6 text-center hover:border-indigo-500 transition-colors">
                  <FileSpreadsheet className="mx-auto h-10 w-10 text-slate-400" />
                  <p className="mt-2 text-sm font-medium text-slate-700">
                    {selectedFile ? selectedFile.name : "Select a .csv file to import"}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    Columns supported: name, company, email, phone, website, description/need, source
                  </p>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    className="mt-3 text-xs text-slate-500 file:mr-2 file:rounded-lg file:border-0 file:bg-indigo-50 file:px-3 file:py-1 file:text-xs file:font-semibold file:text-indigo-700"
                  />
                </div>

                {csvResult && (
                  <div className="rounded-lg bg-slate-50 border p-3 text-xs space-y-1">
                    <p className="font-semibold text-slate-900">
                      Import Summary: {csvResult.imported_count} imported, {csvResult.duplicate_count} duplicates skipped, {csvResult.rejected_count} rejected.
                    </p>
                    {csvResult.errors.length > 0 && (
                      <div className="mt-2 max-h-32 overflow-y-auto space-y-1 text-rose-600">
                        {csvResult.errors.map((err, idx) => (
                          <p key={idx}>Row {err.row_number}: {err.error}</p>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowImportModal(false)}
                    className="rounded-lg border px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={!selectedFile || importing}
                    className="rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-1.5"
                  >
                    {importing && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                    {importing ? "Importing CSV..." : "Start CSV Import"}
                  </button>
                </div>
              </form>
            )}

            {/* Manual Entry Mode */}
            {importMode === "manual" && (
              <form onSubmit={handleManualImport} className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium text-slate-700">Prospect / Lead Name *</label>
                    <input
                      type="text"
                      required
                      value={manualForm.name}
                      onChange={(e) => setManualForm({ ...manualForm, name: e.target.value })}
                      className="mt-1 w-full rounded border px-3 py-1.5 text-xs focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-slate-700">Company</label>
                    <input
                      type="text"
                      value={manualForm.company || ""}
                      onChange={(e) => setManualForm({ ...manualForm, company: e.target.value })}
                      className="mt-1 w-full rounded border px-3 py-1.5 text-xs"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium text-slate-700">Email</label>
                    <input
                      type="email"
                      value={manualForm.email || ""}
                      onChange={(e) => setManualForm({ ...manualForm, email: e.target.value })}
                      className="mt-1 w-full rounded border px-3 py-1.5 text-xs"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-slate-700">Website</label>
                    <input
                      type="url"
                      value={manualForm.website || ""}
                      onChange={(e) => setManualForm({ ...manualForm, website: e.target.value })}
                      className="mt-1 w-full rounded border px-3 py-1.5 text-xs"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-700">Opportunity Details / Stated Need *</label>
                  <textarea
                    required
                    rows={3}
                    value={manualForm.description}
                    onChange={(e) => setManualForm({ ...manualForm, description: e.target.value })}
                    placeholder="Describe client requirements, project scope, or outreach context..."
                    className="mt-1 w-full rounded border px-3 py-1.5 text-xs"
                  />
                </div>

                <div className="flex items-center gap-2 pt-1">
                  <input
                    type="checkbox"
                    id="ai_enrich"
                    checked={manualForm.analyze_with_ai}
                    onChange={(e) => setManualForm({ ...manualForm, analyze_with_ai: e.target.checked })}
                    className="rounded border-slate-300 text-indigo-600"
                  />
                  <label htmlFor="ai_enrich" className="text-xs text-slate-700 flex items-center gap-1 font-medium">
                    <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
                    Auto-analyze need & match services using Gemini AI
                  </label>
                </div>

                <div className="flex justify-end gap-2 pt-3 border-t">
                  <button
                    type="button"
                    onClick={() => setShowImportModal(false)}
                    className="rounded-lg border px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={importing}
                    className="rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-1.5"
                  >
                    {importing && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                    {importing ? "Saving Lead..." : "Save Lead"}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* Modal: Discovery Sources Configuration */}
      {showSourcesModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
          <div className="w-full max-w-xl rounded-2xl bg-white p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Settings className="h-5 w-5 text-indigo-600" />
                Discovery Sources & Feeds
              </h3>
              <button onClick={() => setShowSourcesModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Add Source Form */}
            <form onSubmit={handleCreateSource} className="rounded-xl bg-slate-50 p-4 border space-y-3">
              <h4 className="text-xs font-bold uppercase text-slate-700 tracking-wider">Configure New Feed</h4>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-slate-700">Source Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. RemoteOK Web Dev"
                    value={newSourceName}
                    onChange={(e) => setNewSourceName(e.target.value)}
                    className="mt-1 w-full rounded border px-3 py-1.5 text-xs"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-700">Type</label>
                  <select
                    value={newSourceType}
                    onChange={(e) => setNewSourceType(e.target.value as any)}
                    className="mt-1 w-full rounded border px-3 py-1.5 text-xs"
                  >
                    <option value="JOB_BOARD">Job Board (JSON)</option>
                    <option value="RSS">RSS Feed (XML)</option>
                    <option value="MOCK">Mock Sample Feed</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-slate-700">Feed / API Endpoint URL</label>
                <input
                  type="url"
                  placeholder="https://remoteok.com/api"
                  value={newSourceUrl}
                  onChange={(e) => setNewSourceUrl(e.target.value)}
                  className="mt-1 w-full rounded border px-3 py-1.5 text-xs"
                />
              </div>
              <button
                type="submit"
                disabled={creatingSource || !newSourceName}
                className="rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {creatingSource ? "Adding..." : "+ Add Source"}
              </button>
            </form>

            {/* List of Configured Sources */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase text-slate-700 tracking-wider">Active Configured Sources</h4>
              {sources.length === 0 ? (
                <p className="text-xs text-slate-400 py-4 text-center">No custom sources configured.</p>
              ) : (
                sources.map((src) => (
                  <div key={src.id} className="flex items-center justify-between rounded-lg border p-3 hover:bg-slate-50">
                    <div>
                      <p className="text-sm font-semibold text-slate-900">{src.name}</p>
                      <p className="text-xs text-slate-500">{src.source_type} • {src.feed_url || "Built-in Scout Feed"}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleToggleSource(src)}
                        className={`rounded-full px-2.5 py-0.5 text-xs font-semibold border ${
                          src.is_active
                            ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                            : "bg-slate-100 text-slate-500 border-slate-200"
                        }`}
                      >
                        {src.is_active ? "Active" : "Disabled"}
                      </button>
                      <button
                        onClick={() => handleDeleteSource(src.id)}
                        className="p-1 text-slate-400 hover:text-rose-600"
                        title="Delete Source"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal: Discovery Run History */}
      {showRunsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
          <div className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <History className="h-5 w-5 text-indigo-600" />
                Discovery Scout History & Metrics
              </h3>
              <button onClick={() => setShowRunsModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-3">
              {runs.length === 0 ? (
                <p className="text-xs text-slate-400 py-6 text-center">No discovery runs recorded yet.</p>
              ) : (
                runs.map((r) => (
                  <div key={r.id} className="rounded-xl border p-4 text-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <span className={`font-bold px-2 py-0.5 rounded ${
                        r.status === "SUCCESS" ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
                      }`}>
                        {r.status}
                      </span>
                      <span className="text-slate-400">
                        {new Date(r.started_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="grid grid-cols-4 gap-2 text-center pt-1 border-t">
                      <div>
                        <p className="text-slate-400">Discovered</p>
                        <p className="font-bold text-slate-900 text-sm">{r.total_discovered}</p>
                      </div>
                      <div>
                        <p className="text-slate-400">Accepted</p>
                        <p className="font-bold text-emerald-600 text-sm">{r.accepted_count}</p>
                      </div>
                      <div>
                        <p className="text-slate-400">Duplicates</p>
                        <p className="font-bold text-amber-600 text-sm">{r.duplicate_count}</p>
                      </div>
                      <div>
                        <p className="text-slate-400">Rejected</p>
                        <p className="font-bold text-rose-600 text-sm">{r.rejected_count}</p>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal: Direct Add Lead */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-slate-900">Add Lead Manually</h3>
              <button onClick={() => setShowAddModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleCreateLead} className="space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-700">Lead Name *</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="mt-1 w-full rounded border px-3 py-1.5 text-xs"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-700">Company</label>
                <input
                  type="text"
                  value={formData.company || ""}
                  onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                  className="mt-1 w-full rounded border px-3 py-1.5 text-xs"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-700">Opportunity Description *</label>
                <textarea
                  required
                  rows={3}
                  value={formData.description || ""}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="mt-1 w-full rounded border px-3 py-1.5 text-xs"
                />
              </div>
              <div className="flex justify-end gap-2 pt-3 border-t">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="rounded-lg border px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800"
                >
                  Save Lead
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
