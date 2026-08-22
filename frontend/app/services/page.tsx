"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import {
  createService,
  deleteService,
  getServices,
  toggleServiceActive,
  updateService,
} from "@/lib/api";
import { Service, ServiceCreate, ServiceUpdate } from "@/types";
import {
  Layers,
  Plus,
  Edit2,
  Trash2,
  Power,
  ExternalLink,
  Target,
  DollarSign,
  FileText,
  CheckCircle2,
  XCircle,
  Sparkles,
  Loader2,
  AlertCircle,
} from "lucide-react";

export default function ServicesPage() {
  const { token } = useAuth();
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter
  const [filterActiveOnly, setFilterActiveOnly] = useState(false);

  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingService, setEditingService] = useState<Service | null>(null);
  const [deletingServiceId, setDeletingServiceId] = useState<string | null>(null);

  // Form states
  const [formData, setFormData] = useState<ServiceCreate>({
    name: "",
    description: "",
    pricing: "",
    target_clients: "",
    portfolio_links: "",
    is_active: true,
  });
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const loadServices = async () => {
    if (!token) return;
    try {
      setLoading(true);
      setError(null);
      const data = await getServices(token, filterActiveOnly);
      setServices(data);
    } catch (err: any) {
      setError(err.message || "Failed to load services");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadServices();
  }, [token, filterActiveOnly]);

  const handleOpenAddModal = () => {
    setFormData({
      name: "",
      description: "",
      pricing: "",
      target_clients: "",
      portfolio_links: "",
      is_active: true,
    });
    setFormError(null);
    setShowAddModal(true);
  };

  const handleOpenEditModal = (service: Service) => {
    setEditingService(service);
    setFormData({
      name: service.name,
      description: service.description || "",
      pricing: service.pricing || "",
      target_clients: service.target_clients || "",
      portfolio_links: service.portfolio_links || "",
      is_active: service.is_active,
    });
    setFormError(null);
  };

  const handleSaveService = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !formData.name.trim()) return;

    setFormSubmitting(true);
    setFormError(null);

    try {
      if (editingService) {
        const updated = await updateService(token, editingService.id, formData);
        setServices((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
        setEditingService(null);
      } else {
        const created = await createService(token, formData);
        setServices((prev) => [created, ...prev]);
        setShowAddModal(false);
      }
    } catch (err: any) {
      setFormError(err.message || "Failed to save service");
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleToggleActive = async (service: Service) => {
    if (!token) return;
    try {
      const updated = await toggleServiceActive(token, service.id);
      setServices((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
    } catch (err: any) {
      alert("Failed to toggle service status: " + err.message);
    }
  };

  const handleDelete = async (id: string) => {
    if (!token) return;
    try {
      await deleteService(token, id);
      setServices((prev) => prev.filter((s) => s.id !== id));
      setDeletingServiceId(null);
    } catch (err: any) {
      alert("Failed to delete service: " + err.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Services Catalog</h1>
            <span className="rounded-full bg-sky-50 px-2.5 py-0.5 text-xs font-bold text-sky-700">
              {services.length} Total
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Configure the core agency and freelance offerings used to match and qualify incoming leads.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setFilterActiveOnly(!filterActiveOnly)}
            className={`inline-flex items-center gap-1.5 rounded-xl px-3.5 py-2 text-xs font-semibold border transition ${
              filterActiveOnly
                ? "border-sky-500 bg-sky-50 text-sky-700"
                : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
            }`}
          >
            <Power className="h-3.5 w-3.5" />
            {filterActiveOnly ? "Active Only" : "Show All"}
          </button>

          <button
            onClick={handleOpenAddModal}
            className="inline-flex items-center gap-2 rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-white shadow-sm shadow-sky-600/20 hover:bg-sky-500 active:scale-95 transition"
          >
            <Plus className="h-4 w-4" />
            New Service
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading state */}
      {loading ? (
        <div className="flex min-h-[300px] items-center justify-center rounded-2xl border border-slate-200 bg-white">
          <div className="text-center text-slate-400">
            <Loader2 className="mx-auto h-8 w-8 animate-spin text-sky-500" />
            <p className="mt-2 text-sm font-medium">Loading your services catalog...</p>
          </div>
        </div>
      ) : services.length === 0 ? (
        /* Empty State */
        <div className="flex min-h-[360px] flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-white p-8 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-sky-50 text-sky-600 shadow-inner">
            <Layers className="h-7 w-7" />
          </div>
          <h3 className="mt-4 text-lg font-bold text-slate-800">No Services Found</h3>
          <p className="mt-1.5 max-w-md text-sm text-slate-500">
            {filterActiveOnly
              ? "You don't have any active services. Switch filter or activate an existing service."
              : "Define the services you provide (e.g. Website Design, Graphics Design) to enable lead matching."}
          </p>
          <button
            onClick={handleOpenAddModal}
            className="mt-5 inline-flex items-center gap-2 rounded-xl bg-sky-600 px-4 py-2.5 text-sm font-semibold text-white shadow-md hover:bg-sky-500 active:scale-95 transition"
          >
            <Plus className="h-4 w-4" />
            Add Your First Service
          </button>
        </div>
      ) : (
        /* Service Cards Grid */
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {services.map((service) => (
            <div
              key={service.id}
              className={`group relative flex flex-col justify-between rounded-2xl border bg-white p-6 shadow-sm transition-all duration-200 hover:shadow-md ${
                service.is_active ? "border-slate-200 hover:border-sky-300" : "border-slate-200/60 bg-slate-50/50 opacity-75"
              }`}
            >
              {/* Header */}
              <div>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    <div
                      className={`flex h-9 w-9 items-center justify-center rounded-xl ${
                        service.is_active ? "bg-sky-50 text-sky-600" : "bg-slate-100 text-slate-400"
                      }`}
                    >
                      <Layers className="h-5 w-5" />
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-900 line-clamp-1">{service.name}</h3>
                      <span
                        className={`inline-flex items-center gap-1 text-[11px] font-semibold ${
                          service.is_active ? "text-emerald-600" : "text-slate-400"
                        }`}
                      >
                        {service.is_active ? (
                          <>
                            <CheckCircle2 className="h-3 w-3" /> Active
                          </>
                        ) : (
                          <>
                            <XCircle className="h-3 w-3" /> Inactive
                          </>
                        )}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleOpenEditModal(service)}
                      className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition"
                      title="Edit Service"
                    >
                      <Edit2 className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => setDeletingServiceId(service.id)}
                      className="rounded-lg p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600 transition"
                      title="Delete Service"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {/* Description */}
                <p className="mt-3.5 text-xs leading-relaxed text-slate-600 min-h-[36px]">
                  {service.description || <span className="italic text-slate-400">No description provided.</span>}
                </p>

                {/* Badges / Details */}
                <div className="mt-4 space-y-2 border-t border-slate-100 pt-3">
                  {service.pricing && (
                    <div className="flex items-center gap-2 text-xs text-slate-700">
                      <DollarSign className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                      <span className="font-medium">{service.pricing}</span>
                    </div>
                  )}

                  {service.target_clients && (
                    <div className="flex items-start gap-2 text-xs text-slate-600">
                      <Target className="h-3.5 w-3.5 text-indigo-500 shrink-0 mt-0.5" />
                      <span className="line-clamp-2">{service.target_clients}</span>
                    </div>
                  )}

                  {service.portfolio_links && (
                    <div className="flex items-start gap-2 text-xs text-sky-600">
                      <ExternalLink className="h-3.5 w-3.5 shrink-0 mt-0.5" />
                      <span className="truncate">{service.portfolio_links}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Footer Actions */}
              <div className="mt-5 flex items-center justify-between border-t border-slate-100 pt-3 text-xs">
                <span className="text-[11px] text-slate-400">
                  Updated {new Date(service.updated_at).toLocaleDateString()}
                </span>
                <button
                  onClick={() => handleToggleActive(service)}
                  className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold transition ${
                    service.is_active
                      ? "text-slate-600 hover:bg-slate-100"
                      : "text-emerald-700 bg-emerald-50 hover:bg-emerald-100"
                  }`}
                >
                  <Power className="h-3 w-3" />
                  {service.is_active ? "Deactivate" : "Activate"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add / Edit Modal */}
      {(showAddModal || editingService) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h3 className="text-lg font-bold text-slate-900">
                  {editingService ? "Edit Service" : "Create New Service"}
                </h3>
                <p className="text-xs text-slate-500">
                  {editingService
                    ? "Update your service specifications and target audience."
                    : "Add a service offering to match with new prospect inquiries."}
                </p>
              </div>
              <button
                onClick={() => {
                  setShowAddModal(false);
                  setEditingService(null);
                }}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
              >
                ✕
              </button>
            </div>

            {formError && (
              <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-700 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleSaveService} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Service Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Website Design & Landing Pages"
                  className="mt-1.5 w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Description
                </label>
                <textarea
                  rows={3}
                  value={formData.description || ""}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe the deliverables, process, and value proposition..."
                  className="mt-1.5 w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 resize-none"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
                    Pricing Info
                  </label>
                  <input
                    type="text"
                    value={formData.pricing || ""}
                    onChange={(e) => setFormData({ ...formData, pricing: e.target.value })}
                    placeholder="e.g. $1,500 - $3,000 / project"
                    className="mt-1.5 w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
                    Active Status
                  </label>
                  <select
                    value={formData.is_active ? "true" : "false"}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.value === "true" })}
                    className="mt-1.5 w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 bg-white"
                  >
                    <option value="true">Active (Visible for matching)</option>
                    <option value="false">Inactive (Hidden from matching)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Target Client Profile
                </label>
                <input
                  type="text"
                  value={formData.target_clients || ""}
                  onChange={(e) => setFormData({ ...formData, target_clients: e.target.value })}
                  placeholder="e.g. E-commerce founders, B2B SaaS, local clinics"
                  className="mt-1.5 w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Portfolio / Case Study Links
                </label>
                <input
                  type="text"
                  value={formData.portfolio_links || ""}
                  onChange={(e) => setFormData({ ...formData, portfolio_links: e.target.value })}
                  placeholder="e.g. https://behance.net/portfolio, https://github.com/demo"
                  className="mt-1.5 w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                />
              </div>

              <div className="mt-6 flex justify-end gap-3 border-t border-slate-100 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddModal(false);
                    setEditingService(null);
                  }}
                  className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={formSubmitting}
                  className="inline-flex items-center gap-2 rounded-xl bg-sky-600 px-5 py-2.5 text-sm font-semibold text-white shadow-md hover:bg-sky-500 disabled:opacity-50 transition"
                >
                  {formSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
                  {editingService ? "Save Changes" : "Create Service"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingServiceId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-slate-900">Delete Service?</h3>
            <p className="mt-2 text-xs leading-relaxed text-slate-500">
              Are you sure you want to delete this service? Any leads currently matched with it will retain their data, but the service link will be cleared.
            </p>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setDeletingServiceId(null)}
                className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(deletingServiceId)}
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
