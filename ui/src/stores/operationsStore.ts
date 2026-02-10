import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// ==================== TYPES ====================

export interface SystemMetrics {
  latency: {
    p50: number // milliseconds
    p95: number
    p99: number
    history: Array<{ timestamp: string; value: number }>
  }
  successRate: {
    current: number // percentage
    history: Array<{ timestamp: string; value: number }>
  }
  errorRate: {
    current: number // percentage
    byType: Record<string, number>
    history: Array<{ timestamp: string; value: number }>
  }
  timestamp: string
}

export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'

export interface Job {
  id: string
  type: 'text_generation' | 'image_generation' | 'lora_training' | 'analysis'
  status: JobStatus
  progress: number
  description: string
  createdAt: string
  startedAt?: string
  completedAt?: string
  estimatedDuration?: number
  nodeId?: string
  error?: string
}

export interface UsageMetrics {
  currentPeriod: {
    startDate: string
    endDate: string
    totalTokens: number
    totalCost: number
    requestCount: number
  }
  byBranch: Array<{
    branchId: string
    tokens: number
    cost: number
    requests: number
  }>
  byOperation: Array<{
    operation: string
    tokens: number
    cost: number
    requests: number
  }>
}

export interface BudgetSettings {
  monthlyBudget: number
  warningThresholds: {
    warning: number // 50%
    critical: number // 80%
    block: number // 100%
  }
  currentSpent: number
}

export interface PrivacySettings {
  localOnly: boolean
  externalProviders: {
    enabled: boolean
    provider: 'openai' | 'anthropic' | 'custom' | null
  }
  dataRetention: {
    enabled: boolean
    retentionDays: number
  }
}

export interface OperationsState {
  // System metrics
  systemMetrics: SystemMetrics | null
  isLoadingMetrics: boolean
  
  // Jobs
  jobs: Job[]
  isLoadingJobs: boolean
  
  // Usage
  usageMetrics: UsageMetrics | null
  isLoadingUsage: boolean
  
  // Budget
  budgetSettings: BudgetSettings
  
  // Privacy
  privacySettings: PrivacySettings
  
  // Dashboard visibility
  operationsPanelOpen: boolean
  activeTab: 'metrics' | 'jobs' | 'usage' | 'sync' | 'privacy'
  
  // Actions
  toggleOperationsPanel: () => void
  setActiveTab: (tab: OperationsState['activeTab']) => void
  refreshSystemMetrics: () => Promise<void>
  refreshJobs: () => Promise<void>
  refreshUsage: () => Promise<void>
  cancelJob: (jobId: string) => Promise<void>
  retryJob: (jobId: string) => Promise<void>
  clearCompletedJobs: () => void
  updateBudgetSettings: (settings: Partial<BudgetSettings>) => void
  updatePrivacySettings: (settings: Partial<PrivacySettings>) => void
  getPendingJobsCount: () => number
  getInProgressJobsCount: () => number
  getCompletedJobsCount: () => number
  getFailedJobsCount: () => number
  getBudgetPercentage: () => number
  getBudgetStatus: () => 'ok' | 'warning' | 'critical' | 'exceeded'
  estimateCost: (operation: string, params: Record<string, unknown>) => { cost: number; confidence: 'high' | 'medium' | 'low' }
}

// Mock data generators
const generateLatencyHistory = (): Array<{ timestamp: string; value: number }> => {
  const history: Array<{ timestamp: string; value: number }> = []
  const now = Date.now()
  for (let i = 24; i >= 0; i--) {
    history.push({
      timestamp: new Date(now - i * 3600000).toISOString(),
      value: 50 + Math.random() * 100 + (Math.random() > 0.9 ? 200 : 0), // Occasional spikes
    })
  }
  return history
}

const generateSuccessRateHistory = (): Array<{ timestamp: string; value: number }> => {
  const history: Array<{ timestamp: string; value: number }> = []
  const now = Date.now()
  for (let i = 24; i >= 0; i--) {
    history.push({
      timestamp: new Date(now - i * 3600000).toISOString(),
      value: 95 + Math.random() * 5,
    })
  }
  return history
}

const generateErrorRateHistory = (): Array<{ timestamp: string; value: number }> => {
  const history: Array<{ timestamp: string; value: number }> = []
  const now = Date.now()
  for (let i = 24; i >= 0; i--) {
    history.push({
      timestamp: new Date(now - i * 3600000).toISOString(),
      value: Math.random() * 3,
    })
  }
  return history
}

// ==================== STORE IMPLEMENTATION ====================

export const useOperationsStore = create<OperationsState>()(
  persist(
    (set, get) => ({
      // ==================== INITIAL STATE ====================
      systemMetrics: null,
      isLoadingMetrics: false,
      
      jobs: [],
      isLoadingJobs: false,
      
      usageMetrics: null,
      isLoadingUsage: false,
      
      budgetSettings: {
        monthlyBudget: 100,
        warningThresholds: {
          warning: 50,
          critical: 80,
          block: 100,
        },
        currentSpent: 0,
      },
      
      privacySettings: {
        localOnly: false,
        externalProviders: {
          enabled: true,
          provider: 'openai',
        },
        dataRetention: {
          enabled: true,
          retentionDays: 90,
        },
      },
      
      operationsPanelOpen: false,
      activeTab: 'metrics',
      
      // ==================== PANEL ACTIONS ====================
      toggleOperationsPanel: () => {
        set(state => ({ operationsPanelOpen: !state.operationsPanelOpen }))
      },
      
      setActiveTab: (tab) => {
        set({ activeTab: tab })
      },
      
      // ==================== SYSTEM METRICS ACTIONS ====================
      refreshSystemMetrics: async () => {
        set({ isLoadingMetrics: true })
        
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 500))
        
        const latencyHistory = generateLatencyHistory()
        const successHistory = generateSuccessRateHistory()
        const errorHistory = generateErrorRateHistory()
        
        set({
          systemMetrics: {
            latency: {
              p50: 85,
              p95: 250,
              p99: 450,
              history: latencyHistory,
            },
            successRate: {
              current: 97.5,
              history: successHistory,
            },
            errorRate: {
              current: 2.5,
              byType: {
                'timeout': 1.2,
                'rate_limit': 0.8,
                'validation': 0.5,
              },
              history: errorHistory,
            },
            timestamp: new Date().toISOString(),
          },
          isLoadingMetrics: false,
        })
      },
      
      // ==================== JOBS ACTIONS ====================
      refreshJobs: async () => {
        set({ isLoadingJobs: true })
        
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 300))
        
        const mockJobs: Job[] = [
          {
            id: 'job-1',
            type: 'text_generation',
            status: 'completed',
            progress: 100,
            description: 'Generate scene dialogue',
            createdAt: new Date(Date.now() - 3600000).toISOString(),
            startedAt: new Date(Date.now() - 3600000 + 5000).toISOString(),
            completedAt: new Date(Date.now() - 3600000 + 30000).toISOString(),
            nodeId: 'node-1',
          },
          {
            id: 'job-2',
            type: 'image_generation',
            status: 'processing',
            progress: 65,
            description: 'Generate manga panels for Chapter 3',
            createdAt: new Date(Date.now() - 600000).toISOString(),
            startedAt: new Date(Date.now() - 580000).toISOString(),
            estimatedDuration: 120,
            nodeId: 'node-5',
          },
          {
            id: 'job-3',
            type: 'lora_training',
            status: 'pending',
            progress: 0,
            description: 'Train character LoRA model',
            createdAt: new Date(Date.now() - 120000).toISOString(),
          },
          {
            id: 'job-4',
            type: 'analysis',
            status: 'failed',
            progress: 45,
            description: 'Tone analysis for scene',
            createdAt: new Date(Date.now() - 7200000).toISOString(),
            startedAt: new Date(Date.now() - 7190000).toISOString(),
            completedAt: new Date(Date.now() - 7150000).toISOString(),
            error: 'API rate limit exceeded',
          },
        ]
        
        set({
          jobs: mockJobs,
          isLoadingJobs: false,
        })
      },
      
      cancelJob: async (jobId) => {
        set(state => ({
          jobs: state.jobs.map(job =>
            job.id === jobId
              ? { ...job, status: 'cancelled', progress: 0 }
              : job
          ),
        }))
      },
      
      retryJob: async (jobId) => {
        set(state => ({
          jobs: state.jobs.map(job =>
            job.id === jobId
              ? { ...job, status: 'pending', progress: 0, error: undefined }
              : job
          ),
        }))
      },
      
      clearCompletedJobs: () => {
        set(state => ({
          jobs: state.jobs.filter(job =>
            job.status !== 'completed' && job.status !== 'cancelled'
          ),
        }))
      },
      
      // ==================== USAGE ACTIONS ====================
      refreshUsage: async () => {
        set({ isLoadingUsage: true })
        
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 400))
        
        const now = new Date()
        const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1)
        
        set({
          usageMetrics: {
            currentPeriod: {
              startDate: startOfMonth.toISOString(),
              endDate: now.toISOString(),
              totalTokens: 1250000,
              totalCost: 12.45,
              requestCount: 342,
            },
            byBranch: [
              { branchId: 'main', tokens: 850000, cost: 8.50, requests: 250 },
              { branchId: 'alternate-ending', tokens: 300000, cost: 3.00, requests: 70 },
              { branchId: 'side-story', tokens: 100000, cost: 0.95, requests: 22 },
            ],
            byOperation: [
              { operation: 'Text Generation', tokens: 800000, cost: 8.00, requests: 200 },
              { operation: 'Image Generation', tokens: 300000, cost: 3.00, requests: 80 },
              { operation: 'Analysis', tokens: 150000, cost: 1.45, requests: 62 },
            ],
          },
          isLoadingUsage: false,
        })
      },
      
      // ==================== BUDGET ACTIONS ====================
      updateBudgetSettings: (settings) => {
        set(state => ({
          budgetSettings: { ...state.budgetSettings, ...settings },
        }))
      },
      
      getBudgetPercentage: () => {
        const { budgetSettings } = get()
        if (budgetSettings.monthlyBudget === 0) return 0
        return (budgetSettings.currentSpent / budgetSettings.monthlyBudget) * 100
      },
      
      getBudgetStatus: () => {
        const percentage = get().getBudgetPercentage()
        const { warningThresholds } = get().budgetSettings
        
        if (percentage >= warningThresholds.block) return 'exceeded'
        if (percentage >= warningThresholds.critical) return 'critical'
        if (percentage >= warningThresholds.warning) return 'warning'
        return 'ok'
      },
      
      // ==================== PRIVACY ACTIONS ====================
      updatePrivacySettings: (settings) => {
        set(state => ({
          privacySettings: { ...state.privacySettings, ...settings },
        }))
      },
      
      // ==================== HELPERS ====================
      getPendingJobsCount: () => {
        return get().jobs.filter(j => j.status === 'pending').length
      },
      
      getInProgressJobsCount: () => {
        return get().jobs.filter(j => j.status === 'processing').length
      },
      
      getCompletedJobsCount: () => {
        return get().jobs.filter(j => j.status === 'completed').length
      },
      
      getFailedJobsCount: () => {
        return get().jobs.filter(j => j.status === 'failed').length
      },
      
      estimateCost: (operation, params) => {
        // Simple cost estimation logic
        const baseCosts: Record<string, number> = {
          text_generation: 0.02,
          image_generation: 0.04,
          lora_training: 0.50,
          analysis: 0.01,
        }
        
        const baseCost = baseCosts[operation] || 0.01
        const tokenMultiplier = typeof params.maxTokens === 'number' ? params.maxTokens / 1000 : 1
        const estimatedCost = baseCost * tokenMultiplier
        
        return {
          cost: Math.round(estimatedCost * 100) / 100,
          confidence: params.maxTokens ? 'high' : 'medium',
        }
      },
    }),
    {
      name: 'loom-operations',
      version: 1,
      partialize: (state) => ({
        budgetSettings: state.budgetSettings,
        privacySettings: state.privacySettings,
      }),
    }
  )
)
