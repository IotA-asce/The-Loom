import { create } from 'zustand'

// ==================== TYPES ====================

export interface Toast {
  id: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  duration?: number
}

export interface SyncState {
  sceneId: string
  textVersion: string
  imageVersion: string
  textStatus: string
  imageStatus: string
  badges: { label: string; icon: string }[]
}

export interface GraphMetrics {
  totalNodes: number
  visibleNodes: number
  visibleEdges: number
  virtualizationRatio: number
  estimatedFrameMs: number
  mode: string
  performanceUsable: boolean
}

export interface Phase8Metrics {
  graphPerformanceUsable: boolean
  keyboardMobileUsable: boolean
  dualSyncVisibleAndAccurate: boolean
  virtualizationRatio: number
  estimatedFrameMs: number
  keyboardCoverage: number
  mismatchRate: number
}

export interface SearchResult {
  id: string
  text: string
  source: string
  branchId: string
  relevanceScore: number
  entityType?: 'character' | 'location' | 'event'
  entityName?: string
  timestamp?: string
}

export interface SimulationResult {
  affectedNodes: Array<{
    id: string
    name: string
    impact: 'high' | 'medium' | 'low'
    description: string
  }>
  consistencyScore: number
  riskLevel: 'low' | 'medium' | 'high' | 'critical'
  estimatedTokens: number
  estimatedTime: number
  suggestedActions: string[]
}

// ==================== UI STATE ====================

export interface UIState {
  // Toast notifications
  toasts: Toast[]

  // Loading states
  loading: {
    nodes: boolean
    content: boolean
    generation: boolean
  }

  // Error states
  error: {
    nodes: string | null
    content: string | null
  }

  // Panel visibility flags
  dualViewOpen: boolean
  syncState: SyncState | null
  searchPanelOpen: boolean
  searchResults: SearchResult[]
  memoryBrowserOpen: boolean
  simulatorOpen: boolean
  toneHeatmapOpen: boolean

  // Metrics
  graphMetrics: GraphMetrics | null
  phase8Metrics: Phase8Metrics | null

  // Import
  supportedFormats: { text: string[]; manga: string[]; images: string[] }

  // Keyboard shortcuts
  keyboardShortcuts: Record<string, () => void>

  // Cross-store references
  selectedNodeId: string | null
  nodes: { id: string; label: string; x: number; y: number; branchId: string }[]
  branches: { branchId: string; status: string }[]
}

export interface UIActions {
  // Toast notifications
  addToast: (toast: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void

  // Loading states
  setLoading: (key: keyof UIState['loading'], value: boolean) => void

  // Error states
  setError: (key: keyof UIState['error'], message: string | null) => void
  clearError: (key: keyof UIState['error']) => void

  // Panel toggles
  toggleDualView: () => void
  toggleSearchPanel: () => void
  toggleMemoryBrowser: () => void
  toggleSimulator: () => void
  toggleToneHeatmap: () => void

  // Dual view actions
  initializeDualView: (sceneId: string) => Promise<void>
  editSentence: (sceneId: string, sentenceIndex: number, previousText: string, newText: string) => Promise<void>
  requestPanelRedraw: (sceneId: string, panelIndex: number, reason: string) => Promise<void>
  reconcile: (sceneId: string, textVersion: string, imageVersion: string) => Promise<void>

  // Search & Memory
  performSearch: (query: string, filters: Record<string, string>) => Promise<SearchResult[]>
  addToContext: (resultId: string, getSearchResults: () => SearchResult[], addContextChunk?: (result: SearchResult) => void) => void

  // Simulator
  simulateChange: (request: { nodeId: string; changeType: string; description: string }) => Promise<SimulationResult>

  // Metrics
  refreshMetrics: () => Promise<void>

  // Import actions
  ingestFile: (file: File, refreshMetrics?: () => Promise<void>) => Promise<{ success: boolean; [key: string]: any }>

  // Keyboard navigation
  navigateGraph: (direction: 'up' | 'down' | 'left' | 'right', getNodes?: () => UIState['nodes'], getSelectedNodeId?: () => string | null, selectNode?: (id: string) => void) => void
  selectNextNode: (getNodes?: () => UIState['nodes'], getSelectedNodeId?: () => string | null, selectNode?: (id: string) => void) => void
  selectPreviousNode: (getNodes?: () => UIState['nodes'], getSelectedNodeId?: () => string | null, selectNode?: (id: string) => void) => void
  editSelectedNode: (getSelectedNodeId?: () => string | null, startEditingNode?: (id: string) => void) => void
  deleteSelectedNode: (getSelectedNodeId?: () => string | null, deleteNode?: (id: string) => Promise<void>) => void

  // Initialization
  initialize: () => void
  setKeyboardShortcuts: (shortcuts: Record<string, () => void>) => void

  // Cross-store setters
  setSelectedNodeId: (nodeId: string | null) => void
  setNodes: (nodes: UIState['nodes']) => void
  setBranches: (branches: UIState['branches']) => void
}

const API_BASE = '/api'

// ==================== STORE IMPLEMENTATION ====================

export const useUIStore = create<UIState & UIActions>((set, get) => ({
  // ==================== INITIAL STATE ====================
  toasts: [],
  loading: {
    nodes: false,
    content: false,
    generation: false,
  },
  error: {
    nodes: null,
    content: null,
  },
  dualViewOpen: false,
  syncState: null,
  searchPanelOpen: false,
  searchResults: [],
  memoryBrowserOpen: false,
  simulatorOpen: false,
  toneHeatmapOpen: false,
  graphMetrics: null,
  phase8Metrics: null,
  supportedFormats: { text: ['.txt', '.pdf', '.epub'], manga: ['.cbz', '.zip'], images: ['.png', '.jpg', '.jpeg', '.webp'] },
  keyboardShortcuts: {},
  selectedNodeId: null,
  nodes: [],
  branches: [],

  // ==================== INITIALIZATION ====================
  initialize: () => {
    get().refreshMetrics()
  },

  setKeyboardShortcuts: (shortcuts) => set({ keyboardShortcuts: shortcuts }),

  // ==================== TOAST NOTIFICATIONS ====================
  addToast: (toast) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    set(state => ({
      toasts: [...state.toasts, { ...toast, id }]
    }))
    setTimeout(() => {
      get().removeToast(id)
    }, toast.duration || 5000)
  },

  removeToast: (id) => {
    set(state => ({
      toasts: state.toasts.filter(t => t.id !== id)
    }))
  },

  // ==================== LOADING STATES ====================
  setLoading: (key, value) => {
    set(state => ({
      loading: { ...state.loading, [key]: value }
    }))
  },

  // ==================== ERROR STATES ====================
  setError: (key, message) => {
    set(state => ({
      error: { ...state.error, [key]: message }
    }))
  },

  clearError: (key) => {
    set(state => ({ error: { ...state.error, [key]: null } }))
  },

  // ==================== PANEL TOGGLES ====================
  toggleDualView: () => set(state => ({ dualViewOpen: !state.dualViewOpen })),
  toggleSearchPanel: () => set(state => ({ searchPanelOpen: !state.searchPanelOpen })),
  toggleMemoryBrowser: () => set(state => ({ memoryBrowserOpen: !state.memoryBrowserOpen })),
  toggleSimulator: () => set(state => ({ simulatorOpen: !state.simulatorOpen })),
  toggleToneHeatmap: () => set(state => ({ toneHeatmapOpen: !state.toneHeatmapOpen })),

  // ==================== DUAL VIEW ACTIONS ====================
  initializeDualView: async (sceneId) => {
    try {
      const response = await fetch(`${API_BASE}/dualview/initialize?sceneId=${encodeURIComponent(sceneId)}`, {
        method: 'POST',
      })
      if (response.ok) {
        const result = await response.json()
        set({ syncState: result })
      }
    } catch (error) {
      console.error('Failed to initialize dual view:', error)
    }
  },

  editSentence: async (sceneId, sentenceIndex, previousText, newText) => {
    try {
      const response = await fetch(`${API_BASE}/dualview/sentence-edit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sceneId, sentenceIndex, previousText, newText }),
      })
      if (response.ok) {
        const result = await response.json()
        set({ syncState: result })
      }
    } catch (error) {
      console.error('Failed to edit sentence:', error)
    }
  },

  requestPanelRedraw: async (sceneId, panelIndex, reason) => {
    try {
      const response = await fetch(`${API_BASE}/dualview/panel-redraw`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sceneId, panelIndex, reason }),
      })
      if (response.ok) {
        const result = await response.json()
        set({ syncState: result })
      }
    } catch (error) {
      console.error('Failed to request panel redraw:', error)
    }
  },

  reconcile: async (sceneId, textVersion, imageVersion) => {
    try {
      const response = await fetch(`${API_BASE}/dualview/reconcile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sceneId, textVersion, imageVersion }),
      })
      if (response.ok) {
        const result = await response.json()
        set({ syncState: result })
      }
    } catch (error) {
      console.error('Failed to reconcile:', error)
    }
  },

  // ==================== SEARCH & MEMORY ====================
  performSearch: async (_query, _filters) => {
    const mockResults: SearchResult[] = [
      {
        id: `search-${Date.now()}`,
        text: 'Search result text...',
        source: 'Chapter 1',
        branchId: 'main',
        relevanceScore: 0.95,
      },
    ]
    set({ searchResults: mockResults })
    return mockResults
  },

  addToContext: (resultId, getSearchResults, addContextChunk) => {
    const results = getSearchResults()
    const result = results.find(r => r.id === resultId)
    if (result && addContextChunk) {
      addContextChunk(result)
    }
  },

  // ==================== SIMULATOR ====================
  simulateChange: async (_request) => {
    await new Promise(resolve => setTimeout(resolve, 1000))
    const result: SimulationResult = {
      affectedNodes: [],
      consistencyScore: 0.85,
      riskLevel: 'medium',
      estimatedTokens: 2500,
      estimatedTime: 30,
      suggestedActions: ['Review related nodes'],
    }
    return result
  },

  // ==================== METRICS ====================
  refreshMetrics: async () => {
    try {
      const [graphResponse, phase8Response] = await Promise.all([
        fetch(`${API_BASE}/graph/metrics`),
        fetch(`${API_BASE}/phase8/metrics?sceneId=default`),
      ])

      if (graphResponse.ok) {
        set({ graphMetrics: await graphResponse.json() })
      }
      if (phase8Response.ok) {
        set({ phase8Metrics: await phase8Response.json() })
      }
    } catch (error) {
      console.error('Failed to refresh metrics:', error)
    }
  },

  // ==================== IMPORT ACTIONS ====================
  ingestFile: async (file, refreshMetrics) => {
    const formData = new FormData()
    formData.append('file', file)

    const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
    const isText = ['.txt', '.pdf', '.epub'].includes(extension)
    const isManga = ['.cbz', '.zip'].includes(extension)

    const endpoint = isText ? 'ingest/text' : isManga ? 'ingest/manga' : 'ingest/text'

    try {
      const response = await fetch(`${API_BASE}/${endpoint}`, {
        method: 'POST',
        body: formData,
      })

      if (response.ok) {
        const result = await response.json()
        if (refreshMetrics) await refreshMetrics()
        return result
      } else {
        const error = await response.text()
        return { success: false, message: error }
      }
    } catch (error) {
      console.error('Failed to ingest file:', error)
      return { success: false, message: String(error) }
    }
  },

  // ==================== KEYBOARD NAVIGATION ====================
  navigateGraph: (direction, getNodesFn, getSelectedNodeIdFn, selectNodeFn) => {
    const nodes = getNodesFn ? getNodesFn() : get().nodes
    const selectedNodeId = getSelectedNodeIdFn ? getSelectedNodeIdFn() : get().selectedNodeId

    if (nodes.length === 0) return

    if (!selectedNodeId) {
      if (selectNodeFn) selectNodeFn(nodes[0].id)
      return
    }

    const currentNode = nodes.find(n => n.id === selectedNodeId)
    if (!currentNode) return

    const threshold = 50
    let bestNode: typeof currentNode | null = null
    let bestScore = Infinity

    for (const node of nodes) {
      if (node.id === selectedNodeId) continue

      const dx = node.x - currentNode.x
      const dy = node.y - currentNode.y

      let score = Infinity
      let inDirection = false

      switch (direction) {
        case 'up':
          inDirection = dy < -threshold && Math.abs(dx) < Math.abs(dy)
          score = -dy + Math.abs(dx) * 0.5
          break
        case 'down':
          inDirection = dy > threshold && Math.abs(dx) < Math.abs(dy)
          score = dy + Math.abs(dx) * 0.5
          break
        case 'left':
          inDirection = dx < -threshold && Math.abs(dy) < Math.abs(dx)
          score = -dx + Math.abs(dy) * 0.5
          break
        case 'right':
          inDirection = dx > threshold && Math.abs(dy) < Math.abs(dx)
          score = dx + Math.abs(dy) * 0.5
          break
      }

      if (inDirection && score < bestScore) {
        bestScore = score
        bestNode = node
      }
    }

    if (bestNode && selectNodeFn) {
      selectNodeFn(bestNode.id)
    }
  },

  selectNextNode: (getNodesFn, getSelectedNodeIdFn, selectNodeFn) => {
    const nodes = getNodesFn ? getNodesFn() : get().nodes
    const selectedNodeId = getSelectedNodeIdFn ? getSelectedNodeIdFn() : get().selectedNodeId
    const currentIndex = nodes.findIndex(n => n.id === selectedNodeId)
    if (currentIndex < nodes.length - 1 && selectNodeFn) {
      selectNodeFn(nodes[currentIndex + 1].id)
    }
  },

  selectPreviousNode: (getNodesFn, getSelectedNodeIdFn, selectNodeFn) => {
    const nodes = getNodesFn ? getNodesFn() : get().nodes
    const selectedNodeId = getSelectedNodeIdFn ? getSelectedNodeIdFn() : get().selectedNodeId
    const currentIndex = nodes.findIndex(n => n.id === selectedNodeId)
    if (currentIndex > 0 && selectNodeFn) {
      selectNodeFn(nodes[currentIndex - 1].id)
    }
  },

  editSelectedNode: (getSelectedNodeIdFn, startEditingNode) => {
    const selectedNodeId = getSelectedNodeIdFn ? getSelectedNodeIdFn() : get().selectedNodeId
    if (selectedNodeId && startEditingNode) {
      startEditingNode(selectedNodeId)
    }
  },

  deleteSelectedNode: (getSelectedNodeIdFn, deleteNode) => {
    const selectedNodeId = getSelectedNodeIdFn ? getSelectedNodeIdFn() : get().selectedNodeId
    if (selectedNodeId && deleteNode && confirm('Delete this node?')) {
      deleteNode(selectedNodeId)
    }
  },

  // ==================== CROSS-STORE SETTERS ====================
  setSelectedNodeId: (nodeId) => set({ selectedNodeId: nodeId }),
  setNodes: (nodes) => set({ nodes }),
  setBranches: (branches) => set({ branches }),
}))
