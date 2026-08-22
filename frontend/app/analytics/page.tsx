"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { getCRMAnalytics } from "@/lib/api";
import { CRMAnalyticsData } from "@/types";
import {
  BarChart2,
  TrendingUp,
  RefreshCw,
  Sparkles,
  Layers,
  Share2,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ArrowRight,
  Flame,
  UserCheck,
  Check,
} from "lucide-react";

export default function AnalyticsPage() {
  const { token } = useAuth();
  const [data, setData] = useState<CRMAnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadData = async () => {
    if (!token) return;
    try {
      setLoading(true);
      setErrorMsg(null);
      const res = await getCRMAnalytics(token);
      setData(res);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load analytics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token]);

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <BarChart2 className="h-7 w-7 text-indigo-600" />
            CRM Business Analytics & Conversion Funnel
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Real-time business performance, conversion rates, and revenue channel breakdown powered directly by PostgreSQL.
          </p>
        </div>

        <button
          onClick={loadData}
          className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-sm self-start sm:self-auto"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh Analytics
        </button>
      </div>

      {errorMsg && (
        <div className="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs font-semibold text-rose-800 animate-in fade-in">
          <AlertCircle className="h-4 w-4 text-rose-600 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {loading ? (
        <div className="py-24 text-center text-xs text-slate-400">
          <Loader2 className="h-7 w-7 animate-spin mx-auto mb-2 text-indigo-500" />
          Aggregating PostgreSQL metrics...
        </div>
      ) : data ? (
        <div className="space-y-6">
          {/* Key Metrics Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
              <span className="text-[11px] font-bold text-slate-400 block">Total Leads</span>
              <span className="text-2xl font-bold text-slate-900 mt-1 block">{data.total_leads}</span>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
              <span className="text-[11px] font-bold text-slate-400 block">New Leads</span>
              <span className="text-2xl font-bold text-slate-700 mt-1 block">{data.new_leads}</span>
            </div>
            <div className="rounded-2xl border border-indigo-100 bg-indigo-50/40 p-4 shadow-xs">
              <span className="text-[11px] font-bold text-indigo-600 block">Qualified</span>
              <span className="text-2xl font-bold text-indigo-950 mt-1 block">{data.qualified_leads}</span>
            </div>
            <div className="rounded-2xl border border-amber-100 bg-amber-50/40 p-4 shadow-xs">
              <span className="text-[11px] font-bold text-amber-700 block flex items-center gap-1">
                <Flame className="h-3 w-3 text-amber-600" /> Hot Leads
              </span>
              <span className="text-2xl font-bold text-amber-950 mt-1 block">{data.hot_leads}</span>
            </div>
            <div className="rounded-2xl border border-sky-100 bg-sky-50/40 p-4 shadow-xs">
              <span className="text-[11px] font-bold text-sky-600 block">Contacted</span>
              <span className="text-2xl font-bold text-sky-950 mt-1 block">{data.contacted_leads}</span>
            </div>
            <div className="rounded-2xl border border-teal-100 bg-teal-50/40 p-4 shadow-xs">
              <span className="text-[11px] font-bold text-teal-700 block">Replied</span>
              <span className="text-2xl font-bold text-teal-950 mt-1 block">{data.replied_leads}</span>
            </div>
            <div className="rounded-2xl border border-emerald-200 bg-emerald-100/60 p-4 shadow-xs">
              <span className="text-[11px] font-bold text-emerald-800 block">Won Deals 🎉</span>
              <span className="text-2xl font-bold text-emerald-950 mt-1 block">{data.won_leads}</span>
            </div>
            <div className="rounded-2xl border border-rose-100 bg-rose-50/40 p-4 shadow-xs">
              <span className="text-[11px] font-bold text-rose-600 block">Lost Deals</span>
              <span className="text-2xl font-bold text-rose-950 mt-1 block">{data.lost_leads}</span>
            </div>
          </div>

          {/* Conversion Funnel */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-indigo-600" />
                  Lead-to-Client Conversion Funnel
                </h3>
                <p className="text-xs text-slate-500">Step-by-step conversion efficiency (safe zero-division calculation)</p>
              </div>
              <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700 border border-emerald-200">
                Overall Lead → Won: {data.conversion_funnel.overall_lead_to_won_pct}%
              </span>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-xl border border-slate-100 bg-slate-50 p-4 space-y-1">
                <span className="text-xs text-slate-400 font-semibold">Lead → Qualified</span>
                <div className="text-2xl font-bold text-indigo-600">
                  {data.conversion_funnel.lead_to_qualified_pct}%
                </div>
                <span className="text-[11px] text-slate-500">({data.qualified_leads} of {data.total_leads})</span>
              </div>

              <div className="rounded-xl border border-slate-100 bg-slate-50 p-4 space-y-1">
                <span className="text-xs text-slate-400 font-semibold">Qualified → Contacted</span>
                <div className="text-2xl font-bold text-sky-600">
                  {data.conversion_funnel.qualified_to_contacted_pct}%
                </div>
                <span className="text-[11px] text-slate-500">({data.contacted_leads} of {data.qualified_leads})</span>
              </div>

              <div className="rounded-xl border border-slate-100 bg-slate-50 p-4 space-y-1">
                <span className="text-xs text-slate-400 font-semibold">Contacted → Replied</span>
                <div className="text-2xl font-bold text-teal-600">
                  {data.conversion_funnel.contacted_to_replied_pct}%
                </div>
                <span className="text-[11px] text-slate-500">({data.replied_leads} of {data.contacted_leads})</span>
              </div>

              <div className="rounded-xl border border-slate-100 bg-slate-50 p-4 space-y-1">
                <span className="text-xs text-slate-400 font-semibold">Replied → Won</span>
                <div className="text-2xl font-bold text-emerald-600">
                  {data.conversion_funnel.replied_to_won_pct}%
                </div>
                <span className="text-[11px] text-slate-500">({data.won_leads} of {data.replied_leads})</span>
              </div>
            </div>
          </div>

          {/* 2-Column Section: Service Performance & Source Breakdown */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Service ROI Breakdown */}
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2 border-b border-slate-100 pb-3">
                <Layers className="h-4 w-4 text-indigo-600" />
                Service ROI & Performance Breakdown
              </h3>

              {data.service_performance.length === 0 ? (
                <div className="text-center py-10 text-xs text-slate-400">
                  No service breakdown available yet.
                </div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {data.service_performance.map((svc) => (
                    <div key={svc.service_name} className="py-3 flex items-center justify-between">
                      <div>
                        <h4 className="font-bold text-xs text-slate-900">{svc.service_name}</h4>
                        <div className="flex items-center gap-3 text-[11px] text-slate-500 mt-0.5">
                          <span>{svc.total_leads} leads</span>
                          <span>• {svc.qualified_leads} qualified</span>
                          <span>• {svc.won_deals} deals won</span>
                        </div>
                      </div>

                      <span className="rounded-lg bg-emerald-50 px-2.5 py-1 text-xs font-bold text-emerald-800 border border-emerald-100">
                        {svc.clients_count} Active Clients
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Source Acquisition Performance */}
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2 border-b border-slate-100 pb-3">
                <Share2 className="h-4 w-4 text-indigo-600" />
                Lead Acquisition Source Performance
              </h3>

              {data.source_performance.length === 0 ? (
                <div className="text-center py-10 text-xs text-slate-400">
                  No source data available yet.
                </div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {data.source_performance.map((src) => (
                    <div key={src.source_name} className="py-3 flex items-center justify-between">
                      <div>
                        <h4 className="font-bold text-xs text-slate-900 capitalize">{src.source_name}</h4>
                        <div className="flex items-center gap-3 text-[11px] text-slate-500 mt-0.5">
                          <span>{src.total_leads} leads</span>
                          <span>• {src.qualified_leads} qualified</span>
                        </div>
                      </div>

                      <span className="rounded-lg bg-indigo-50 px-2.5 py-1 text-xs font-bold text-indigo-800 border border-indigo-100">
                        {src.clients_count} Clients Generated
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
