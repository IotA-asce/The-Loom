import { create } from 'zustand'

// Types
export interface GraphNode {
  id: string
  label: string
  branchId: string
  sceneId: string
  x: number
  y: number
  importance: number
}

export interface GraphEdge {
  source: string
  target: string
  type: string
}

export interface Branch {
  branchId: string
  parentBranchId: string | null
  sourceNodeId: string
  label: string
  status: 'active' | 'archived' | 'merged'
  lineage: string[]
  createdAt: string
}

export interface TunerSettings {
  violence: number
  humor: number
  romance: number
}

export interface TunerResolution extends TunerSettings {
  warnings: string[]
  precedenceOrder: string[]
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

interface AppState {
  // Graph state
  nodes: GraphNode[]
  edges: GraphEdge[]
  selectedNodeId: string | null
  zoom: number
  viewport: { x: number; y: number; width: number; height: number }
  
  // Branch state
  branches: Branch[]
  
  // Tuner state
  tunerSettings: TunerSettings
  tunerResolution: TunerResolution | null
  tunerOpen: boolean
  
  // Dual view state
  dualViewOpen: boolean
  syncState: SyncState | null
  
  // Metrics
  graphMetrics: GraphMetrics | null
  phase8Metrics: Phase8Metrics | null
  
  // Import
  supportedFormats: { text: string[]; manga: string[]; images: string[] }
  
  // Keyboard shortcuts
  keyboardShortcuts: Record<string, () => void>
  
  // Actions
  initialize: () => void
  addNode: (node: Omit<GraphNode, 'id'>) => Promise<void>
  selectNode: (nodeId: string | null) => void
  setZoom: (zoom: number) => void
  setViewport: (viewport: { x: number; y: number; width: number; height: number }) => void
  undo: () => Promise<void>
  redo: () => Promise<void>
  createAutosave: (reason: string) => Promise<void>
  
  // Branch actions
  createBranch: (sourceNodeId: string, label: string, parentBranchId?: string) => Promise<void>
  archiveBranch: (branchId: string, reason: string) => Promise<void>
  mergeBranch: (sourceBranchId: string, targetBranchId: string) => Promise<void>
  previewBranchImpact: (nodeId: string) => Promise<{ descendantCount: number; divergenceScore: number; summary: string } | null>
  
  // Tuner actions
  toggleTuner: () => void
  updateTuner: (settings: TunerSettings) => Promise<void>
  
  // Dual view actions
  toggleDualView: () => void
  initializeDualView: (sceneId: string) => Promise<void>
  editSentence: (sceneId: string, sentenceIndex: number, previousText: string, newText: string) => Promise<void>
  requestPanelRedraw: (sceneId: string, panelIndex: number, reason: string) => Promise<void>
  reconcile: (sceneId: string, textVersion: string, imageVersion: string) => Promise<void>
  
  // Metrics
  refreshMetrics: () => Promise<void>
  
  // Import actions
  ingestFile: (file: File) => Promise<{ success: boolean; [key: string]: any }>
}

const API_BASE = '/api'

export const useAppStore = create<AppState>((set, get) => ({
  // Initial state
  nodes: [],
  edges: [],
  selectedNodeId: null,
  zoom: 1,
  viewport: { x: 0, y: 0, width: 1200, height: 800 },
  branches: [],
  tunerSettings: { violence: 0.5, humor: 0.5, romance: 0.5 },
  tunerResolution: null,
  tunerOpen: false,
  dualViewOpen: false,
  syncState: null,
  graphMetrics: null,
  phase8Metrics: null,
  supportedFormats: { text: ['.txt', '.pdf', '.epub'], manga: ['.cbz', '.zip'], images: ['.png', '.jpg', '.jpeg', '.webp'] },
  keyboardShortcuts: {},
  
  // Initialize
  initialize: () => {
    // Set up keyboard shortcuts
    set({
      keyboardShortcuts: {
        'ctrl+z': () => get().undo(),
        'ctrl+y': () => get().redo(),
        'ctrl+t': () => get().toggleTuner(),
        'ctrl+d': () => get().toggleDualView(),
        'ctrl+s': () => get().createAutosave('manual'),
      }
    })
    
    // Load initial data
    get().refreshMetrics()
    
    // Fetch branches
    fetch(`${API_BASE}/branches`)
      .then(r => r.json())
      .then(branches => set({ branches }))
      .catch(console.error)
  },
  
  // Graph actions
  addNode: async (node) => {
    try {
      const response = await fetch(`${API_BASE}/graph/nodes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(node),
      })
      if (response.ok) {
        const result = await response.json()
        set(state => ({
          nodes: [...state.nodes, { ...node, id: result.node_id }]
        }))
        await get().refreshMetrics()
      }
    } catch (error) {
      console.error('Failed to add node:', error)
    }
  },
  
  selectNode: (nodeId) => set({ selectedNodeId: nodeId }),
  
  setZoom: (zoom) => {
    set({ zoom })
    // Update viewport on backend
    const { viewport } = get()
    fetch(`${API_BASE}/graph/viewport`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...viewport, zoom }),
    }).catch(console.error)
  },
  
  setViewport: (viewport) => {
    set({ viewport })
    fetch(`${API_BASE}/graph/viewport`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...viewport, zoom: get().zoom }),
    }).catch(console.error)
  },
  
  undo: async () => {
    try {
      await fetch(`${API_BASE}/graph/undo`, { method: 'POST' })
      await get().refreshMetrics()
    } catch (error) {
      console.error('Undo failed:', error)
    }
  },
  
  redo: async () => {
    try {
      await fetch(`${API_BASE}/graph/redo`, { method: 'POST' })
      await get().refreshMetrics()
    } catch (error) {
      console.error('Redo failed:', error)
    }
  },
  
  createAutosave: async (reason) => {
    try {
      await fetch(`${API_BASE}/graph/autosave?reason=${encodeURIComponent(reason)}`, { method: 'POST' })
    } catch (error) {
      console.error('Autosave failed:', error)
    }
  },
  
  // Branch actions
  createBranch: async (sourceNodeId, label, parentBranchId = 'main') => {
    try {
      const response = await fetch(`${API_BASE}/branches`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sourceNodeId, label, parentBranchId }),
      })
      if (response.ok) {
        const result = await response.json()
        set(state => ({
          branches: [...state.branches, {
            branchId: result.branchId,
            parentBranchId,
            sourceNodeId,
            label,
            status: 'active',
            lineage: result.lineage,
            createdAt: new Date().toISOString(),
          }]
        }))
      }
    } catch (error) {
      console.error('Failed to create branch:', error)
    }
  },
  
  archiveBranch: async (branchId, reason) => {
    try {
      await fetch(`${API_BASE}/branches/archive`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ branchId, reason }),
      })
      set(state => ({
        branches: state.branches.map(b => 
          b.branchId === branchId ? { ...b, status: 'archived' as const } : b
        )
      }))
    } catch (error) {
      console.error('Failed to archive branch:', error)
    }
  },
  
  mergeBranch: async (sourceBranchId, targetBranchId) => {
    try {
      await fetch(`${API_BASE}/branches/merge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sourceBranchId, targetBranchId }),
      })
      set(state => ({
        branches: state.branches.map(b => 
          b.branchId === sourceBranchId ? { ...b, status: 'merged' as const } : b
        )
      }))
    } catch (error) {
      console.error('Failed to merge branch:', error)
    }
  },
  
  previewBranchImpact: async (nodeId) => {
    try {
      const response = await fetch(`${API_BASE}/branches/impact/${encodeURIComponent(nodeId)}`)
      if (response.ok) {
        return await response.json()
      }
    } catch (error) {
      console.error('Failed to preview impact:', error)
    }
    return null
  },
  
  // Tuner actions
  toggleTuner: () => set(state => ({ tunerOpen: !state.tunerOpen })),
  
  updateTuner: async (settings) => {
    set({ tunerSettings: settings })
    try {
      const response = await fetch(`${API_BASE}/tuner/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      })
      if (response.ok) {
        const result = await response.json()
        set({
          tunerResolution: {
            violence: result.resolvedSettings.violence,
            humor: result.resolvedSettings.humor,
            romance: result.resolvedSettings.romance,
            warnings: result.warnings,
            precedenceOrder: result.precedenceOrder,
          }
        })
      }
    } catch (error) {
      console.error('Failed to update tuner:', error)
    }
  },
  
  // Dual view actions
  toggleDualView: () => set(state => ({ dualViewOpen: !state.dualViewOpen })),
  
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
  
  // Metrics
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
  
  // Import actions
  ingestFile: async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    
    // Determine endpoint based on file type
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
        // Refresh metrics after successful import
        get().refreshMetrics()
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
}))
