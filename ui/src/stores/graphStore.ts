import { create } from 'zustand'

// ==================== TYPES ====================

export type NodeType = 'chapter' | 'scene' | 'beat' | 'dialogue' | 'manga'

export interface SceneMetadata {
  title: string
  location: string
  timeOfDay: string
  estimatedReadingTime: number
  moodTags: string[]
  typeSpecific?: Record<string, unknown>
}

export interface NodeContent {
  text: string
  version: number
  lastModified: string
  wordCount: number
}

export interface NodeVersion {
  id: string
  content: string
  timestamp: string
  wordCount: number
}

export interface GraphNode {
  id: string
  label: string
  branchId: string
  sceneId: string
  x: number
  y: number
  importance: number
  type: NodeType
  content: NodeContent
  metadata: SceneMetadata
  versions: NodeVersion[]
  characters: string[]
}

export interface GraphEdge {
  source: string
  target: string
  type: 'causal' | 'temporal' | 'parallel'
  label?: string
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

export interface Viewport {
  x: number
  y: number
  width: number
  height: number
}

// ==================== GRAPH STATE ====================

export interface GraphState {
  // State
  nodes: GraphNode[]
  edges: GraphEdge[]
  selectedNodeId: string | null
  zoom: number
  viewport: Viewport
  branches: Branch[]
}

export interface GraphActions {
  // Actions
  addNode: (node: Partial<GraphNode>) => Promise<void>
  selectNode: (nodeId: string | null) => void
  deleteNode: (nodeId: string) => Promise<void>
  updateNodePosition: (nodeId: string, x: number, y: number) => void
  setZoom: (zoom: number) => void
  setViewport: (viewport: Viewport) => void
  navigateGraph: (direction: 'up' | 'down' | 'left' | 'right') => void
  undo: () => Promise<void>
  redo: () => Promise<void>
  createAutosave: (reason: string) => Promise<void>
  createBranch: (sourceNodeId: string, label: string, parentBranchId?: string) => Promise<void>
  archiveBranch: (branchId: string, reason: string) => Promise<void>
  mergeBranch: (sourceBranchId: string, targetBranchId: string) => Promise<void>
  previewBranchImpact: (nodeId: string) => Promise<{ descendantCount: number; divergenceScore: number; summary: string } | null>
  initialize: () => void
}

const API_BASE = '/api'

// ==================== STORE IMPLEMENTATION ====================

export const useGraphStore = create<GraphState & GraphActions>((set, get) => ({
  // ==================== INITIAL STATE ====================
  nodes: [],
  edges: [],
  selectedNodeId: null,
  zoom: 1,
  viewport: { x: 0, y: 0, width: 1200, height: 800 },
  branches: [],

  // ==================== INITIALIZATION ====================
  initialize: () => {
    // Fetch branches
    fetch(`${API_BASE}/branches`)
      .then(r => r.json())
      .then(branches => set({ branches }))
      .catch(console.error)
  },

  // ==================== GRAPH ACTIONS ====================
  addNode: async (nodeData) => {
    try {
      const newNode: GraphNode = {
        id: `node-${Date.now()}`,
        label: nodeData.label || 'New Node',
        branchId: nodeData.branchId || 'main',
        sceneId: nodeData.sceneId || 'default',
        x: nodeData.x ?? Math.random() * 400,
        y: nodeData.y ?? Math.random() * 300,
        importance: nodeData.importance ?? 0.5,
        type: nodeData.type || 'scene',
        content: {
          text: nodeData.content?.text || '',
          version: 1,
          lastModified: new Date().toISOString(),
          wordCount: 0,
        },
        metadata: {
          title: nodeData.metadata?.title || '',
          location: nodeData.metadata?.location || '',
          timeOfDay: nodeData.metadata?.timeOfDay || '',
          estimatedReadingTime: 0,
          moodTags: nodeData.metadata?.moodTags || [],
        },
        versions: [],
        characters: nodeData.characters || [],
      }

      const response = await fetch(`${API_BASE}/graph/nodes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newNode),
      })

      if (response.ok) {
        set(state => ({
          nodes: [...state.nodes, newNode],
          selectedNodeId: newNode.id,
        }))
      }
    } catch (error) {
      console.error('Failed to add node:', error)
    }
  },

  selectNode: (nodeId) => set({ selectedNodeId: nodeId }),

  deleteNode: async (nodeId) => {
    try {
      set(state => ({
        nodes: state.nodes.filter(n => n.id !== nodeId),
        selectedNodeId: state.selectedNodeId === nodeId ? null : state.selectedNodeId,
      }))
    } catch (error) {
      console.error('Failed to delete node:', error)
    }
  },

  updateNodePosition: (nodeId, x, y) => {
    set(state => ({
      nodes: state.nodes.map(n =>
        n.id === nodeId ? { ...n, x, y } : n
      ),
    }))
  },

  setZoom: (zoom) => {
    set({ zoom })
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
    } catch (error) {
      console.error('Undo failed:', error)
    }
  },

  redo: async () => {
    try {
      await fetch(`${API_BASE}/graph/redo`, { method: 'POST' })
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

  navigateGraph: (direction) => {
    const state = get()
    if (state.nodes.length === 0) return

    const currentId = state.selectedNodeId
    if (!currentId) {
      set({ selectedNodeId: state.nodes[0].id })
      return
    }

    const currentNode = state.nodes.find(n => n.id === currentId)
    if (!currentNode) return

    const threshold = 50
    let bestNode: GraphNode | null = null
    let bestScore = Infinity

    for (const node of state.nodes) {
      if (node.id === currentId) continue

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

    if (bestNode) {
      set({ selectedNodeId: bestNode.id })
    }
  },

  // ==================== BRANCH ACTIONS ====================
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
}))
