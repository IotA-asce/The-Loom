import { create } from 'zustand'

// ==================== TYPES ====================

export interface BranchSuggestion {
  id: string
  nodeId: string
  nodeLabel: string
  description: string
  divergenceScore: number // 0-100
  impactSummary: {
    affectedNodes: number
    consistencyImpact: 'low' | 'medium' | 'high'
    estimatedTokens: number
  }
  reason: string
  dismissed: boolean
  createdAt: string
}

export interface Constraint {
  id: string
  type: 'canon' | 'character' | 'timeline' | 'tone'
  description: string
  severity: 'info' | 'warning' | 'critical'
  sourceNodeId?: string
  createdAt: string
}

export interface ConstraintViolation {
  id: string
  constraintId: string
  nodeId: string
  message: string
  severity: 'warning' | 'critical'
  suggestedFix?: string
  createdAt: string
  acknowledged: boolean
}

export interface RecommendationsState {
  // Suggestions
  suggestions: BranchSuggestion[]
  isLoadingSuggestions: boolean
  
  // Constraints
  constraints: Constraint[]
  violations: ConstraintViolation[]
  
  // Panel state
  recommendationsPanelOpen: boolean
  activeTab: 'suggestions' | 'constraints'
  
  // Selected for preview
  previewSuggestionId: string | null
  previewData: {
    affectedNodes: Array<{ id: string; label: string; impact: 'high' | 'medium' | 'low' }>
    consistencyScore: number
    riskLevel: 'low' | 'medium' | 'high' | 'critical'
  } | null
  
  // Actions
  toggleRecommendationsPanel: () => void
  setActiveTab: (tab: RecommendationsState['activeTab']) => void
  refreshSuggestions: () => Promise<void>
  dismissSuggestion: (suggestionId: string) => void
  createBranchFromSuggestion: (suggestionId: string, label: string) => Promise<string | null>
  previewImpact: (suggestionId: string) => Promise<void>
  clearPreview: () => void
  
  // Constraint actions
  addConstraint: (constraint: Omit<Constraint, 'id' | 'createdAt'>) => void
  removeConstraint: (constraintId: string) => void
  acknowledgeViolation: (violationId: string) => void
  getViolationCount: () => number
  getUnacknowledgedViolations: () => ConstraintViolation[]
  getAllUnresolvedCount: () => number
}

// Mock data generators
const generateMockSuggestions = (): BranchSuggestion[] => [
  {
    id: 'sugg-1',
    nodeId: 'node-5',
    nodeLabel: 'The Revelation',
    description: 'Create alternate timeline where the protagonist discovers the truth earlier',
    divergenceScore: 85,
    impactSummary: {
      affectedNodes: 12,
      consistencyImpact: 'high',
      estimatedTokens: 4500,
    },
    reason: 'High reader engagement potential - this branch point has significant narrative weight',
    dismissed: false,
    createdAt: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: 'sugg-2',
    nodeId: 'node-12',
    nodeLabel: 'The Betrayal',
    description: 'Explore outcome if the ally refuses to betray the protagonist',
    divergenceScore: 72,
    impactSummary: {
      affectedNodes: 8,
      consistencyImpact: 'medium',
      estimatedTokens: 3200,
    },
    reason: 'Character arc variation - offers different emotional trajectory',
    dismissed: false,
    createdAt: new Date(Date.now() - 172800000).toISOString(),
  },
  {
    id: 'sugg-3',
    nodeId: 'node-8',
    nodeLabel: 'The Choice',
    description: 'Branch where the protagonist takes the dangerous path',
    divergenceScore: 68,
    impactSummary: {
      affectedNodes: 6,
      consistencyImpact: 'medium',
      estimatedTokens: 2800,
    },
    reason: 'Genre alignment - high-stakes choice fits thriller tone',
    dismissed: false,
    createdAt: new Date(Date.now() - 259200000).toISOString(),
  },
  {
    id: 'sugg-4',
    nodeId: 'node-3',
    nodeLabel: 'The Meeting',
    description: 'What if the meeting never happens?',
    divergenceScore: 45,
    impactSummary: {
      affectedNodes: 4,
      consistencyImpact: 'low',
      estimatedTokens: 1500,
    },
    reason: 'Exploratory branch - lower impact but interesting possibilities',
    dismissed: true,
    createdAt: new Date(Date.now() - 345600000).toISOString(),
  },
]

const generateMockConstraints = (): Constraint[] => [
  {
    id: 'const-1',
    type: 'canon',
    description: 'Protagonist must survive until Chapter 10',
    severity: 'critical',
    createdAt: new Date(Date.now() - 604800000).toISOString(),
  },
  {
    id: 'const-2',
    type: 'character',
    description: 'Antagonist cannot show remorse before Act 3',
    severity: 'warning',
    createdAt: new Date(Date.now() - 518400000).toISOString(),
  },
  {
    id: 'const-3',
    type: 'timeline',
    description: 'Events must occur in chronological order within each branch',
    severity: 'info',
    createdAt: new Date(Date.now() - 432000000).toISOString(),
  },
  {
    id: 'const-4',
    type: 'tone',
    description: 'Maintain dark atmosphere in horror branches',
    severity: 'warning',
    createdAt: new Date(Date.now() - 345600000).toISOString(),
  },
]

const generateMockViolations = (): ConstraintViolation[] => [
  {
    id: 'viol-1',
    constraintId: 'const-1',
    nodeId: 'node-15',
    message: 'Protagonist death detected before Chapter 10',
    severity: 'critical',
    suggestedFix: 'Move death scene to Chapter 11 or later',
    createdAt: new Date(Date.now() - 3600000).toISOString(),
    acknowledged: false,
  },
  {
    id: 'viol-2',
    constraintId: 'const-2',
    nodeId: 'node-7',
    message: 'Antagonist shows early remorse in dialogue',
    severity: 'warning',
    suggestedFix: 'Remove sympathetic dialogue or move to Act 3',
    createdAt: new Date(Date.now() - 7200000).toISOString(),
    acknowledged: false,
  },
  {
    id: 'viol-3',
    constraintId: 'const-4',
    nodeId: 'node-9',
    message: 'Tone shift detected - comedic elements in horror branch',
    severity: 'warning',
    createdAt: new Date(Date.now() - 10800000).toISOString(),
    acknowledged: true,
  },
]

// ==================== STORE IMPLEMENTATION ====================

export const useRecommendationsStore = create<RecommendationsState>((set, get) => ({
  // ==================== INITIAL STATE ====================
  suggestions: [],
  isLoadingSuggestions: false,
  
  constraints: [],
  violations: [],
  
  recommendationsPanelOpen: false,
  activeTab: 'suggestions',
  
  previewSuggestionId: null,
  previewData: null,
  
  // ==================== PANEL ACTIONS ====================
  toggleRecommendationsPanel: () => {
    set(state => ({ recommendationsPanelOpen: !state.recommendationsPanelOpen }))
    // Load data if opening
    if (!get().recommendationsPanelOpen) {
      get().refreshSuggestions()
    }
  },
  
  setActiveTab: (tab) => {
    set({ activeTab: tab })
  },
  
  // ==================== SUGGESTIONS ACTIONS ====================
  refreshSuggestions: async () => {
    set({ isLoadingSuggestions: true })
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 600))
    
    set({
      suggestions: generateMockSuggestions(),
      constraints: generateMockConstraints(),
      violations: generateMockViolations(),
      isLoadingSuggestions: false,
    })
  },
  
  dismissSuggestion: (suggestionId) => {
    set(state => ({
      suggestions: state.suggestions.map(s =>
        s.id === suggestionId ? { ...s, dismissed: true } : s
      ),
    }))
  },
  
  createBranchFromSuggestion: async (suggestionId, _label) => {
    const suggestion = get().suggestions.find(s => s.id === suggestionId)
    if (!suggestion) return null
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 800))
    
    const newBranchId = `branch-${Date.now()}`
    
    // Mark suggestion as dismissed after creating branch
    get().dismissSuggestion(suggestionId)
    
    return newBranchId
  },
  
  previewImpact: async (suggestionId) => {
    set({ previewSuggestionId: suggestionId, previewData: null })
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 500))
    
    const suggestion = get().suggestions.find(s => s.id === suggestionId)
    if (!suggestion) return
    
    // Generate mock preview data based on suggestion
    const affectedCount = suggestion.impactSummary.affectedNodes
    set({
      previewData: {
        affectedNodes: Array.from({ length: Math.min(affectedCount, 6) }, (_, i) => ({
          id: `node-${i + 1}`,
          label: `Affected Node ${i + 1}`,
          impact: i < 3 ? 'high' : i < 5 ? 'medium' : 'low' as const,
        })),
        consistencyScore: 100 - suggestion.divergenceScore * 0.3,
        riskLevel: suggestion.impactSummary.consistencyImpact === 'high' ? 'high' : 
                   suggestion.impactSummary.consistencyImpact === 'medium' ? 'medium' : 'low',
      },
    })
  },
  
  clearPreview: () => {
    set({ previewSuggestionId: null, previewData: null })
  },
  
  // ==================== CONSTRAINT ACTIONS ====================
  addConstraint: (constraint) => {
    const newConstraint: Constraint = {
      ...constraint,
      id: `const-${Date.now()}`,
      createdAt: new Date().toISOString(),
    }
    set(state => ({
      constraints: [...state.constraints, newConstraint],
    }))
  },
  
  removeConstraint: (constraintId) => {
    set(state => ({
      constraints: state.constraints.filter(c => c.id !== constraintId),
      violations: state.violations.filter(v => v.constraintId !== constraintId),
    }))
  },
  
  acknowledgeViolation: (violationId) => {
    set(state => ({
      violations: state.violations.map(v =>
        v.id === violationId ? { ...v, acknowledged: true } : v
      ),
    }))
  },
  
  getViolationCount: () => {
    return get().violations.filter(v => !v.acknowledged).length
  },
  
  getUnacknowledgedViolations: () => {
    return get().violations.filter(v => !v.acknowledged)
  },
  
  getAllUnresolvedCount: () => {
    return get().violations.filter(v => !v.acknowledged).length
  },
}))
