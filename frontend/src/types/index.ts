// Main types export file for admin panel enhancement

// Marketing module types
export * from './marketing';

// Project management module types  
export * from './project';

// Notification system types
export * from './notifications';

// Common types used across modules
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'super_admin' | 'admin' | 'moderator' | 'analyst' | 'marketing_manager' | 'project_manager';
  isActive: boolean;
  lastLogin?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface AdminRole {
  id: string;
  name: string;
  description?: string;
  permissions: Permission[];
  isSystem: boolean; // cannot be deleted
  userCount: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface Permission {
  id: string;
  name: string;
  resource: string;
  action: 'create' | 'read' | 'update' | 'delete' | 'execute';
  conditions?: Record<string, any>;
}

export interface AuditLog {
  id: string;
  userId: string;
  userName: string;
  userRole: string;
  action: string;
  resource: string;
  resourceId?: string;
  details: Record<string, any>;
  ipAddress: string;
  userAgent: string;
  timestamp: Date;
  success: boolean;
  errorMessage?: string;
}

export interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical' | 'down';
  uptime: number; // seconds
  lastCheck: Date;
  services: ServiceHealth[];
  metrics: SystemMetrics;
}

export interface ServiceHealth {
  name: string;
  status: 'healthy' | 'warning' | 'critical' | 'down';
  responseTime: number; // milliseconds
  lastCheck: Date;
  errorMessage?: string;
  url?: string;
}

export interface SystemMetrics {
  cpuUsage: number; // percentage
  memoryUsage: number; // percentage
  diskUsage: number; // percentage
  networkIn: number; // bytes per second
  networkOut: number; // bytes per second
  activeConnections: number;
  requestsPerSecond: number;
  errorRate: number; // percentage
}

export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  errors?: string[];
  pagination?: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
  meta?: Record<string, any>;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface FilterParams {
  search?: string;
  dateFrom?: Date;
  dateTo?: Date;
  status?: string[];
  category?: string[];
  [key: string]: any;
}

export interface DateRange {
  start: Date;
  end: Date;
}

export interface ChartDataPoint {
  label: string;
  value: number;
  date?: Date;
  category?: string;
  color?: string;
}

export interface TableColumn<T = any> {
  key: keyof T | string;
  title: string;
  sortable?: boolean;
  filterable?: boolean;
  width?: string | number;
  align?: 'left' | 'center' | 'right';
  render?: (value: any, record: T) => React.ReactNode;
}

export interface TableProps<T = any> {
  columns: TableColumn<T>[];
  data: T[];
  loading?: boolean;
  pagination?: {
    current: number;
    pageSize: number;
    total: number;
    onChange: (page: number, pageSize: number) => void;
  };
  selection?: {
    selectedRowKeys: string[];
    onChange: (selectedRowKeys: string[], selectedRows: T[]) => void;
  };
  onRow?: (record: T) => {
    onClick?: () => void;
    onDoubleClick?: () => void;
  };
}

export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'number' | 'date' | 'datetime' | 'select' | 'multiselect' | 'textarea' | 'checkbox' | 'radio' | 'file';
  required?: boolean;
  placeholder?: string;
  options?: { label: string; value: any }[];
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    custom?: (value: any) => string | null;
  };
  disabled?: boolean;
  hidden?: boolean;
  defaultValue?: any;
  description?: string;
}

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  closable?: boolean;
  maskClosable?: boolean;
  footer?: React.ReactNode;
  children: React.ReactNode;
}

export interface ToastNotification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number; // milliseconds, 0 for persistent
  action?: {
    label: string;
    onClick: () => void;
  };
  createdAt: Date;
}

// Theme and UI types
export interface ThemeConfig {
  mode: 'light' | 'dark' | 'auto';
  primaryColor: string;
  borderRadius: number;
  fontSize: number;
  fontFamily: string;
  compactMode: boolean;
  animations: boolean;
}

export interface ModuleColors {
  marketing: string;
  moderation: string;
  project: string;
  analytics: string;
  system: string;
}

// WebSocket types
export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: Date;
  id?: string;
}

export interface WebSocketConnection {
  isConnected: boolean;
  lastConnected?: Date;
  reconnectAttempts: number;
  maxReconnectAttempts: number;
}

// Error types
export interface AppError {
  code: string;
  message: string;
  details?: Record<string, any>;
  timestamp: Date;
  userId?: string;
  requestId?: string;
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

// File upload types
export interface FileUpload {
  id: string;
  name: string;
  size: number;
  type: string;
  url?: string;
  progress: number;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  error?: string;
  uploadedAt?: Date;
}

// Search types
export interface SearchResult<T = any> {
  id: string;
  title: string;
  description?: string;
  type: string;
  url?: string;
  data: T;
  score: number;
  highlights?: string[];
}

export interface SearchFilters {
  types?: string[];
  dateRange?: DateRange;
  categories?: string[];
  [key: string]: any;
}

// Export utility types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

export type Nullable<T> = T | null;

export type ID = string | number;