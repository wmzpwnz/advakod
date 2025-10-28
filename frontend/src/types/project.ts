// Project management module types for admin panel enhancement

export interface Task {
  id: string;
  title: string;
  description?: string;
  type: 'feature' | 'bug' | 'improvement' | 'maintenance' | 'research' | 'documentation';
  status: 'backlog' | 'todo' | 'in_progress' | 'review' | 'testing' | 'done' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'critical';
  assigneeId?: string;
  assigneeName?: string;
  reporterId: string;
  reporterName: string;
  projectId?: string;
  milestoneId?: string;
  sprintId?: string;
  labels: string[];
  estimatedHours?: number;
  actualHours?: number;
  storyPoints?: number;
  dueDate?: Date;
  startDate?: Date;
  completedDate?: Date;
  createdAt: Date;
  updatedAt: Date;
  comments: TaskComment[];
  attachments: TaskAttachment[];
  dependencies: TaskDependency[];
  subtasks: Task[];
  parentTaskId?: string;
}

export interface TaskComment {
  id: string;
  taskId: string;
  authorId: string;
  authorName: string;
  content: string;
  createdAt: Date;
  updatedAt?: Date;
  isEdited: boolean;
}

export interface TaskAttachment {
  id: string;
  taskId: string;
  fileName: string;
  fileSize: number;
  fileType: string;
  url: string;
  uploadedBy: string;
  uploadedAt: Date;
}

export interface TaskDependency {
  id: string;
  taskId: string;
  dependsOnTaskId: string;
  type: 'blocks' | 'relates_to' | 'duplicates' | 'caused_by';
  createdAt: Date;
}

export interface Milestone {
  id: string;
  name: string;
  description?: string;
  projectId?: string;
  status: 'planning' | 'active' | 'completed' | 'cancelled' | 'overdue';
  startDate: Date;
  dueDate: Date;
  completedDate?: Date;
  progress: number; // 0-100
  totalTasks: number;
  completedTasks: number;
  totalStoryPoints?: number;
  completedStoryPoints?: number;
  budget?: number;
  spentBudget?: number;
  currency?: string;
  ownerId: string;
  ownerName: string;
  createdAt: Date;
  updatedAt: Date;
  tasks: Task[];
}

export interface Sprint {
  id: string;
  name: string;
  goal?: string;
  projectId?: string;
  status: 'planning' | 'active' | 'completed' | 'cancelled';
  startDate: Date;
  endDate: Date;
  capacity: number; // story points or hours
  commitment: number; // planned story points or hours
  completed: number; // actual completed story points or hours
  velocity: number; // average velocity from previous sprints
  tasks: Task[];
  burndownData: BurndownPoint[];
  createdAt: Date;
  updatedAt: Date;
}

export interface BurndownPoint {
  date: Date;
  remainingWork: number;
  idealRemaining: number;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  key: string; // project key like "ADV"
  type: 'software' | 'marketing' | 'research' | 'operations';
  status: 'planning' | 'active' | 'on_hold' | 'completed' | 'cancelled';
  visibility: 'public' | 'private' | 'team';
  leadId: string;
  leadName: string;
  teamMembers: ProjectMember[];
  startDate?: Date;
  endDate?: Date;
  budget?: number;
  spentBudget?: number;
  currency?: string;
  progress: number; // 0-100
  health: 'green' | 'yellow' | 'red';
  milestones: Milestone[];
  sprints: Sprint[];
  totalTasks: number;
  completedTasks: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface ProjectMember {
  userId: string;
  userName: string;
  email: string;
  role: 'owner' | 'admin' | 'developer' | 'designer' | 'tester' | 'viewer';
  joinedAt: Date;
  allocation: number; // percentage of time allocated to project
  isActive: boolean;
}

export interface ResourceAllocation {
  id: string;
  userId: string;
  userName: string;
  email: string;
  role: string;
  department: string;
  totalCapacity: number; // hours per week
  allocations: ProjectAllocation[];
  availability: AvailabilityPeriod[];
  skills: Skill[];
  hourlyRate?: number;
  currency?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface ProjectAllocation {
  projectId: string;
  projectName: string;
  allocation: number; // percentage or hours
  startDate: Date;
  endDate?: Date;
  role: string;
  isActive: boolean;
}

export interface AvailabilityPeriod {
  id: string;
  type: 'vacation' | 'sick_leave' | 'training' | 'conference' | 'unavailable';
  startDate: Date;
  endDate: Date;
  description?: string;
  isApproved: boolean;
  approvedBy?: string;
  createdAt: Date;
}

export interface Skill {
  id: string;
  name: string;
  category: string;
  level: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  yearsOfExperience?: number;
  certifications?: string[];
}

export interface TimeEntry {
  id: string;
  userId: string;
  userName: string;
  taskId?: string;
  projectId?: string;
  description: string;
  hours: number;
  date: Date;
  billable: boolean;
  hourlyRate?: number;
  currency?: string;
  status: 'draft' | 'submitted' | 'approved' | 'rejected';
  approvedBy?: string;
  approvedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface ProjectReport {
  id: string;
  projectId: string;
  type: 'status' | 'progress' | 'budget' | 'resource' | 'velocity' | 'burndown';
  title: string;
  period: DateRange;
  data: Record<string, any>;
  generatedBy: string;
  generatedAt: Date;
  format: 'json' | 'pdf' | 'excel' | 'csv';
  url?: string;
}

export interface ProjectDashboard {
  totalProjects: number;
  activeProjects: number;
  completedProjects: number;
  overdueTasks: number;
  totalTeamMembers: number;
  averageProjectHealth: number;
  budgetUtilization: number;
  velocityTrend: VelocityPoint[];
  upcomingDeadlines: Milestone[];
  resourceUtilization: ResourceUtilization[];
  recentActivity: ProjectActivity[];
  period: DateRange;
  lastUpdated: Date;
}

export interface VelocityPoint {
  sprintName: string;
  planned: number;
  completed: number;
  date: Date;
}

export interface ResourceUtilization {
  userId: string;
  userName: string;
  totalCapacity: number;
  allocated: number;
  utilization: number; // percentage
  overallocated: boolean;
}

export interface ProjectActivity {
  id: string;
  type: 'task_created' | 'task_completed' | 'milestone_reached' | 'sprint_started' | 'sprint_completed';
  description: string;
  userId: string;
  userName: string;
  projectId?: string;
  projectName?: string;
  taskId?: string;
  taskTitle?: string;
  createdAt: Date;
}

export interface KanbanBoard {
  id: string;
  name: string;
  projectId?: string;
  columns: KanbanColumn[];
  filters: KanbanFilters;
  createdAt: Date;
  updatedAt: Date;
}

export interface KanbanColumn {
  id: string;
  name: string;
  status: string;
  order: number;
  wipLimit?: number; // work in progress limit
  tasks: Task[];
  color?: string;
}

export interface KanbanFilters {
  assignee?: string[];
  priority?: string[];
  type?: string[];
  labels?: string[];
  milestone?: string;
  sprint?: string;
}

export interface DateRange {
  start: Date;
  end: Date;
}

// API Response types
export interface ProjectApiResponse<T> {
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

export interface ProjectFilters {
  status?: string[];
  type?: string[];
  assignee?: string[];
  priority?: string[];
  milestone?: string[];
  sprint?: string[];
  dateRange?: DateRange;
  labels?: string[];
}

// Form types for creating/editing
export interface CreateTaskRequest {
  title: string;
  description?: string;
  type: 'feature' | 'bug' | 'improvement' | 'maintenance' | 'research' | 'documentation';
  priority: 'low' | 'medium' | 'high' | 'critical';
  assigneeId?: string;
  projectId?: string;
  milestoneId?: string;
  sprintId?: string;
  labels: string[];
  estimatedHours?: number;
  storyPoints?: number;
  dueDate?: Date;
  parentTaskId?: string;
}

export interface CreateMilestoneRequest {
  name: string;
  description?: string;
  projectId?: string;
  startDate: Date;
  dueDate: Date;
  budget?: number;
  currency?: string;
}

export interface CreateSprintRequest {
  name: string;
  goal?: string;
  projectId?: string;
  startDate: Date;
  endDate: Date;
  capacity: number;
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
  key: string;
  type: 'software' | 'marketing' | 'research' | 'operations';
  visibility: 'public' | 'private' | 'team';
  leadId: string;
  startDate?: Date;
  endDate?: Date;
  budget?: number;
  currency?: string;
}

export interface UpdateResourceAllocationRequest {
  allocations: {
    projectId: string;
    allocation: number;
    startDate: Date;
    endDate?: Date;
    role: string;
  }[];
  availability: Omit<AvailabilityPeriod, 'id' | 'isApproved' | 'approvedBy' | 'createdAt'>[];
}

export interface CreateTimeEntryRequest {
  taskId?: string;
  projectId?: string;
  description: string;
  hours: number;
  date: Date;
  billable: boolean;
}