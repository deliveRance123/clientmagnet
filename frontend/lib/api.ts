import {
  CaptionGenerateRequest,
  CaptionGenerateResponse,
  ConversationSummaryRequest,
  ConversationSummaryResponse,
  CSVImportResult,
  DiscoveryRun,
  DiscoveryRunRequest,
  DiscoverySource,
  DiscoverySourceCreate,
  DiscoverySourceUpdate,
  EmailDraftRequest,
  EmailDraftResponse,
  IntentScoreRequest,
  IntentScoreResponse,
  Lead,
  LeadAnalysisRequest,
  LeadAnalysisResponse,
  LeadCreate,
  LeadStatsSummary,
  LeadUpdate,
  ManualLeadImportRequest,
  ReplySuggestionRequest,
  ReplySuggestionResponse,
  Service,
  ServiceCreate,
  ServiceMatchRequest,
  ServiceMatchResponse,
  ServiceUpdate,
  SocialAccountConnection,
  OAuthInitiateResponse,
  SocialDisconnectResponse,
  EmailAccountConnection,
  EmailConnectResponse,
  EmailConversation,
  EmailDraftGenerateRequest,
  EmailDraftGenerateResponse,
  EmailSendRequest,
  EmailSendResult,
  ContentItem,
  ContentCreateInput,
  AICaptionGenerateRequestInput,
  AICaptionGenerateResult,
  ScheduledPostItem,
  PublishResultItem,
  PlatformCapabilityInfo,
  WhatsAppAccount,
  WhatsAppAccountConnectInput,
  WhatsAppSendRequestInput,
  WhatsAppSendResult,
  UnifiedConversation,
  ConversationSummary,
  SuggestedReply,
  FollowUpItem,
  FollowUpCreateInput,
  FollowUpUpdateInput,
  NotificationSummary,
  UserCommunicationPreferences,
  ClientItem,
  ClientCreateInput,
  LeadConvertToClientInput,
  CRMDashboardMetrics,
  CRMAnalyticsData,
  GlobalSearchResponse,
  ActivityTimelineData,
  UserBusinessProfile,
} from "@/types";

import { getApiBase, resilientFetch } from "./api-config";

async function apiFetch(input: string, init?: RequestInit): Promise<Response> {
  let cleanEndpoint = input;
  if (cleanEndpoint.includes("/api/v1")) {
    cleanEndpoint = cleanEndpoint.substring(cleanEndpoint.indexOf("/api/v1") + 7);
  }
  return await resilientFetch(cleanEndpoint, init);
}

const API_BASE = typeof window !== "undefined" ? getApiBase() : (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1");

function getAuthHeaders(token: string) {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

// Services API
export async function getServices(token: string, activeOnly = false): Promise<Service[]> {
  const url = activeOnly ? `${API_BASE}/services/?active_only=true` : `${API_BASE}/services/`;
  const res = await apiFetch(url, { headers: getAuthHeaders(token) });
  if (!res.ok) throw new Error("Failed to fetch services");
  return res.json();
}

export async function getServiceById(token: string, id: string): Promise<Service> {
  const res = await apiFetch(`${API_BASE}/services/${id}`, { headers: getAuthHeaders(token) });
  if (!res.ok) throw new Error("Failed to fetch service details");
  return res.json();
}

export async function createService(token: string, data: ServiceCreate): Promise<Service> {
  const res = await apiFetch(`${API_BASE}/services/`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to create service");
  }
  return res.json();
}

export async function updateService(token: string, id: string, data: ServiceUpdate): Promise<Service> {
  const res = await apiFetch(`${API_BASE}/services/${id}`, {
    method: "PATCH",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to update service");
  }
  return res.json();
}

export async function toggleServiceActive(token: string, id: string): Promise<Service> {
  const res = await apiFetch(`${API_BASE}/services/${id}/toggle`, {
    method: "PATCH",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error("Failed to toggle service status");
  return res.json();
}

export async function deleteService(token: string, id: string): Promise<void> {
  const res = await apiFetch(`${API_BASE}/services/${id}`, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error("Failed to delete service");
}

// Leads API
export interface LeadQueryParams {
  search?: string;
  status?: string;
  source?: string;
  matched_service_id?: string;
  sort_by?: string;
  sort_dir?: string;
}

export async function getLeads(token: string, params: LeadQueryParams = {}): Promise<Lead[]> {
  const query = new URLSearchParams();
  if (params.search) query.append("search", params.search);
  if (params.status) query.append("status", params.status);
  if (params.source) query.append("source", params.source);
  if (params.matched_service_id) query.append("matched_service_id", params.matched_service_id);
  if (params.sort_by) query.append("sort_by", params.sort_by);
  if (params.sort_dir) query.append("sort_dir", params.sort_dir);

  const url = `${API_BASE}/leads/${query.toString() ? `?${query.toString()}` : ""}`;
  const res = await apiFetch(url, { headers: getAuthHeaders(token) });
  if (!res.ok) throw new Error("Failed to fetch leads");
  return res.json();
}

export async function getLeadById(token: string, id: string): Promise<Lead> {
  const res = await apiFetch(`${API_BASE}/leads/${id}`, { headers: getAuthHeaders(token) });
  if (!res.ok) throw new Error("Failed to fetch lead details");
  return res.json();
}

export async function createLead(token: string, data: LeadCreate): Promise<Lead> {
  const res = await apiFetch(`${API_BASE}/leads/`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to create lead");
  }
  return res.json();
}

export async function updateLead(token: string, id: string, data: LeadUpdate): Promise<Lead> {
  const res = await apiFetch(`${API_BASE}/leads/${id}`, {
    method: "PATCH",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to update lead");
  }
  return res.json();
}

export async function deleteLead(token: string, id: string): Promise<void> {
  const res = await apiFetch(`${API_BASE}/leads/${id}`, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) throw new Error("Failed to delete lead");
}

export async function getLeadStatsSummary(token: string): Promise<LeadStatsSummary> {
  const res = await apiFetch(`${API_BASE}/leads/stats/summary`, { headers: getAuthHeaders(token) });
  if (!res.ok) throw new Error("Failed to fetch lead stats");
  return res.json();
}

// ---------------------------------------------------------------------------
// AI Intelligence APIs
// ---------------------------------------------------------------------------

export async function analyzeLead(
  token: string,
  data: LeadAnalysisRequest
): Promise<LeadAnalysisResponse> {
  const res = await apiFetch(`${API_BASE}/ai/analyze-lead`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to analyze lead");
  }
  return res.json();
}

export async function matchService(
  token: string,
  data: ServiceMatchRequest
): Promise<ServiceMatchResponse> {
  const res = await apiFetch(`${API_BASE}/ai/match-service`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to match service");
  }
  return res.json();
}

export async function scoreIntent(
  token: string,
  data: IntentScoreRequest
): Promise<IntentScoreResponse> {
  const res = await apiFetch(`${API_BASE}/ai/score-intent`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to score lead intent");
  }
  return res.json();
}

export async function generateCaption(
  token: string,
  data: CaptionGenerateRequest
): Promise<CaptionGenerateResponse> {
  const res = await apiFetch(`${API_BASE}/ai/generate-caption`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to generate caption");
  }
  return res.json();
}

export async function generateEmailDraft(
  token: string,
  data: EmailDraftRequest
): Promise<EmailDraftResponse> {
  const res = await apiFetch(`${API_BASE}/ai/generate-email`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to generate email draft");
  }
  return res.json();
}

export async function suggestReply(
  token: string,
  data: ReplySuggestionRequest
): Promise<ReplySuggestionResponse> {
  const res = await apiFetch(`${API_BASE}/ai/suggest-reply`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to suggest reply");
  }
  return res.json();
}

export async function summarizeConversation(
  token: string,
  data: ConversationSummaryRequest
): Promise<ConversationSummaryResponse> {
  const res = await apiFetch(`${API_BASE}/ai/summarize-conversation`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to summarize conversation");
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Lead Discovery APIs
// ---------------------------------------------------------------------------

export async function runLeadDiscovery(
  token: string,
  data: DiscoveryRunRequest = {}
): Promise<DiscoveryRun[]> {
  const res = await apiFetch(`${API_BASE}/discovery/run`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Discovery run failed");
  }
  return res.json();
}

export async function getDiscoverySources(token: string): Promise<DiscoverySource[]> {
  const res = await apiFetch(`${API_BASE}/discovery/sources`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch discovery sources");
  }
  return res.json();
}

export async function createDiscoverySource(
  token: string,
  data: DiscoverySourceCreate
): Promise<DiscoverySource> {
  const res = await apiFetch(`${API_BASE}/discovery/sources`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to create discovery source");
  }
  return res.json();
}

export async function updateDiscoverySource(
  token: string,
  sourceId: string,
  data: DiscoverySourceUpdate
): Promise<DiscoverySource> {
  const res = await apiFetch(`${API_BASE}/discovery/sources/${sourceId}`, {
    method: "PATCH",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update discovery source");
  }
  return res.json();
}

export async function deleteDiscoverySource(
  token: string,
  sourceId: string
): Promise<void> {
  const res = await apiFetch(`${API_BASE}/discovery/sources/${sourceId}`, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to delete discovery source");
  }
}

export async function getDiscoveryRuns(token: string): Promise<DiscoveryRun[]> {
  const res = await apiFetch(`${API_BASE}/discovery/runs`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch discovery runs");
  }
  return res.json();
}

export async function importManualLead(
  token: string,
  data: ManualLeadImportRequest
): Promise<Lead> {
  const res = await apiFetch(`${API_BASE}/discovery/import`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to import lead");
  }
  return res.json();
}

export async function importCSVLeads(
  token: string,
  file: File
): Promise<CSVImportResult> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await apiFetch(`${API_BASE}/discovery/import/csv`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to upload and import CSV file");
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Social Media Account Connections APIs
// ---------------------------------------------------------------------------

export async function getSocialAccounts(token: string): Promise<SocialAccountConnection[]> {
  const res = await apiFetch(`${API_BASE}/social/accounts`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch connected social accounts");
  }
  return res.json();
}

export async function initiateSocialConnect(
  token: string,
  platform: string,
  redirectUri?: string
): Promise<OAuthInitiateResponse> {
  const query = redirectUri ? `?redirect_uri=${encodeURIComponent(redirectUri)}` : "";
  const res = await apiFetch(`${API_BASE}/social/connect/${platform.toLowerCase()}${query}`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to initiate connection for ${platform}`);
  }
  return res.json();
}

export async function handleProgrammaticOAuthCallback(
  token: string,
  platform: string,
  code: string,
  state: string
): Promise<SocialAccountConnection> {
  const res = await apiFetch(`${API_BASE}/social/callback/${platform.toLowerCase()}`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify({ code, state }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `OAuth callback failed for ${platform}`);
  }
  return res.json();
}

export async function disconnectSocialAccount(
  token: string,
  accountId: string
): Promise<SocialDisconnectResponse> {
  const res = await apiFetch(`${API_BASE}/social/accounts/${accountId}/disconnect`, {
    method: "POST",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to disconnect social account");
  }
  return res.json();
}

export async function refreshSocialAccountToken(
  token: string,
  accountId: string
): Promise<SocialAccountConnection> {
  const res = await apiFetch(`${API_BASE}/social/accounts/${accountId}/refresh`, {
    method: "POST",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to refresh token");
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Email Integration & Outreach APIs
// ---------------------------------------------------------------------------

export async function getEmailAccounts(token: string): Promise<EmailAccountConnection[]> {
  const res = await apiFetch(`${API_BASE}/email/accounts`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch email accounts");
  }
  return res.json();
}

export async function initiateEmailConnect(
  token: string,
  provider: string = "gmail"
): Promise<EmailConnectResponse> {
  const res = await apiFetch(`${API_BASE}/email/connect?provider=${provider}`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to initiate Gmail connection");
  }
  return res.json();
}

export async function handleProgrammaticEmailCallback(
  token: string,
  code: string,
  state: string
): Promise<EmailAccountConnection> {
  const res = await apiFetch(`${API_BASE}/email/callback`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify({ code, state }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Email OAuth exchange failed");
  }
  return res.json();
}

export async function disconnectEmailAccount(
  token: string,
  accountId: string
): Promise<EmailAccountConnection> {
  const res = await apiFetch(`${API_BASE}/email/accounts/${accountId}/disconnect`, {
    method: "POST",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to disconnect email account");
  }
  return res.json();
}

export async function getEmailConversations(
  token: string,
  query?: string
): Promise<EmailConversation[]> {
  const qStr = query ? `?q=${encodeURIComponent(query)}` : "";
  const res = await apiFetch(`${API_BASE}/email/conversations${qStr}`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch email conversations");
  }
  return res.json();
}

export async function getEmailConversation(
  token: string,
  conversationId: string
): Promise<EmailConversation> {
  const res = await apiFetch(`${API_BASE}/email/conversations/${conversationId}`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch conversation thread");
  }
  return res.json();
}

export async function associateLeadToConversation(
  token: string,
  conversationId: string,
  leadId: string | null
): Promise<EmailConversation> {
  const res = await apiFetch(`${API_BASE}/email/conversations/${conversationId}`, {
    method: "PATCH",
    headers: getAuthHeaders(token),
    body: JSON.stringify({ lead_id: leadId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update conversation lead association");
  }
  return res.json();
}

export async function generateAIDraft(
  token: string,
  data: EmailDraftGenerateRequest
): Promise<EmailDraftGenerateResponse> {
  const res = await apiFetch(`${API_BASE}/email/drafts/generate`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to generate AI email draft");
  }
  return res.json();
}

export async function sendApprovedEmail(
  token: string,
  data: EmailSendRequest
): Promise<EmailSendResult> {
  const res = await apiFetch(`${API_BASE}/email/send`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to send approved email");
  }
  return res.json();
}

export async function syncEmailInbox(
  token: string
): Promise<{ status: string; message: string; synced_count: number }> {
  const res = await apiFetch(`${API_BASE}/email/sync`, {
    method: "POST",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to sync inbox");
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Social Content & Multi-Platform Scheduling APIs
// ---------------------------------------------------------------------------

export async function getContentList(
  token: string,
  status?: string
): Promise<ContentItem[]> {
  const qStr = status ? `?status=${encodeURIComponent(status)}` : "";
  const res = await apiFetch(`${API_BASE}/content${qStr}`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch content drafts");
  }
  return res.json();
}

export async function createContent(
  token: string,
  data: ContentCreateInput
): Promise<ContentItem> {
  const res = await apiFetch(`${API_BASE}/content/`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to create content draft");
  }
  return res.json();
}

export async function updateContent(
  token: string,
  contentId: string,
  data: Partial<ContentCreateInput>
): Promise<ContentItem> {
  const res = await apiFetch(`${API_BASE}/content/${contentId}`, {
    method: "PATCH",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update content");
  }
  return res.json();
}

export async function deleteContent(
  token: string,
  contentId: string
): Promise<void> {
  const res = await apiFetch(`${API_BASE}/content/${contentId}`, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to delete content");
  }
}

export async function generateAICaption(
  token: string,
  data: AICaptionGenerateRequestInput
): Promise<AICaptionGenerateResult> {
  const res = await apiFetch(`${API_BASE}/content/generate-caption`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to generate AI caption");
  }
  return res.json();
}

export async function getPlatformCapabilities(
  token: string
): Promise<{ capabilities: PlatformCapabilityInfo[] }> {
  const res = await apiFetch(`${API_BASE}/content/capabilities`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch platform capabilities");
  }
  return res.json();
}

export async function getScheduledPosts(
  token: string,
  status?: string
): Promise<ScheduledPostItem[]> {
  const qStr = status ? `?status=${encodeURIComponent(status)}` : "";
  const res = await apiFetch(`${API_BASE}/social/schedule${qStr}`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch scheduled posts");
  }
  return res.json();
}

export async function scheduleSocialPost(
  token: string,
  contentId: string,
  platforms: string[],
  scheduledAt: string
): Promise<ScheduledPostItem[]> {
  const res = await apiFetch(`${API_BASE}/social/schedule`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      content_id: contentId,
      platforms,
      scheduled_at: scheduledAt,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to schedule post");
  }
  return res.json();
}

export async function publishNowSocialPost(
  token: string,
  contentId: string,
  platforms: string[]
): Promise<PublishResultItem[]> {
  const res = await apiFetch(`${API_BASE}/social/publish-now`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify({ content_id: contentId, platforms }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to publish post");
  }
  return res.json();
}

export async function cancelScheduledPost(
  token: string,
  postId: string
): Promise<ScheduledPostItem> {
  const res = await apiFetch(`${API_BASE}/social/schedule/${postId}/cancel`, {
    method: "POST",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to cancel scheduled post");
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// WhatsApp Business Cloud API
// ---------------------------------------------------------------------------

export async function getWhatsAppAccounts(token: string): Promise<WhatsAppAccount[]> {
  const res = await apiFetch(`${API_BASE}/whatsapp/accounts`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch WhatsApp accounts");
  }
  return res.json();
}

export async function connectWhatsAppAccount(
  token: string,
  data: WhatsAppAccountConnectInput
): Promise<WhatsAppAccount> {
  const res = await apiFetch(`${API_BASE}/whatsapp/connect`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to connect WhatsApp account");
  }
  return res.json();
}

export async function disconnectWhatsAppAccount(
  token: string,
  accountId: string
): Promise<WhatsAppAccount> {
  const res = await apiFetch(`${API_BASE}/whatsapp/accounts/${accountId}/disconnect`, {
    method: "POST",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to disconnect WhatsApp account");
  }
  return res.json();
}

export async function suggestWhatsAppReply(
  token: string,
  conversationId: string
): Promise<{ conversation_id: string; suggested_reply: string }> {
  const res = await apiFetch(
    `${API_BASE}/whatsapp/suggest-reply?conversation_id=${encodeURIComponent(conversationId)}`,
    {
      method: "POST",
      headers: getAuthHeaders(token),
    }
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to generate suggested reply");
  }
  return res.json();
}

export async function sendApprovedWhatsAppMessage(
  token: string,
  data: WhatsAppSendRequestInput
): Promise<WhatsAppSendResult> {
  const res = await apiFetch(`${API_BASE}/whatsapp/send`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to send WhatsApp message");
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Unified Cross-Channel Inbox & Intelligence APIs
// ---------------------------------------------------------------------------

export async function getUnifiedConversations(
  token: string,
  params?: {
    platform?: string;
    lead_status?: string;
    unread_only?: boolean;
    q?: string;
  }
): Promise<UnifiedConversation[]> {
  const searchParams = new URLSearchParams();
  if (params?.platform) searchParams.append("platform", params.platform);
  if (params?.lead_status) searchParams.append("lead_status", params.lead_status);
  if (params?.unread_only) searchParams.append("unread_only", "true");
  if (params?.q) searchParams.append("q", params.q);

  const qStr = searchParams.toString() ? `?${searchParams.toString()}` : "";
  const res = await apiFetch(`${API_BASE}/inbox/conversations${qStr}`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch unified conversations");
  }
  return res.json();
}

export async function getUnifiedConversation(
  token: string,
  conversationId: string
): Promise<UnifiedConversation> {
  const res = await apiFetch(`${API_BASE}/inbox/conversations/${conversationId}`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch conversation thread");
  }
  return res.json();
}

export async function getConversationSummary(
  token: string,
  conversationId: string
): Promise<ConversationSummary> {
  const res = await apiFetch(`${API_BASE}/inbox/conversations/${conversationId}/summary`, {
    method: "POST",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to summarize conversation");
  }
  return res.json();
}

export async function getSuggestedReply(
  token: string,
  conversationId: string
): Promise<SuggestedReply> {
  const res = await apiFetch(`${API_BASE}/inbox/conversations/${conversationId}/suggest-reply`, {
    method: "POST",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to generate suggested reply");
  }
  return res.json();
}

export async function getLeadTimeline(
  token: string,
  leadId: string
): Promise<any[]> {
  const res = await apiFetch(`${API_BASE}/inbox/timeline/${leadId}`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch lead timeline");
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Follow-Up Management APIs
// ---------------------------------------------------------------------------

export async function getFollowUps(
  token: string,
  params?: { status?: string; due?: string }
): Promise<FollowUpItem[]> {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.append("status", params.status);
  if (params?.due) searchParams.append("due", params.due);

  const qStr = searchParams.toString() ? `?${searchParams.toString()}` : "";
  const res = await apiFetch(`${API_BASE}/follow-ups/${qStr}`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch follow-ups");
  }
  return res.json();
}

export async function createFollowUp(
  token: string,
  data: FollowUpCreateInput
): Promise<FollowUpItem> {
  const res = await apiFetch(`${API_BASE}/follow-ups/`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to create follow-up");
  }
  return res.json();
}

export async function updateFollowUp(
  token: string,
  followUpId: string,
  data: FollowUpUpdateInput
): Promise<FollowUpItem> {
  const res = await apiFetch(`${API_BASE}/follow-ups/${followUpId}`, {
    method: "PATCH",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update follow-up");
  }
  return res.json();
}

export async function recommendFollowUps(
  token: string
): Promise<{ status: string; message: string; recommended_count: number }> {
  const res = await apiFetch(`${API_BASE}/follow-ups/recommend`, {
    method: "POST",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to run follow-up recommendations");
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// In-App Notifications APIs
// ---------------------------------------------------------------------------

export async function getNotifications(
  token: string,
  unreadOnly: boolean = false
): Promise<NotificationSummary> {
  const res = await apiFetch(`${API_BASE}/notifications/?unread_only=${unreadOnly}`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch notifications");
  }
  return res.json();
}

export async function markNotificationRead(
  token: string,
  notificationId: string
): Promise<void> {
  const res = await apiFetch(`${API_BASE}/notifications/${notificationId}/read`, {
    method: "PATCH",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to mark notification read");
  }
}

export async function markAllNotificationsRead(token: string): Promise<void> {
  const res = await apiFetch(`${API_BASE}/notifications/mark-all-read`, {
    method: "POST",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to mark all notifications read");
  }
}

// ---------------------------------------------------------------------------
// Communication Preferences APIs
// ---------------------------------------------------------------------------

export async function getCommunicationPreferences(
  token: string
): Promise<UserCommunicationPreferences> {
  const res = await apiFetch(`${API_BASE}/settings/communication-preferences`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch communication preferences");
  }
  return res.json();
}

export async function updateCommunicationPreferences(
  token: string,
  data: UserCommunicationPreferences
): Promise<UserCommunicationPreferences> {
  const res = await apiFetch(`${API_BASE}/settings/communication-preferences`, {
    method: "PATCH",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update communication preferences");
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// CRM Pipeline & Client Directory APIs
// ---------------------------------------------------------------------------

export async function updateLeadStage(
  token: string,
  leadId: string,
  stage: string,
  notes?: string
): Promise<Lead> {
  const res = await apiFetch(`${API_BASE}/crm/leads/${leadId}/stage`, {
    method: "PATCH",
    headers: getAuthHeaders(token),
    body: JSON.stringify({ stage, notes }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update lead pipeline stage");
  }
  return res.json();
}

export async function convertLeadToClient(
  token: string,
  leadId: string,
  data: LeadConvertToClientInput
): Promise<ClientItem> {
  const res = await apiFetch(`${API_BASE}/crm/leads/${leadId}/convert-to-client`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to convert lead to client");
  }
  return res.json();
}

export async function getClients(
  token: string,
  params?: { status?: string; service_id?: string; q?: string }
): Promise<ClientItem[]> {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.append("status", params.status);
  if (params?.service_id) searchParams.append("service_id", params.service_id);
  if (params?.q) searchParams.append("q", params.q);

  const qStr = searchParams.toString() ? `?${searchParams.toString()}` : "";
  const res = await apiFetch(`${API_BASE}/crm/clients/${qStr}`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch clients");
  }
  return res.json();
}

export async function getClient(
  token: string,
  clientId: string
): Promise<ClientItem> {
  const res = await apiFetch(`${API_BASE}/crm/clients/${clientId}`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch client details");
  }
  return res.json();
}

export async function createClient(
  token: string,
  data: ClientCreateInput
): Promise<ClientItem> {
  const res = await apiFetch(`${API_BASE}/crm/clients/`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to create client");
  }
  return res.json();
}

export async function updateClient(
  token: string,
  clientId: string,
  data: Partial<ClientCreateInput>
): Promise<ClientItem> {
  const res = await apiFetch(`${API_BASE}/crm/clients/${clientId}`, {
    method: "PATCH",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update client");
  }
  return res.json();
}

export async function getCRMDashboard(
  token: string
): Promise<CRMDashboardMetrics> {
  const res = await apiFetch(`${API_BASE}/crm/dashboard`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to load CRM dashboard");
  }
  return res.json();
}

export async function getCRMAnalytics(
  token: string
): Promise<CRMAnalyticsData> {
  const res = await apiFetch(`${API_BASE}/crm/analytics`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to load business analytics");
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Global Search API
// ---------------------------------------------------------------------------

export async function globalSearch(
  token: string,
  query: string,
  limit: number = 20
): Promise<GlobalSearchResponse> {
  const res = await apiFetch(
    `${API_BASE}/search/?q=${encodeURIComponent(query)}&limit=${limit}`,
    {
      method: "GET",
      headers: getAuthHeaders(token),
    }
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Search request failed");
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Activity Timeline APIs
// ---------------------------------------------------------------------------

export async function getLeadActivities(
  token: string,
  leadId: string
): Promise<ActivityTimelineData> {
  const res = await apiFetch(`${API_BASE}/activities/lead/${leadId}`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to load lead activity timeline");
  }
  return res.json();
}

export async function getClientActivities(
  token: string,
  clientId: string
): Promise<ActivityTimelineData> {
  const res = await apiFetch(`${API_BASE}/activities/client/${clientId}`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to load client activity timeline");
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Business Profile & User Settings APIs
// ---------------------------------------------------------------------------

export async function getUserBusinessProfile(
  token: string
): Promise<UserBusinessProfile> {
  const res = await apiFetch(`${API_BASE}/settings/business-profile`, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to load business profile");
  }
  return res.json();
}

export async function updateUserBusinessProfile(
  token: string,
  data: UserBusinessProfile
): Promise<UserBusinessProfile> {
  const res = await apiFetch(`${API_BASE}/settings/business-profile`, {
    method: "PATCH",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update business profile");
  }
  return res.json();
}


