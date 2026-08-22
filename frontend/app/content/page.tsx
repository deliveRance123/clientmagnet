"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import {
  cancelScheduledPost,
  createContent,
  deleteContent,
  generateAICaption,
  getContentList,
  getPlatformCapabilities,
  getScheduledPosts,
  getSocialAccounts,
  publishNowSocialPost,
  scheduleSocialPost,
  updateContent,
} from "@/lib/api";
import {
  AICaptionGenerateResult,
  ContentItem,
  PlatformCapabilityInfo,
  ScheduledPostItem,
  SocialAccountConnection,
} from "@/types";
import {
  Sparkles,
  Share2,
  Calendar as CalendarIcon,
  Copy,
  Check,
  Loader2,
  Send,
  Plus,
  Trash2,
  Edit3,
  Clock,
  CheckCircle2,
  AlertCircle,
  XCircle,
  Eye,
  Layers,
  BarChart2,
  Info,
} from "lucide-react";

export default function ContentPage() {
  const { token } = useAuth();

  // State
  const [activeTab, setActiveTab] = useState<"studio" | "calendar" | "drafts" | "published">("studio");
  const [drafts, setDrafts] = useState<ContentItem[]>([]);
  const [scheduledPosts, setScheduledPosts] = useState<ScheduledPostItem[]>([]);
  const [socialAccounts, setSocialAccounts] = useState<SocialAccountConnection[]>([]);
  const [capabilities, setCapabilities] = useState<PlatformCapabilityInfo[]>([]);

  const [loading, setLoading] = useState(true);
  const [actionBusy, setActionBusy] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Content Form State
  const [editingContentId, setEditingContentId] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [hashtags, setHashtags] = useState("");
  const [cta, setCta] = useState("");
  const [mediaUrl, setMediaUrl] = useState("");
  const [targetPlatforms, setTargetPlatforms] = useState<string[]>(["LINKEDIN", "X", "FACEBOOK", "INSTAGRAM"]);
  const [previewPlatform, setPreviewPlatform] = useState<string>("LINKEDIN");

  // AI Caption Drawer State
  const [aiTopic, setAiTopic] = useState("");
  const [aiDescription, setAiDescription] = useState("");
  const [aiTone, setAiTone] = useState("Professional & Engaging");
  const [generatingCaption, setGeneratingCaption] = useState(false);
  const [copied, setCopied] = useState(false);

  // Schedule Modal
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [selectedContentForSchedule, setSelectedContentForSchedule] = useState<ContentItem | null>(null);
  const [scheduleDateTime, setScheduleDateTime] = useState("");
  const [selectedSchedulePlatforms, setSelectedSchedulePlatforms] = useState<string[]>(["LINKEDIN"]);

  // Load Data
  const loadData = async () => {
    if (!token) return;
    try {
      setLoading(true);
      setErrorMsg(null);

      const [draftsData, scheduleData, accountsData, capsData] = await Promise.all([
        getContentList(token).catch(() => []),
        getScheduledPosts(token).catch(() => []),
        getSocialAccounts(token).catch(() => []),
        getPlatformCapabilities(token).catch(() => ({ capabilities: [] })),
      ]);

      setDrafts(draftsData);
      setScheduledPosts(scheduleData);
      setSocialAccounts(accountsData);
      setCapabilities(capsData.capabilities || []);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load content data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token]);

  // AI Caption Generation
  const handleGenerateCaption = async () => {
    if (!token || !aiTopic.trim()) {
      alert("Please enter a topic for the AI post.");
      return;
    }
    try {
      setGeneratingCaption(true);
      setErrorMsg(null);
      const res: AICaptionGenerateResult = await generateAICaption(token, {
        topic: aiTopic,
        description: aiDescription || undefined,
        platform: previewPlatform,
        tone: aiTone,
      });

      setBody(res.caption);
      setHashtags(res.hashtags.map((h) => (h.startsWith("#") ? h : `#${h}`)).join(" "));
      setCta(res.call_to_action);
      if (!title) setTitle(aiTopic.slice(0, 40));
      setSuccessMsg("AI caption generated with Gemini! Review and tailor before publishing.");
    } catch (err: any) {
      setErrorMsg(err.message || "Caption generation failed.");
    } finally {
      setGeneratingCaption(false);
    }
  };

  // Save / Update Content Draft
  const handleSaveDraft = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    if (!title.trim() || !body.trim()) {
      alert("Title and Body are required.");
      return;
    }

    try {
      setActionBusy(true);
      setErrorMsg(null);

      if (editingContentId) {
        await updateContent(token, editingContentId, {
          title: title.trim(),
          body: body.trim(),
          hashtags: hashtags.trim() || undefined,
          call_to_action: cta.trim() || undefined,
          media_reference: mediaUrl.trim() || undefined,
          target_platforms: targetPlatforms,
        });
        setSuccessMsg("Content draft updated successfully.");
      } else {
        await createContent(token, {
          title: title.trim(),
          body: body.trim(),
          hashtags: hashtags.trim() || undefined,
          call_to_action: cta.trim() || undefined,
          media_reference: mediaUrl.trim() || undefined,
          target_platforms: targetPlatforms,
          status: "Draft",
        });
        setSuccessMsg("Content draft saved successfully.");
      }

      // Reset form
      setEditingContentId(null);
      setTitle("");
      setBody("");
      setHashtags("");
      setCta("");
      setMediaUrl("");
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to save content draft.");
    } finally {
      setActionBusy(false);
    }
  };

  // Load Draft into Form for Editing
  const handleEditDraft = (item: ContentItem) => {
    setEditingContentId(item.id);
    setTitle(item.title);
    setBody(item.body);
    setHashtags(item.hashtags || "");
    setCta(item.call_to_action || "");
    setMediaUrl(item.media_reference || "");
    setTargetPlatforms(item.target_platforms || ["LINKEDIN"]);
    setActiveTab("studio");
  };

  // Delete Draft
  const handleDeleteDraft = async (id: string) => {
    if (!token) return;
    if (!confirm("Are you sure you want to delete this content item?")) return;
    try {
      await deleteContent(token, id);
      setSuccessMsg("Content deleted.");
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to delete content.");
    }
  };

  // Instant Publishing
  const handlePublishNow = async (contentItem: ContentItem) => {
    if (!token) return;
    const platforms = contentItem.target_platforms.length > 0 ? contentItem.target_platforms : ["LINKEDIN"];
    if (!confirm(`Publish "${contentItem.title}" immediately to ${platforms.join(", ")}?`)) return;

    try {
      setActionBusy(true);
      setErrorMsg(null);
      const results = await publishNowSocialPost(token, contentItem.id, platforms);
      const anySuccess = results.some((r) => r.status === "PUBLISHED");
      if (anySuccess) {
        setSuccessMsg("Content successfully published!");
      } else {
        setErrorMsg(results.map((r) => `${r.platform}: ${r.message}`).join(" | "));
      }
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || "Publishing failed.");
    } finally {
      setActionBusy(false);
    }
  };

  // Schedule Post Action
  const handleScheduleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !selectedContentForSchedule || !scheduleDateTime) return;

    try {
      setActionBusy(true);
      setErrorMsg(null);
      await scheduleSocialPost(
        token,
        selectedContentForSchedule.id,
        selectedSchedulePlatforms,
        new Date(scheduleDateTime).toISOString()
      );
      setSuccessMsg("Post scheduled successfully in PostgreSQL queue!");
      setShowScheduleModal(false);
      setSelectedContentForSchedule(null);
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || "Scheduling failed.");
    } finally {
      setActionBusy(false);
    }
  };

  // Cancel Scheduled Post
  const handleCancelPost = async (postId: string) => {
    if (!token) return;
    if (!confirm("Cancel this scheduled post?")) return;
    try {
      await cancelScheduledPost(token, postId);
      setSuccessMsg("Scheduled post cancelled.");
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to cancel post.");
    }
  };

  // Platform Capability Helpers
  const currentCap = capabilities.find((c) => c.platform === previewPlatform);
  const fullPostText = `${body}\n\n${cta}\n\n${hashtags}`.trim();
  const charLimit = currentCap ? currentCap.max_text_length : 3000;
  const isOverLimit = fullPostText.length > charLimit;

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Share2 className="h-7 w-7 text-indigo-600" />
            Social Content Studio & Multi-Platform Calendar
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Create, optimize with Gemini AI, and schedule compliant social posts across connected accounts.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-1 rounded-xl bg-slate-100 p-1">
          <button
            onClick={() => setActiveTab("studio")}
            className={`rounded-lg px-3.5 py-1.5 text-xs font-bold transition ${
              activeTab === "studio" ? "bg-white text-indigo-700 shadow-xs" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Content Studio
          </button>
          <button
            onClick={() => setActiveTab("calendar")}
            className={`rounded-lg px-3.5 py-1.5 text-xs font-bold transition ${
              activeTab === "calendar" ? "bg-white text-indigo-700 shadow-xs" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Calendar ({scheduledPosts.filter((p) => p.status === "Scheduled").length})
          </button>
          <button
            onClick={() => setActiveTab("drafts")}
            className={`rounded-lg px-3.5 py-1.5 text-xs font-bold transition ${
              activeTab === "drafts" ? "bg-white text-indigo-700 shadow-xs" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Drafts ({drafts.length})
          </button>
          <button
            onClick={() => setActiveTab("published")}
            className={`rounded-lg px-3.5 py-1.5 text-xs font-bold transition ${
              activeTab === "published" ? "bg-white text-indigo-700 shadow-xs" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            History
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

      {/* Tab 1: Content Studio */}
      {activeTab === "studio" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left 7 Columns: Creator & Gemini Drafter */}
          <div className="lg:col-span-7 space-y-5">
            {/* Gemini AI Drafter Drawer */}
            <div className="rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50/50 to-white p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-indigo-100/60 pb-3">
                <div className="flex items-center gap-2">
                  <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600 text-white">
                    <Sparkles className="h-4 w-4" />
                  </span>
                  <div>
                    <h3 className="font-bold text-slate-900 text-xs">Gemini AI Social Drafter</h3>
                    <p className="text-[10px] text-slate-500">Auto-generates punchy captions, tailored hashtags & CTAs</p>
                  </div>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                <div className="sm:col-span-2">
                  <label className="text-[11px] font-bold text-slate-600 block mb-1">Post Topic / Hook</label>
                  <input
                    type="text"
                    value={aiTopic}
                    onChange={(e) => setAiTopic(e.target.value)}
                    placeholder="e.g. 3 reasons every business needs workflow automation in 2026"
                    className="w-full rounded-xl border border-slate-200 bg-white p-2.5 text-xs outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="text-[11px] font-bold text-slate-600 block mb-1">Tone</label>
                  <select
                    value={aiTone}
                    onChange={(e) => setAiTone(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-white p-2.5 text-xs font-semibold outline-none"
                  >
                    <option value="Professional & Engaging">Professional</option>
                    <option value="Direct, Bold & ROI-Focused">Bold & Direct</option>
                    <option value="Casual & Relatable">Casual</option>
                    <option value="Educational & Step-by-Step">Educational</option>
                  </select>
                </div>
              </div>

              <button
                type="button"
                onClick={handleGenerateCaption}
                disabled={generatingCaption || !aiTopic.trim()}
                className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50 transition"
              >
                {generatingCaption ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin" /> Drafting with Gemini...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-3.5 w-3.5" /> Generate Multi-Platform Caption Draft
                  </>
                )}
              </button>
            </div>

            {/* Post Content Form */}
            <form onSubmit={handleSaveDraft} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="font-bold text-slate-900 text-xs">
                  {editingContentId ? "Edit Content Draft" : "Compose Post Content"}
                </h3>
                {editingContentId && (
                  <button
                    type="button"
                    onClick={() => {
                      setEditingContentId(null);
                      setTitle("");
                      setBody("");
                    }}
                    className="text-[11px] font-semibold text-slate-500 hover:text-slate-800"
                  >
                    Cancel Editing
                  </button>
                )}
              </div>

              <div>
                <label className="text-[11px] font-bold text-slate-600 block mb-1">Internal Title / Label *</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Website Redesign Launch Announcement"
                  className="w-full rounded-xl border border-slate-200 p-2.5 text-xs font-semibold outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-[11px] font-bold text-slate-600 block mb-1">Post Body Copy *</label>
                <textarea
                  rows={5}
                  required
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  placeholder="Write or edit your post caption here..."
                  className="w-full rounded-xl border border-slate-200 p-3 text-xs leading-relaxed outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="text-[11px] font-bold text-slate-600 block mb-1">Hashtags</label>
                  <input
                    type="text"
                    value={hashtags}
                    onChange={(e) => setHashtags(e.target.value)}
                    placeholder="#WebDesign #FastAPI #NextJS"
                    className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="text-[11px] font-bold text-slate-600 block mb-1">Call-To-Action (CTA)</label>
                  <input
                    type="text"
                    value={cta}
                    onChange={(e) => setCta(e.target.value)}
                    placeholder="e.g. Book your free consultation today"
                    className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-bold text-slate-600 block mb-1">Media Reference URL (Image/Video)</label>
                <input
                  type="url"
                  value={mediaUrl}
                  onChange={(e) => setMediaUrl(e.target.value)}
                  placeholder="https://example.com/portfolio-screenshot.jpg"
                  className="w-full rounded-xl border border-slate-200 p-2.5 text-xs outline-none focus:border-indigo-500"
                />
              </div>

              {/* Target Platform Checkboxes */}
              <div>
                <label className="text-[11px] font-bold text-slate-600 block mb-1.5">Target Platforms</label>
                <div className="flex flex-wrap gap-2">
                  {["LINKEDIN", "X", "FACEBOOK", "INSTAGRAM", "TIKTOK"].map((p) => {
                    const isChecked = targetPlatforms.includes(p);
                    return (
                      <button
                        key={p}
                        type="button"
                        onClick={() => {
                          setTargetPlatforms((prev) =>
                            prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]
                          );
                        }}
                        className={`rounded-lg px-3 py-1.5 text-xs font-bold border transition ${
                          isChecked
                            ? "bg-indigo-600 text-white border-indigo-600 shadow-xs"
                            : "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100"
                        }`}
                      >
                        {p}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="submit"
                  disabled={actionBusy}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-slate-900 px-4 py-2 text-xs font-bold text-white hover:bg-slate-800 shadow-sm"
                >
                  <Check className="h-4 w-4" />
                  {editingContentId ? "Update Draft" : "Save Content Draft"}
                </button>
              </div>
            </form>
          </div>

          {/* Right 5 Columns: Live Multi-Platform Preview Card */}
          <div className="lg:col-span-5 space-y-4">
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4 sticky top-6">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <Eye className="h-4 w-4 text-indigo-600" />
                  <h3 className="font-bold text-slate-900 text-xs">Live Platform Preview</h3>
                </div>

                {/* Platform Selector for Preview */}
                <select
                  value={previewPlatform}
                  onChange={(e) => setPreviewPlatform(e.target.value)}
                  className="rounded-lg border border-slate-200 bg-white py-1 px-2 text-xs font-semibold outline-none"
                >
                  <option value="LINKEDIN">LinkedIn</option>
                  <option value="X">X (Twitter)</option>
                  <option value="FACEBOOK">Facebook</option>
                  <option value="INSTAGRAM">Instagram</option>
                  <option value="TIKTOK">TikTok</option>
                </select>
              </div>

              {/* Character Limit Counter */}
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-slate-400">Length Constraint:</span>
                <span className={`font-bold ${isOverLimit ? "text-rose-600" : "text-slate-600"}`}>
                  {fullPostText.length} / {charLimit} chars
                </span>
              </div>

              {/* Capability Warning if Any */}
              {currentCap && previewPlatform === "TIKTOK" && !mediaUrl && (
                <div className="rounded-lg bg-amber-50 p-2.5 border border-amber-200 text-[11px] text-amber-800 flex items-center gap-1.5">
                  <Info className="h-3.5 w-3.5 flex-shrink-0 text-amber-600" />
                  <span>TikTok requires a video URL; text-only posting is unsupported by official API.</span>
                </div>
              )}
              {currentCap && previewPlatform === "INSTAGRAM" && !mediaUrl && (
                <div className="rounded-lg bg-amber-50 p-2.5 border border-amber-200 text-[11px] text-amber-800 flex items-center gap-1.5">
                  <Info className="h-3.5 w-3.5 flex-shrink-0 text-amber-600" />
                  <span>Instagram requires an image or video URL.</span>
                </div>
              )}

              {/* Mock Social Card Preview */}
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-3 shadow-xs">
                <div className="flex items-center gap-2.5">
                  <div className="h-8 w-8 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-xs">
                    CM
                  </div>
                  <div>
                    <h4 className="font-bold text-xs text-slate-900">Client Magnet Brand</h4>
                    <span className="text-[10px] text-slate-400">Preview on {previewPlatform}</span>
                  </div>
                </div>

                <div className="text-xs text-slate-800 leading-relaxed whitespace-pre-wrap">
                  {body || "Your post copy will render here as you type..."}
                </div>

                {cta && (
                  <div className="rounded-lg bg-white p-2 text-xs font-semibold text-indigo-700 border border-slate-200">
                    👉 {cta}
                  </div>
                )}

                {hashtags && (
                  <p className="text-xs font-semibold text-sky-600 break-words">
                    {hashtags}
                  </p>
                )}

                {mediaUrl && (
                  <div className="rounded-lg border border-slate-200 bg-white p-2 text-[10px] text-slate-400 truncate">
                    Attached Media: {mediaUrl}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Content Calendar */}
      {activeTab === "calendar" && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <CalendarIcon className="h-4 w-4 text-indigo-600" />
              PostgreSQL Scheduled Execution Queue
            </h3>
          </div>

          {scheduledPosts.length === 0 ? (
            <div className="text-center py-12 text-xs text-slate-400">
              No scheduled posts in the queue. Create a draft and click Schedule Post.
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {scheduledPosts.map((post) => (
                <div key={post.id} className="py-3.5 flex items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="rounded bg-indigo-50 px-2 py-0.5 text-[10px] font-bold text-indigo-700 border border-indigo-100">
                        {post.platform}
                      </span>
                      <h4 className="font-bold text-xs text-slate-900">
                        {post.content_title || "Social Post"}
                      </h4>
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                          post.status === "Scheduled"
                            ? "bg-amber-50 text-amber-700 border border-amber-200"
                            : post.status === "Published"
                            ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                            : "bg-rose-50 text-rose-700 border border-rose-200"
                        }`}
                      >
                        {post.status}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-[11px] text-slate-400">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        Scheduled for: <strong>{new Date(post.scheduled_at).toLocaleString()}</strong>
                      </span>
                      {post.external_post_id && (
                        <span>External ID: {post.external_post_id}</span>
                      )}
                    </div>
                  </div>

                  {post.status === "Scheduled" && (
                    <button
                      onClick={() => handleCancelPost(post.id)}
                      className="rounded-lg border border-slate-200 px-3 py-1 text-xs font-semibold text-rose-600 hover:bg-rose-50"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Drafts */}
      {activeTab === "drafts" && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="font-bold text-slate-900 text-sm">Saved Content Drafts</h3>
            <button
              onClick={() => {
                setEditingContentId(null);
                setTitle("");
                setBody("");
                setActiveTab("studio");
              }}
              className="inline-flex items-center gap-1 rounded-xl bg-indigo-600 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-indigo-700"
            >
              <Plus className="h-3.5 w-3.5" />
              New Draft
            </button>
          </div>

          {drafts.length === 0 ? (
            <div className="text-center py-12 text-xs text-slate-400">
              No saved drafts found. Create your first draft in the Content Studio.
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {drafts.map((d) => (
                <div key={d.id} className="rounded-xl border border-slate-200 p-4 space-y-3 bg-slate-50/40 flex flex-col justify-between">
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <h4 className="font-bold text-xs text-slate-900 truncate">{d.title}</h4>
                      <span className="rounded bg-slate-200/70 px-2 py-0.5 text-[10px] font-semibold text-slate-700">
                        {d.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed">{d.body}</p>
                    <div className="flex flex-wrap gap-1 pt-1">
                      {d.target_platforms.map((p) => (
                        <span key={p} className="rounded bg-indigo-50 px-1.5 py-0.5 text-[10px] font-bold text-indigo-700">
                          {p}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-200/60">
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => handleEditDraft(d)}
                        className="p-1.5 text-slate-500 hover:text-indigo-600 rounded-lg hover:bg-slate-100"
                        title="Edit Draft"
                      >
                        <Edit3 className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => handleDeleteDraft(d.id)}
                        className="p-1.5 text-slate-500 hover:text-rose-600 rounded-lg hover:bg-slate-100"
                        title="Delete"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => {
                          setSelectedContentForSchedule(d);
                          setSelectedSchedulePlatforms(d.target_platforms.length > 0 ? d.target_platforms : ["LINKEDIN"]);
                          setShowScheduleModal(true);
                        }}
                        className="rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-50"
                      >
                        Schedule
                      </button>
                      <button
                        onClick={() => handlePublishNow(d)}
                        disabled={actionBusy}
                        className="rounded-lg bg-indigo-600 px-2.5 py-1 text-[11px] font-bold text-white hover:bg-indigo-700 shadow-xs"
                      >
                        Publish Now
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Published History */}
      {activeTab === "published" && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
          <h3 className="font-bold text-slate-900 text-sm border-b border-slate-100 pb-3">
            Published Social Posts & Analytics
          </h3>

          {scheduledPosts.filter((p) => p.status === "Published").length === 0 ? (
            <div className="text-center py-12 text-xs text-slate-400">
              No published posts recorded yet.
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {scheduledPosts
                .filter((p) => p.status === "Published")
                .map((post) => (
                  <div key={post.id} className="py-3.5 flex items-center justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="rounded bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-700 border border-emerald-200">
                          {post.platform}
                        </span>
                        <h4 className="font-bold text-xs text-slate-900">{post.content_title || "Post"}</h4>
                      </div>
                      <p className="text-[11px] text-slate-400">
                        Published at: {post.published_at ? new Date(post.published_at).toLocaleString() : "Recently"}
                      </p>
                    </div>

                    <div className="flex items-center gap-3 text-xs font-semibold text-slate-600 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-100">
                      <span>👍 {post.analytics.likes || 0}</span>
                      <span>💬 {post.analytics.comments || 0}</span>
                      <span>🔄 {post.analytics.shares || 0}</span>
                      <span>👁️ {post.analytics.views || 0}</span>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </div>
      )}

      {/* Schedule Post Modal */}
      {showScheduleModal && selectedContentForSchedule && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-xs animate-in fade-in">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl border border-slate-100 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 text-sm">Schedule Post for Publishing</h3>
              <button
                onClick={() => setShowScheduleModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleScheduleSubmit} className="space-y-4">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Post Title</label>
                <input
                  type="text"
                  disabled
                  value={selectedContentForSchedule.title}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-xs text-slate-600"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Scheduled Date & Time *</label>
                <input
                  type="datetime-local"
                  required
                  value={scheduleDateTime}
                  onChange={(e) => setScheduleDateTime(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 p-2.5 text-xs font-semibold outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1.5">Target Platforms</label>
                <div className="flex flex-wrap gap-2">
                  {["LINKEDIN", "X", "FACEBOOK", "INSTAGRAM", "TIKTOK"].map((p) => {
                    const isChecked = selectedSchedulePlatforms.includes(p);
                    return (
                      <button
                        key={p}
                        type="button"
                        onClick={() => {
                          setSelectedSchedulePlatforms((prev) =>
                            prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]
                          );
                        }}
                        className={`rounded-lg px-2.5 py-1 text-xs font-bold border transition ${
                          isChecked
                            ? "bg-indigo-600 text-white border-indigo-600"
                            : "bg-slate-50 text-slate-600 border-slate-200"
                        }`}
                      >
                        {p}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowScheduleModal(false)}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionBusy || !scheduleDateTime}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-700 shadow-sm disabled:opacity-50"
                >
                  {actionBusy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CalendarIcon className="h-3.5 w-3.5" />}
                  Confirm Schedule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
