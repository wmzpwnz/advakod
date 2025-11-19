// Marketing module types for admin panel enhancement

export interface SalesFunnel {
  id: string;
  name: string;
  description?: string;
  stages: FunnelStage[];
  createdAt: Date;
  updatedAt: Date;
  isActive: boolean;
  totalUsers: number;
  conversionRate: number;
  revenue: number;
}

export interface FunnelStage {
  id: string;
  name: string;
  description?: string;
  order: number;
  users: number;
  conversionRate: number;
  dropOffRate: number;
  averageTimeSpent: number; // in seconds
  actions: FunnelAction[];
}

export interface FunnelAction {
  id: string;
  name: string;
  type: 'click' | 'view' | 'form_submit' | 'purchase' | 'signup' | 'custom';
  count: number;
  conversionRate: number;
}

export interface PromoCode {
  id: string;
  code: string;
  name: string;
  description?: string;
  type: 'percentage' | 'fixed_amount' | 'free_trial';
  value: number;
  currency?: string;
  minOrderAmount?: number;
  maxDiscountAmount?: number;
  usageLimit?: number;
  usageCount: number;
  userLimit?: number; // per user
  validFrom: Date;
  validTo: Date;
  isActive: boolean;
  applicableProducts?: string[];
  excludedProducts?: string[];
  createdBy: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface PromoCodeUsage {
  id: string;
  promoCodeId: string;
  userId: string;
  orderId?: string;
  discountAmount: number;
  currency: string;
  usedAt: Date;
  userEmail?: string;
  userName?: string;
}

export interface TrafficSource {
  id: string;
  name: string;
  type: 'organic' | 'paid' | 'social' | 'email' | 'direct' | 'referral' | 'affiliate';
  url?: string;
  utmSource?: string;
  utmMedium?: string;
  utmCampaign?: string;
  utmTerm?: string;
  utmContent?: string;
  visitors: number;
  uniqueVisitors: number;
  sessions: number;
  bounceRate: number;
  averageSessionDuration: number; // in seconds
  pageViews: number;
  conversions: number;
  conversionRate: number;
  revenue: number;
  cost?: number;
  roi?: number; // return on investment
  createdAt: Date;
  lastActivity: Date;
}

export interface Campaign {
  id: string;
  name: string;
  description?: string;
  type: 'email' | 'social' | 'ppc' | 'content' | 'affiliate' | 'influencer';
  status: 'draft' | 'active' | 'paused' | 'completed' | 'cancelled';
  budget?: number;
  spent?: number;
  currency?: string;
  startDate: Date;
  endDate?: Date;
  targetAudience?: string[];
  goals: CampaignGoal[];
  metrics: CampaignMetrics;
  createdBy: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface CampaignGoal {
  id: string;
  type: 'awareness' | 'traffic' | 'leads' | 'sales' | 'retention';
  target: number;
  current: number;
  unit: string;
  deadline?: Date;
}

export interface CampaignMetrics {
  impressions: number;
  clicks: number;
  ctr: number; // click-through rate
  conversions: number;
  conversionRate: number;
  cost: number;
  cpc: number; // cost per click
  cpa: number; // cost per acquisition
  revenue: number;
  roi: number;
  lastUpdated: Date;
}

export interface ABTest {
  id: string;
  name: string;
  description?: string;
  hypothesis: string;
  status: 'draft' | 'running' | 'paused' | 'completed' | 'cancelled';
  type: 'page' | 'feature' | 'email' | 'ui_element';
  variants: ABTestVariant[];
  trafficAllocation: number; // percentage of traffic
  startDate: Date;
  endDate?: Date;
  duration?: number; // in days
  sampleSize: number;
  confidenceLevel: number; // 90, 95, 99
  primaryMetric: string;
  secondaryMetrics: string[];
  results?: ABTestResults;
  createdBy: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface ABTestVariant {
  id: string;
  name: string;
  description?: string;
  isControl: boolean;
  trafficPercentage: number;
  participants: number;
  conversions: number;
  conversionRate: number;
  configuration: Record<string, any>;
}

export interface ABTestResults {
  winner?: string; // variant id
  confidence: number;
  pValue: number;
  statisticalSignificance: boolean;
  uplift: number; // percentage improvement
  summary: string;
  recommendations: string[];
  completedAt: Date;
}

export interface EmailCampaign {
  id: string;
  name: string;
  subject: string;
  content: string;
  type: 'newsletter' | 'promotional' | 'transactional' | 'welcome' | 'retention';
  status: 'draft' | 'scheduled' | 'sending' | 'sent' | 'cancelled';
  recipientCount: number;
  segmentIds?: string[];
  scheduledAt?: Date;
  sentAt?: Date;
  metrics: EmailMetrics;
  createdBy: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface EmailMetrics {
  sent: number;
  delivered: number;
  opened: number;
  clicked: number;
  bounced: number;
  unsubscribed: number;
  complained: number;
  openRate: number;
  clickRate: number;
  bounceRate: number;
  unsubscribeRate: number;
  complaintRate: number;
}

export interface CustomerSegment {
  id: string;
  name: string;
  description?: string;
  criteria: SegmentCriteria[];
  userCount: number;
  isActive: boolean;
  createdBy: string;
  createdAt: Date;
  updatedAt: Date;
  lastCalculated: Date;
}

export interface SegmentCriteria {
  field: string;
  operator: 'equals' | 'not_equals' | 'greater_than' | 'less_than' | 'contains' | 'in' | 'not_in';
  value: any;
  logicalOperator?: 'AND' | 'OR';
}

export interface MarketingDashboard {
  totalRevenue: number;
  totalUsers: number;
  newUsers: number;
  activeUsers: number;
  conversionRate: number;
  averageOrderValue: number;
  customerLifetimeValue: number;
  churnRate: number;
  topTrafficSources: TrafficSource[];
  topCampaigns: Campaign[];
  activeFunnels: SalesFunnel[];
  recentPromoUsage: PromoCodeUsage[];
  period: DateRange;
  lastUpdated: Date;
}

export interface DateRange {
  start: Date;
  end: Date;
}

// API Response types
export interface MarketingApiResponse<T> {
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

export interface MarketingFilters {
  dateRange?: DateRange;
  trafficSource?: string[];
  campaign?: string[];
  segment?: string[];
  status?: string[];
}

// Form types for creating/editing
export interface CreatePromoCodeRequest {
  code: string;
  name: string;
  description?: string;
  type: 'percentage' | 'fixed_amount' | 'free_trial';
  value: number;
  currency?: string;
  minOrderAmount?: number;
  maxDiscountAmount?: number;
  usageLimit?: number;
  userLimit?: number;
  validFrom: Date;
  validTo: Date;
  applicableProducts?: string[];
  excludedProducts?: string[];
}

export interface CreateCampaignRequest {
  name: string;
  description?: string;
  type: 'email' | 'social' | 'ppc' | 'content' | 'affiliate' | 'influencer';
  budget?: number;
  currency?: string;
  startDate: Date;
  endDate?: Date;
  targetAudience?: string[];
  goals: Omit<CampaignGoal, 'id' | 'current'>[];
}

export interface CreateABTestRequest {
  name: string;
  description?: string;
  hypothesis: string;
  type: 'page' | 'feature' | 'email' | 'ui_element';
  variants: Omit<ABTestVariant, 'id' | 'participants' | 'conversions' | 'conversionRate'>[];
  trafficAllocation: number;
  duration: number;
  sampleSize: number;
  confidenceLevel: number;
  primaryMetric: string;
  secondaryMetrics: string[];
}