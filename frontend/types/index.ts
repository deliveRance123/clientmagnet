export type LeadStatus =
  | "NEW"
  | "QUALIFIED"
  | "CONTACTED"
  | "REPLIED"
  | "INTERESTED"
  | "DISCOVERY"
  | "PROPOSAL"
  | "NEGOTIATION"
  | "WON"
  | "LOST"
  | "NOT_A_FIT";

export type LeadSource =
  | "MANUAL"
  | "WEBSITE"
  | "EMAIL"
  | "FACEBOOK"
  | "INSTAGRAM"
  | "X"
  | "LINKEDIN"
  | "TIKTOK"
  | "OTHER";

export interface Service {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  pricing: string | null;
  target_clients: string | null;
  portfolio_links: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type ServiceItem = Service;

export interface ServiceCreate {
  name: string;
  description?: string;
  pricing?: string;
  target_clients?: string;
  portfolio_links?: string;
  is_active?: boolean;
}

export interface ServiceUpdate {
  name?: string;
  description?: string;
  pricing?: string;
  target_clients?: string;
  portfolio_links?: string;
  is_active?: boolean;
}

export interface Lead {
  id: string;
  user_id: string;
  name: string;
  company: string | null;
  email: string | null;
  phone: string | null;
  website: string | null;
  platform: string | null;
  profile_url: string | null;
  location: string | null;
  source: LeadSource | string;
  source_url: string | null;
  description: string | null;
  detected_need: string | null;
  matched_service_id: string | null;
  matched_service?: Service | null;
  intent_score: number;
  status: LeadStatus | string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface LeadCreate {
  name: string;
  company?: string;
  email?: string;
  phone?: string;
  website?: string;
  platform?: string;
  profile_url?: string;
  location?: string;
  source?: LeadSource;
  source_url?: string;
  description?: string;
  detected_need?: string;
  matched_service_id?: string;
  intent_score?: number;
  status?: LeadStatus;
  notes?: string;
}

export interface LeadUpdate {
  name?: string;
  company?: string;
  email?: string;
  phone?: string;
  website?: string;
  platform?: string;
  profile_url?: string;
  location?: string;
  source?: LeadSource;
  source_url?: string;
  description?: string;
  detected_need?: string;
  matched_service_id?: string | null;
  intent_score?: number;
  status?: LeadStatus;
  notes?: string;
}

export interface LeadStatsSummary {
  total_leads: number;
  new_leads: number;
  qualified_leads: number;
  interested_leads: number;
  won_clients: number;
}

// ---------------------------------------------------------------------------
// AI Types
// ---------------------------------------------------------------------------

export interface LeadAnalysisRequest {
  lead_id?: string;
  lead_name?: string;
  lead_company?: string;
  lead_description?: string;
  source?: string;
  detected_need?: string;
  additional_context?: string;
}

export interface LeadAnalysisResponse {
  detected_need: string;
  matched_service: string | null;
  matched_service_id: string | null;
  intent_score: number;
  reasoning_summary: string;
  recommended_next_action: string;
}

export interface ServiceMatchRequest {
  lead_id?: string;
  lead_description: string;
  lead_need?: string;
}

export interface ServiceMatchResponse {
  matched_service: string | null;
  matched_service_id: string | null;
  confidence: number;
  match_reasoning: string;
}

export interface IntentScoreRequest {
  lead_id?: string;
  lead_description: string;
  lead_need?: string;
  source?: string;
}

export interface IntentScoreResponse {
  intent_score: number;
  intent_level: string;
  scoring_factors: string[];
  reasoning: string;
}

export interface CaptionGenerateRequest {
  content_description: string;
  platform?: string;
  desired_tone?: string;
  call_to_action?: string;
  target_service_id?: string;
}

export interface CaptionGenerateResponse {
  caption: string;
  hashtags: string[];
  call_to_action: string;
}

export interface EmailDraftRequest {
  lead_id?: string;
  lead_name?: string;
  lead_company?: string;
  lead_need?: string;
  matched_service_id?: string;
  desired_tone?: string;
  custom_instructions?: string;
}

export interface EmailDraftResponse {
  subject: string;
  body: string;
  matched_service_name: string | null;
  tone_used: string;
}

export interface ChatMessageItem {
  sender: string;
  message: string;
  timestamp?: string;
}

export interface ReplySuggestionRequest {
  conversation_id?: string;
  incoming_message: string;
  conversation_history?: ChatMessageItem[];
  preferred_style?: string;
}

export interface ReplySuggestionResponse {
  suggested_reply: string;
  reasoning_summary: string;
}

export interface ConversationSummaryRequest {
  conversation_id?: string;
  messages?: ChatMessageItem[];
  conversation_text?: string;
}

export interface ConversationSummaryResponse {
  summary: string;
  client_needs: string[];
  questions: string[];
  next_action: string;
  lead_status_suggestion: string;
}

// ---------------------------------------------------------------------------
// Discovery Types
// ---------------------------------------------------------------------------

export type DiscoverySourceType = "JOB_BOARD" | "RSS" | "API" | "MANUAL" | "MOCK";
export type DiscoveryFrequency = "MANUAL" | "30MIN" | "HOURLY" | "6HOURS" | "DAILY";
export type DiscoveryRunStatus = "SUCCESS" | "PARTIAL" | "FAILED";

export interface DiscoverySource {
  id: string;
  user_id: string;
  name: string;
  source_type: DiscoverySourceType;
  feed_url?: string | null;
  config_json?: string | null;
  frequency: DiscoveryFrequency;
  is_active: boolean;
  last_run_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface DiscoverySourceCreate {
  name: string;
  source_type: DiscoverySourceType;
  feed_url?: string;
  config_json?: string;
  frequency?: DiscoveryFrequency;
  is_active?: boolean;
}

export interface DiscoverySourceUpdate {
  name?: string;
  source_type?: DiscoverySourceType;
  feed_url?: string;
  config_json?: string;
  frequency?: DiscoveryFrequency;
  is_active?: boolean;
}

export interface DiscoveryRun {
  id: string;
  user_id: string;
  source_id?: string | null;
  status: DiscoveryRunStatus;
  started_at: string;
  finished_at: string;
  total_discovered: number;
  accepted_count: number;
  duplicate_count: number;
  rejected_count: number;
  error_message?: string | null;
  metadata_json?: string | null;
}

export interface DiscoveryRunRequest {
  source_id?: string | null;
  analyze_with_ai?: boolean;
}

export interface ManualLeadImportRequest {
  name: string;
  company?: string;
  email?: string;
  phone?: string;
  website?: string;
  platform?: string;
  location?: string;
  description: string;
  source?: string;
  source_url?: string;
  analyze_with_ai?: boolean;
}

export interface CSVRowError {
  row_number: number;
  error: string;
  row_data?: Record<string, any>;
}

export interface CSVImportResult {
  total_rows: number;
  imported_count: number;
  duplicate_count: number;
  rejected_count: number;
  errors: CSVRowError[];
}

// ---------------------------------------------------------------------------
// Social Media Account Connection Types
// ---------------------------------------------------------------------------

export type SocialConnectionStatus = "CONNECTED" | "DISCONNECTED" | "EXPIRED" | "REAUTH_REQUIRED" | "ERROR";

export interface SocialAccountConnection {
  id: string;
  user_id: string;
  platform: "FACEBOOK" | "INSTAGRAM" | "X" | "LINKEDIN" | "TIKTOK" | string;
  account_identifier: string;
  account_name?: string | null;
  account_username?: string | null;
  profile_picture_url?: string | null;
  connection_status: SocialConnectionStatus;
  scopes: string[];
  token_expires_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface OAuthInitiateResponse {
  platform: string;
  authorization_url: string;
  state: string;
}

export interface SocialDisconnectResponse {
  status: string;
  message: string;
  account_id: string;
}

// ---------------------------------------------------------------------------
// Email Integration & Inbox Types
// ---------------------------------------------------------------------------

export interface EmailAccountConnection {
  id: string;
  user_id: string;
  provider: string;
  email_address: string;
  account_name?: string | null;
  profile_picture_url?: string | null;
  connection_status: "CONNECTED" | "DISCONNECTED" | "EXPIRED" | "REAUTH_REQUIRED";
  scopes: string[];
  token_expires_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmailConnectResponse {
  provider: string;
  authorization_url: string;
  state: string;
}

export interface EmailMessage {
  id: string;
  conversation_id: string;
  sender: string;
  recipient: string;
  subject?: string | null;
  message_content: string;
  platform: string;
  direction: "inbound" | "outbound";
  status: "DRAFT" | "SENT" | "DELIVERED" | "FAILED" | "RECEIVED" | string;
  error_message?: string | null;
  external_message_id?: string | null;
  sent_at: string;
  created_at: string;
}

export interface EmailConversationLeadInfo {
  id: string;
  name: string;
  company?: string | null;
  email?: string | null;
  matched_service_name?: string | null;
}

export interface EmailConversation {
  id: string;
  user_id: string;
  lead_id?: string | null;
  platform: string;
  subject?: string | null;
  external_conversation_id?: string | null;
  status: string;
  unread_count: number;
  last_message_at?: string | null;
  lead?: EmailConversationLeadInfo | null;
  messages: EmailMessage[];
  created_at: string;
  updated_at: string;
}

export interface EmailDraftGenerateRequest {
  lead_id: string;
  service_id?: string | null;
  tone?: string;
  context_notes?: string;
}

export interface EmailDraftGenerateResponse {
  lead_id: string;
  recipient: string;
  subject: string;
  body: string;
  matched_service_id?: string | null;
  matched_service_name?: string | null;
}

export interface EmailSendRequest {
  recipient: string;
  subject: string;
  body: string;
  lead_id?: string | null;
  conversation_id?: string | null;
  in_reply_to_message_id?: string | null;
}

export interface EmailSendResult {
  message_id: string;
  conversation_id: string;
  status: string;
  recipient: string;
  subject: string;
  external_message_id?: string | null;
  sent_at: string;
  message: string;
}

// ---------------------------------------------------------------------------
// Social Media Content & Scheduling Types
// ---------------------------------------------------------------------------

export interface ContentItem {
  id: string;
  user_id: string;
  title: string;
  body: string;
  hashtags?: string | null;
  call_to_action?: string | null;
  target_platforms: string[];
  media_reference?: string | null;
  content_type: string;
  status: "Draft" | "Approved" | "Scheduled" | "Published" | "Archived" | string;
  created_at: string;
  updated_at: string;
}

export interface ContentCreateInput {
  title: string;
  body: string;
  hashtags?: string;
  call_to_action?: string;
  target_platforms?: string[];
  media_reference?: string;
  content_type?: string;
  status?: string;
}

export interface AICaptionGenerateRequestInput {
  topic: string;
  description?: string;
  platform: string;
  tone?: string;
  call_to_action?: string;
}

export interface AICaptionGenerateResult {
  caption: string;
  hashtags: string[];
  call_to_action: string;
  full_formatted_text: string;
  platform: string;
}

export interface ScheduledPostItem {
  id: string;
  user_id: string;
  content_id: string;
  social_account_id?: string | null;
  platform: string;
  scheduled_at: string;
  published_at?: string | null;
  status: "Scheduled" | "Publishing" | "Published" | "Failed" | "Cancelled" | string;
  external_post_id?: string | null;
  error_message?: string | null;
  analytics: {
    likes?: number;
    comments?: number;
    shares?: number;
    views?: number;
    engagement_rate?: number;
  };
  content_title?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PublishResultItem {
  post_id: string;
  platform: string;
  status: string;
  external_post_id?: string | null;
  message: string;
}

export interface PlatformCapabilityInfo {
  platform: string;
  supports_text: boolean;
  supports_image: boolean;
  supports_video: boolean;
  supports_reels: boolean;
  supports_stories: boolean;
  supports_scheduling: boolean;
  max_text_length: number;
  direct_publishing_supported: boolean;
  notes: string;
}

// ---------------------------------------------------------------------------
// WhatsApp Business Cloud API Types
// ---------------------------------------------------------------------------

export interface WhatsAppAccount {
  id: string;
  user_id: string;
  phone_number_id: string;
  phone_number: string;
  business_account_id?: string | null;
  display_name?: string | null;
  connection_status: "CONNECTED" | "DISCONNECTED" | "EXPIRED" | "ERROR" | string;
  webhook_verify_token?: string | null;
  created_at: string;
  updated_at: string;
}

export interface WhatsAppAccountConnectInput {
  phone_number_id: string;
  phone_number: string;
  business_account_id?: string;
  display_name?: string;
  access_token: string;
  webhook_verify_token?: string;
}

export interface WhatsAppSendRequestInput {
  recipient_phone: string;
  message_text: string;
  lead_id?: string | null;
  conversation_id?: string | null;
}

export interface WhatsAppSendResult {
  message_id: string;
  conversation_id: string;
  status: string;
  recipient_phone: string;
  external_message_id?: string | null;
  sent_at: string;
  message: string;
}

// ---------------------------------------------------------------------------
// Unified Cross-Platform Inbox & Conversation Intelligence Types
// ---------------------------------------------------------------------------

export interface UnifiedMessage {
  id: string;
  conversation_id: string;
  sender: string;
  recipient: string;
  subject?: string | null;
  message_content: string;
  platform: string;
  direction: "inbound" | "outbound" | string;
  status: string;
  error_message?: string | null;
  external_message_id?: string | null;
  sent_at: string;
  created_at: string;
}

export interface UnifiedConversation {
  id: string;
  user_id: string;
  lead_id?: string | null;
  platform: string;
  subject?: string | null;
  external_conversation_id?: string | null;
  status: string;
  unread_count: number;
  last_message_at?: string | null;
  lead?: {
    id: string;
    name: string;
    company?: string | null;
    email?: string | null;
    phone?: string | null;
    status: string;
    detected_need?: string | null;
    matched_service_name?: string | null;
  } | null;
  messages: UnifiedMessage[];
  created_at: string;
  updated_at: string;
}

export interface ConversationSummary {
  conversation_id: string;
  summary: string;
  client_needs: string[];
  questions: string[];
  objections: string[];
  next_action: string;
  lead_status_suggestion?: string | null;
}

export interface SuggestedReply {
  conversation_id: string;
  suggested_reply: string;
  rationale?: string | null;
  platform: string;
}

// ---------------------------------------------------------------------------
// Follow-Up Management Types
// ---------------------------------------------------------------------------

export interface FollowUpItem {
  id: string;
  user_id: string;
  lead_id?: string | null;
  conversation_id?: string | null;
  channel: string;
  scheduled_time: string;
  status: "Pending" | "Drafted" | "Approved" | "Sent" | "Cancelled" | string;
  notes?: string | null;
  message_draft?: string | null;
  recommended_by_ai: boolean;
  completed_at?: string | null;
  lead_name?: string | null;
  lead_company?: string | null;
  created_at: string;
  updated_at: string;
}

export interface FollowUpCreateInput {
  lead_id?: string;
  conversation_id?: string;
  channel: string;
  scheduled_time: string;
  notes?: string;
  message_draft?: string;
}

export interface FollowUpUpdateInput {
  scheduled_time?: string;
  channel?: string;
  notes?: string;
  message_draft?: string;
  status?: string;
}

// ---------------------------------------------------------------------------
// Notification Types
// ---------------------------------------------------------------------------

export interface NotificationItem {
  id: string;
  user_id: string;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  link_url?: string | null;
  created_at: string;
}

export interface NotificationSummary {
  unread_count: number;
  notifications: NotificationItem[];
}

export interface UserCommunicationPreferences {
  preferred_tone?: string | null;
  default_signature?: string | null;
  business_intro?: string | null;
  preferred_cta?: string | null;
}

// ---------------------------------------------------------------------------
// CRM Pipeline & Client Types
// ---------------------------------------------------------------------------

export type LeadStage =
  | "NEW"
  | "QUALIFIED"
  | "CONTACTED"
  | "REPLIED"
  | "INTERESTED"
  | "DISCOVERY"
  | "PROPOSAL"
  | "NEGOTIATION"
  | "WON"
  | "LOST";

export type ClientStatus = "ACTIVE" | "COMPLETED" | "PAUSED" | "LOST";

export interface ClientItem {
  id: string;
  user_id: string;
  lead_id?: string | null;
  service_id?: string | null;
  name: string;
  company?: string | null;
  email?: string | null;
  phone?: string | null;
  website?: string | null;
  service_purchased?: string | null;
  service_name?: string | null;
  status: ClientStatus | string;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ClientCreateInput {
  name: string;
  company?: string;
  email?: string;
  phone?: string;
  website?: string;
  lead_id?: string;
  service_id?: string;
  service_purchased?: string;
  status?: string;
  notes?: string;
}

export interface LeadConvertToClientInput {
  service_id?: string;
  service_purchased?: string;
  status?: string;
  notes?: string;
}

// ---------------------------------------------------------------------------
// CRM Dashboard & PostgreSQL Analytics Types
// ---------------------------------------------------------------------------

export interface CRMDashboardMetrics {
  total_leads: number;
  qualified_leads: number;
  active_conversations: number;
  follow_ups_due: number;
  active_clients: number;
  won_deals: number;
  lost_deals: number;
  leads_by_service: Record<string, number>;
  leads_by_source: Record<string, number>;
  leads_by_status: Record<string, number>;
  clients_by_service: Record<string, number>;
}

export interface ConversionFunnelMetrics {
  lead_to_qualified_pct: number;
  qualified_to_contacted_pct: number;
  contacted_to_replied_pct: number;
  replied_to_won_pct: number;
  overall_lead_to_won_pct: number;
}

export interface ServicePerformanceItem {
  service_name: string;
  service_id?: string | null;
  total_leads: number;
  qualified_leads: number;
  clients_count: number;
  won_deals: number;
}

export interface SourcePerformanceItem {
  source_name: string;
  total_leads: number;
  qualified_leads: number;
  clients_count: number;
}

export interface CRMAnalyticsData {
  total_leads: number;
  new_leads: number;
  qualified_leads: number;
  hot_leads: number;
  contacted_leads: number;
  replied_leads: number;
  won_leads: number;
  lost_leads: number;
  conversion_funnel: ConversionFunnelMetrics;
  service_performance: ServicePerformanceItem[];
  source_performance: SourcePerformanceItem[];
}

// ---------------------------------------------------------------------------
// Global Search Types
// ---------------------------------------------------------------------------

export interface GlobalSearchResultItem {
  id: string;
  entity_type: "lead" | "client" | "conversation" | "message" | string;
  title: string;
  subtitle?: string | null;
  snippet?: string | null;
  url: string;
  metadata?: Record<string, any>;
}

export interface GlobalSearchResponse {
  query: string;
  total_results: number;
  results: GlobalSearchResultItem[];
}

// ---------------------------------------------------------------------------
// Activity Timeline Types
// ---------------------------------------------------------------------------

export interface ActivityLogItem {
  id: string;
  user_id: string;
  lead_id?: string | null;
  client_id?: string | null;
  event_type: string;
  channel?: string | null;
  description: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface ActivityTimelineData {
  entity_id: string;
  entity_type: string;
  activities: ActivityLogItem[];
}

// ---------------------------------------------------------------------------
// User Business Profile & Notification Settings
// ---------------------------------------------------------------------------

export interface UserBusinessProfile {
  full_name?: string | null;
  company_name?: string | null;
  business_description?: string | null;
  business_website?: string | null;
  portfolio_links_json?: string | null;
  preferred_tone?: string | null;
  default_signature?: string | null;
  business_intro?: string | null;
  preferred_cta?: string | null;
  notify_new_lead?: boolean;
  notify_new_reply?: boolean;
  notify_follow_up_due?: boolean;
  notify_post_failed?: boolean;
  notify_account_warning?: boolean;
}

