"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import {
  createClient,
  getClientActivities,
  getClients,
  getServices,
  updateClient,
} from "@/lib/api";
import {
  ActivityLogItem,
  ClientItem,
  ClientStatus,
  ServiceItem,
} from "@/types";
import {
  Briefcase,
  Plus,
  Search,
  CheckCircle2,
  AlertCircle,
  Clock,
  Mail,
  Phone,
  Globe,
  Edit3,
  RefreshCw,
  Loader2,
  Check,
  History,
  X,
} from "lucide-react";

export default function ClientsPage() {
  const { token } = useAuth();

  // State
  const [clients, setClients] = useState<ClientItem[]>([]);
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  const [loading, setLoading] = useState(true);
  const [actionBusy, setActionBusy] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Create Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [website, setWebsite] = useState("");
  const [serviceId, setServiceId] = useState("");
  const [status, setStatus] = useState<ClientStatus>("ACTIVE");
  const [notes, setNotes] = useState("");

  // Timeline Drawer State
  const [showTimelineDrawer, setShowTimelineDrawer] = useState(false);
  const [timelineClient, setTimelineClient] = useState<ClientItem | null>(null);
  const [activities, setActivities] = useState<ActivityLogItem[]>([]);
  const [loadingTimeline, setLoadingTimeline] = useState(false);

  const loadData = async () => {
    if (!token) return;
    try {
      setLoading(true);
      setErrorMsg(null);

      const [clientsData, servicesData] = await Promise.all([
        getClients(token, {
          status: statusFilter !== "ALL" ? statusFilter : undefined,
          q: searchQuery.trim() || undefined,
        }).catch(() => []),
        getServices(token).catch(() => []),
      ]);

      setClients(clientsData);
      setServices(servicesData);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load clients.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token, statusFilter]);

  // Create Client Submit
  const handleCreateClient = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !name.trim()) return;

    try {
      setActionBusy(true);
      setErrorMsg(null);
      await createClient(token, {
        name: name.trim(),
        company: company.trim() || undefined,
        email: email.trim() || undefined,
        phone: phone.trim() || undefined,
        website: website.trim() || undefined,
        service_id: serviceId || undefined,
        status,
        notes: notes.trim() || undefined,
      });

      setSuccessMsg(`Client '${name}' created successfully!`);
      setShowCreateModal(false);
      setName("");
      setCompany("");
      setEmail("");
      setPhone("");
      setWebsite("");
      setNotes("");
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to create client.");
    } finally {
      setActionBusy(false);
    }
  };

  // Update Status
  const handleUpdateStatus = async (clientId: string, newStatus: ClientStatus) => {
    if (!token) return;
    try {
      setActionBusy(true);
      await updateClient(token, clientId, { status: newStatus });
      setSuccessMsg("Client status updated.");
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to update status.");
    } finally {
      setActionBusy(false);
    }
  };

  // Open Timeline Drawer
  const handleOpenTimeline = async (client: ClientItem) => {
    if (!token) return;
    setTimelineClient(client);
    setShowTimelineDrawer(true);
    try {
      setLoadingTimeline(true);
      const data = await getClientActivities(token, client.id);
      setActivities(data.activities || []);
    } catch (err: any) {
      setActivities([]);
    } finally {
      setLoadingTimeline(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Briefcase className="h-7 w-7 text-indigo-600" />
            Client Directory & Retainers
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Manage active client engagements, contract retainers, and relationship activity history.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-700 shadow-sm"
          >
            <Plus className="h-4 w-4" />
            Add Client
          </button>
          <button
            onClick={loadData}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-sm"
          >
            <RefreshCw className="h-3.5 w-3.5" />
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

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto">
          {["ALL", "ACTIVE", "COMPLETED", "PAUSED", "LOST"].map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`rounded-xl px-3.5 py-1.5 text-xs font-bold transition ${
                statusFilter === s
                  ? "bg-indigo-600 text-white shadow-xs"
                  : "bg-slate-50 text-slate-600 hover:bg-slate-100"
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="h-4 w-4 absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && loadData()}
            placeholder="Search client name, company, email..."
            className="w-full rounded-xl border border-slate-200 bg-slate-50/50 py-2 pl-9 pr-3 text-xs outline-none focus:border-indigo-500 bg-white"
          />
        </div>
      </div>

      {/* Clients Cards Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {loading ? (
          <div className="col-span-full py-16 text-center text-xs text-slate-400">
            <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2 text-indigo-500" />
            Loading clients directory...
          </div>
        ) : clients.length === 0 ? (
          <div className="col-span-full py-16 text-center text-xs text-slate-400 bg-white rounded-2xl border border-slate-200">
            <Briefcase className="h-10 w-10 mx-auto mb-2 text-slate-300" />
            No client records found. Convert won leads in the CRM or click Add Client.
          </div>
        ) : (
          clients.map((client) => (
            <div
              key={client.id}
              className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm flex flex-col justify-between space-y-4 hover:shadow-md transition"
            >
              <div className="space-y-2.5">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="font-bold text-slate-900 text-sm">{client.name}</h3>
                    {client.company && (
                      <span className="text-xs font-semibold text-slate-500">🏢 {client.company}</span>
                    )}
                  </div>

                  <select
                    value={client.status}
                    onChange={(e) => handleUpdateStatus(client.id, e.target.value as ClientStatus)}
                    className={`rounded-lg px-2 py-0.5 text-[10px] font-bold outline-none ${
                      client.status === "ACTIVE"
                        ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                        : client.status === "COMPLETED"
                        ? "bg-indigo-50 text-indigo-700 border border-indigo-200"
                        : client.status === "PAUSED"
                        ? "bg-amber-50 text-amber-700 border border-amber-200"
                        : "bg-rose-50 text-rose-700 border border-rose-200"
                    }`}
                  >
                    <option value="ACTIVE">ACTIVE</option>
                    <option value="COMPLETED">COMPLETED</option>
                    <option value="PAUSED">PAUSED</option>
                    <option value="LOST">LOST</option>
                  </select>
                </div>

                {client.service_purchased && (
                  <div className="rounded-lg bg-indigo-50/50 p-2 text-xs font-semibold text-indigo-900">
                    🎯 Service: {client.service_purchased}
                  </div>
                )}

                <div className="space-y-1 text-xs text-slate-600">
                  {client.email && (
                    <div className="flex items-center gap-1.5 truncate">
                      <Mail className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
                      <a href={`mailto:${client.email}`} className="hover:underline">{client.email}</a>
                    </div>
                  )}
                  {client.phone && (
                    <div className="flex items-center gap-1.5">
                      <Phone className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
                      <span>{client.phone}</span>
                    </div>
                  )}
                  {client.website && (
                    <div className="flex items-center gap-1.5 truncate">
                      <Globe className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
                      <a href={client.website} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline">
                        {client.website}
                      </a>
                    </div>
                  )}
                </div>

                {client.notes && (
                  <p className="text-[11px] text-slate-500 line-clamp-2 italic pt-1 border-t border-slate-100">
                    "{client.notes}"
                  </p>
                )}
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-slate-100 text-[11px] text-slate-400">
                <span>Client since {new Date(client.created_at).toLocaleDateString([], { month: "short", year: "numeric" })}</span>
                <button
                  onClick={() => handleOpenTimeline(client)}
                  className="inline-flex items-center gap-1 font-bold text-indigo-600 hover:text-indigo-800"
                >
                  <History className="h-3.5 w-3.5" /> Timeline
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Activity Timeline Drawer */}
      {showTimelineDrawer && timelineClient && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40 backdrop-blur-xs animate-in fade-in">
          <div className="w-full max-w-md bg-white h-full shadow-2xl p-6 flex flex-col justify-between space-y-4 overflow-hidden">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                  <History className="h-4 w-4 text-indigo-600" />
                  Activity Timeline
                </h3>
                <span className="text-xs text-slate-500">{timelineClient.name} ({timelineClient.company || "Direct"})</span>
              </div>
              <button
                onClick={() => setShowTimelineDrawer(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-4 pr-1">
              {loadingTimeline ? (
                <div className="text-center py-12 text-xs text-slate-400">
                  <Loader2 className="h-5 w-5 animate-spin mx-auto mb-2 text-indigo-500" />
                  Loading activity timeline...
                </div>
              ) : activities.length === 0 ? (
                <div className="text-center py-12 text-xs text-slate-400">
                  No activity logged for this client yet.
                </div>
              ) : (
                activities.map((act) => (
                  <div key={act.id} className="relative pl-6 pb-4 border-l-2 border-slate-200 last:border-0 last:pb-0">
                    <span className="absolute -left-1.5 top-0.5 h-3 w-3 rounded-full bg-indigo-600 ring-4 ring-white" />
                    <div className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded">
                          {act.event_type}
                        </span>
                        <span className="text-[10px] text-slate-400">
                          {new Date(act.created_at).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                        </span>
                      </div>
                      <p className="text-xs text-slate-700">{act.description}</p>
                    </div>
                  </div>
                ))
              )}
            </div>

            <button
              onClick={() => setShowTimelineDrawer(false)}
              className="w-full rounded-xl bg-slate-100 py-2.5 text-xs font-bold text-slate-700 hover:bg-slate-200"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Create Client Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-xs animate-in fade-in">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl border border-slate-100 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 text-sm">Add New Client</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateClient} className="space-y-3.5">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Client / Contact Name *</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Sarah Jenkins"
                  className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="text-xs font-bold text-slate-700 block mb-1">Company</label>
                  <input
                    type="text"
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    placeholder="Acme Corp"
                    className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-bold text-slate-700 block mb-1">Status</label>
                  <select
                    value={status}
                    onChange={(e) => setStatus(e.target.value as ClientStatus)}
                    className="w-full rounded-xl border border-slate-200 p-2.5 text-xs font-semibold outline-none"
                  >
                    <option value="ACTIVE">ACTIVE</option>
                    <option value="COMPLETED">COMPLETED</option>
                    <option value="PAUSED">PAUSED</option>
                    <option value="LOST">LOST</option>
                  </select>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="text-xs font-bold text-slate-700 block mb-1">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="sarah@acme.com"
                    className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-bold text-slate-700 block mb-1">Phone</label>
                  <input
                    type="text"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+14155552671"
                    className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Website</label>
                <input
                  type="url"
                  value={website}
                  onChange={(e) => setWebsite(e.target.value)}
                  placeholder="https://acme.com"
                  className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Purchased Service</label>
                <select
                  value={serviceId}
                  onChange={(e) => setServiceId(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 p-2.5 text-xs font-semibold outline-none"
                >
                  <option value="">-- Select Service --</option>
                  {services.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Notes</label>
                <textarea
                  rows={2}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Contract terms, deliverables, or retainer notes..."
                  className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionBusy || !name.trim()}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-700 shadow-sm"
                >
                  {actionBusy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />}
                  Save Client
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
