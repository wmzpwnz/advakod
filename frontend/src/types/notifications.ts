// Notification system types for admin panel enhancement

export interface NotificationTemplate {
  id: string;
  name: string;
  description?: string;
  type: 'email' | 'push' | 'sms' | 'slack' | 'telegram' | 'webhook';
  category: 'system' | 'marketing' | 'moderation' | 'project' | 'analytics' | 'security';
  trigger: NotificationTrigger;
  subject?: string; // for email notifications
  title: string; // for push notifications
  content: string;
  contentType: 'text' | 'html' | 'markdown';
  variables: NotificationVariable[];
  conditions: NotificationCondition[];
  isActive: boolean;
  priority: 'low' | 'medium' | 'high' | 'critical';
  throttling?: ThrottlingConfig;
  scheduling?: SchedulingConfig;
  createdBy: string;
  createdAt: Date;
  updatedAt: Date;
  lastUsed?: Date;
  usageCount: number;
}

export interface NotificationTrigger {
  event: string; // e.g., 'user.registered', 'task.completed', 'system.error'
  source: 'user' | 'system' | 'api' | 'scheduled';
  filters?: Record<string, any>;
}

export interface NotificationVariable {
  name: string;
  type: 'string' | 'number' | 'date' | 'boolean' | 'object';
  description: string;
  required: boolean;
  defaultValue?: any;
  example?: any;
}

export interface NotificationCondition {
  field: string;
  operator: 'equals' | 'not_equals' | 'greater_than' | 'less_than' | 'contains' | 'in' | 'not_in' | 'exists';
  value: any;
  logicalOperator?: 'AND' | 'OR';
}

export interface ThrottlingConfig {
  enabled: boolean;
  maxPerHour?: number;
  maxPerDay?: number;
  cooldownMinutes?: number;
  groupBy?: string[]; // fields to group notifications by
}

export interface SchedulingConfig {
  enabled: boolean;
  timezone: string;
  allowedHours?: {
    start: string; // HH:mm format
    end: string;
  };
  allowedDays?: number[]; // 0-6, Sunday = 0
  delay?: number; // minutes to delay notification
}

export interface NotificationHistory {
  id: string;
  templateId: string;
  templateName: string;
  type: 'email' | 'push' | 'sms' | 'slack' | 'telegram' | 'webhook';
  category: 'system' | 'marketing' | 'moderation' | 'project' | 'analytics' | 'security';
  recipientId?: string;
  recipientEmail?: string;
  recipientPhone?: string;
  recipientName?: string;
  subject?: string;
  title: string;
  content: string;
  status: 'pending' | 'sent' | 'delivered' | 'failed' | 'bounced' | 'clicked' | 'opened';
  priority: 'low' | 'medium' | 'high' | 'critical';
  scheduledAt?: Date;
  sentAt?: Date;
  deliveredAt?: Date;
  openedAt?: Date;
  clickedAt?: Date;
  failureReason?: string;
  retryCount: number;
  maxRetries: number;
  metadata: Record<string, any>;
  createdAt: Date;
  updatedAt: Date;
}

export interface NotificationChannel {
  id: string;
  name: string;
  type: 'email' | 'push' | 'sms' | 'slack' | 'telegram' | 'webhook';
  isActive: boolean;
  configuration: ChannelConfiguration;
  rateLimits: RateLimitConfig;
  failureHandling: FailureHandlingConfig;
  createdAt: Date;
  updatedAt: Date;
  lastUsed?: Date;
  successRate: number;
  totalSent: number;
  totalFailed: number;
}

export interface ChannelConfiguration {
  // Email configuration
  smtpHost?: string;
  smtpPort?: number;
  smtpUsername?: string;
  smtpPassword?: string;
  fromEmail?: string;
  fromName?: string;
  
  // Push notification configuration
  vapidPublicKey?: string;
  vapidPrivateKey?: string;
  
  // SMS configuration
  apiKey?: string;
  apiSecret?: string;
  senderId?: string;
  
  // Slack configuration
  webhookUrl?: string;
  botToken?: string;
  channel?: string;
  
  // Telegram configuration
  botToken?: string;
  chatId?: string;
  
  // Webhook configuration
  url?: string;
  method?: 'POST' | 'PUT' | 'PATCH';
  headers?: Record<string, string>;
  authentication?: {
    type: 'none' | 'basic' | 'bearer' | 'api_key';
    credentials?: Record<string, string>;
  };
}

export interface RateLimitConfig {
  enabled: boolean;
  requestsPerSecond?: number;
  requestsPerMinute?: number;
  requestsPerHour?: number;
  requestsPerDay?: number;
  burstLimit?: number;
}

export interface FailureHandlingConfig {
  retryEnabled: boolean;
  maxRetries: number;
  retryDelay: number; // seconds
  exponentialBackoff: boolean;
  deadLetterQueue: boolean;
  fallbackChannel?: string;
}

export interface NotificationSubscription {
  id: string;
  userId: string;
  userEmail: string;
  userName: string;
  role: string;
  categories: SubscriptionCategory[];
  channels: SubscriptionChannel[];
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface SubscriptionCategory {
  category: 'system' | 'marketing' | 'moderation' | 'project' | 'analytics' | 'security';
  enabled: boolean;
  priority: 'low' | 'medium' | 'high' | 'critical';
  channels: string[]; // channel types enabled for this category
}

export interface SubscriptionChannel {
  type: 'email' | 'push' | 'sms' | 'slack' | 'telegram';
  enabled: boolean;
  address?: string; // email, phone, slack channel, etc.
  verified: boolean;
  verifiedAt?: Date;
}

export interface NotificationGroup {
  id: string;
  name: string;
  description?: string;
  notifications: NotificationHistory[];
  groupKey: string; // key used to group notifications
  count: number;
  firstNotificationAt: Date;
  lastNotificationAt: Date;
  status: 'active' | 'dismissed' | 'resolved';
  dismissedBy?: string;
  dismissedAt?: Date;
  resolvedBy?: string;
  resolvedAt?: Date;
  priority: 'low' | 'medium' | 'high' | 'critical';
  category: 'system' | 'marketing' | 'moderation' | 'project' | 'analytics' | 'security';
}

export interface NotificationRule {
  id: string;
  name: string;
  description?: string;
  isActive: boolean;
  conditions: NotificationCondition[];
  actions: NotificationAction[];
  priority: number; // execution order
  createdBy: string;
  createdAt: Date;
  updatedAt: Date;
  executionCount: number;
  lastExecuted?: Date;
}

export interface NotificationAction {
  type: 'send' | 'suppress' | 'delay' | 'escalate' | 'group' | 'transform';
  configuration: Record<string, any>;
}

export interface NotificationStats {
  totalSent: number;
  totalDelivered: number;
  totalFailed: number;
  totalOpened: number;
  totalClicked: number;
  deliveryRate: number;
  openRate: number;
  clickRate: number;
  failureRate: number;
  byChannel: ChannelStats[];
  byCategory: CategoryStats[];
  byPriority: PriorityStats[];
  timeline: TimelineStats[];
  period: DateRange;
  lastUpdated: Date;
}

export interface ChannelStats {
  type: 'email' | 'push' | 'sms' | 'slack' | 'telegram' | 'webhook';
  sent: number;
  delivered: number;
  failed: number;
  opened: number;
  clicked: number;
  deliveryRate: number;
  openRate: number;
  clickRate: number;
}

export interface CategoryStats {
  category: 'system' | 'marketing' | 'moderation' | 'project' | 'analytics' | 'security';
  sent: number;
  delivered: number;
  failed: number;
  opened: number;
  clicked: number;
}

export interface PriorityStats {
  priority: 'low' | 'medium' | 'high' | 'critical';
  sent: number;
  delivered: number;
  failed: number;
  averageDeliveryTime: number; // seconds
}

export interface TimelineStats {
  date: Date;
  sent: number;
  delivered: number;
  failed: number;
  opened: number;
  clicked: number;
}

export interface NotificationCenter {
  unreadCount: number;
  totalCount: number;
  notifications: NotificationCenterItem[];
  groups: NotificationGroup[];
  filters: NotificationFilters;
  lastUpdated: Date;
}

export interface NotificationCenterItem {
  id: string;
  title: string;
  content: string;
  category: 'system' | 'marketing' | 'moderation' | 'project' | 'analytics' | 'security';
  priority: 'low' | 'medium' | 'high' | 'critical';
  isRead: boolean;
  isStarred: boolean;
  actionUrl?: string;
  actionText?: string;
  createdAt: Date;
  readAt?: Date;
  expiresAt?: Date;
  metadata: Record<string, any>;
}

export interface DateRange {
  start: Date;
  end: Date;
}

// API Response types
export interface NotificationApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  pagination?: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

export interface NotificationFilters {
  category?: string[];
  priority?: string[];
  status?: string[];
  type?: string[];
  dateRange?: DateRange;
  isRead?: boolean;
  isStarred?: boolean;
}

// Form types for creating/editing
export interface CreateNotificationTemplateRequest {
  name: string;
  description?: string;
  type: 'email' | 'push' | 'sms' | 'slack' | 'telegram' | 'webhook';
  category: 'system' | 'marketing' | 'moderation' | 'project' | 'analytics' | 'security';
  trigger: NotificationTrigger;
  subject?: string;
  title: string;
  content: string;
  contentType: 'text' | 'html' | 'markdown';
  variables: Omit<NotificationVariable, 'name'>[];
  conditions: NotificationCondition[];
  priority: 'low' | 'medium' | 'high' | 'critical';
  throttling?: ThrottlingConfig;
  scheduling?: SchedulingConfig;
}

export interface CreateNotificationChannelRequest {
  name: string;
  type: 'email' | 'push' | 'sms' | 'slack' | 'telegram' | 'webhook';
  configuration: ChannelConfiguration;
  rateLimits: RateLimitConfig;
  failureHandling: FailureHandlingConfig;
}

export interface SendNotificationRequest {
  templateId?: string;
  type: 'email' | 'push' | 'sms' | 'slack' | 'telegram' | 'webhook';
  recipients: NotificationRecipient[];
  subject?: string;
  title: string;
  content: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  scheduledAt?: Date;
  metadata?: Record<string, any>;
}

export interface NotificationRecipient {
  id?: string;
  email?: string;
  phone?: string;
  name?: string;
  variables?: Record<string, any>;
}

export interface UpdateSubscriptionRequest {
  categories: SubscriptionCategory[];
  channels: SubscriptionChannel[];
}

// WebSocket events for real-time notifications
export interface NotificationWebSocketEvent {
  type: 'notification.new' | 'notification.read' | 'notification.deleted' | 'notification.updated';
  data: NotificationCenterItem | NotificationGroup;
  timestamp: Date;
}