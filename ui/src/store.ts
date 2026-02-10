import { create } from 'zustand'

// ==================== TYPES ====================

export type NodeType = 'chapter' | 'scene' | 'beat' | 'dialogue'

export interface SceneMetadata {
  title: string
  location: string
  timeOfDay: string
  estimatedReadingTime: number
  moodTags: string[]
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
  // Phase A: Content management
  type: NodeType
  content: NodeContent
  metadata: SceneMetadata
  versions: NodeVersion[]
  characters: string[] // IDs of characters present
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

export interface Character {
  id: string
  name: string
  aliases: string[]
  traits: string[]
  description: string
  voiceProfile?: {
    speechPatterns: string[]
    vocabulary: string[]
    sampleQuotes: string[]
  }
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

export interface ReadingPreferences {
  fontSize: 'small' | 'medium' | 'large'
  theme: 'light' | 'dark' | 'sepia'
  lineSpacing: 'compact' | 'normal' | 'relaxed'
}

// ==================== APP STATE ====================

interface AppState {
  // Graph state
  nodes: GraphNode[]
  edges: GraphEdge[]
  selectedNodeId: string | null
  zoom: number
  viewport: { x: number; y: number; width: number; height: number }
  
  // Phase A: Content editing state
  editingNodeId: string | null
  showNodePreview: boolean
  
  // Phase A: Reading view
  readingMode: boolean
  readingBranchId: string | null
  readingNodeId: string | null
  readingPreferences: ReadingPreferences
  
  // Phase A: Characters
  characters: Character[]
  
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
  
  // ==================== ACTIONS ====================
  
  // Initialization
  initialize: () => void
  
  // Graph actions
  addNode: (node: Partial<GraphNode>) => Promise<void>
  selectNode: (nodeId: string | null) => void
  deleteNode: (nodeId: string) => Promise<void>
  updateNodePosition: (nodeId: string, x: number, y: number) => void
  setZoom: (zoom: number) => void
  setViewport: (viewport: { x: number; y: number; width: number; height: number }) => void
  undo: () => Promise<void>
  redo: () => Promise<void>
  createAutosave: (reason: string) => Promise<void>
  
  // Phase A: Content editing actions
  startEditingNode: (nodeId: string) => void
  stopEditingNode: () => void
  updateNodeContent: (nodeId: string, text: string) => Promise<void>
  updateNodeMetadata: (nodeId: string, metadata: Partial<SceneMetadata>) => Promise<void>
  updateNodeType: (nodeId: string, type: NodeType) => Promise<void>
  saveNodeVersion: (nodeId: string) => Promise<void>
  restoreNodeVersion: (nodeId: string, versionId: string) => Promise<void>
  toggleNodePreview: () => void
  
  // Phase A: Character management
  addCharacter: (character: Omit<Character, 'id'>) => Promise<void>
  updateCharacter: (characterId: string, updates: Partial<Character>) => Promise<void>
  deleteCharacter: (characterId: string) => Promise<void>
  toggleCharacterInNode: (nodeId: string, characterId: string) => Promise<void>
  
  // Phase A: Reading view actions
  toggleReadingMode: () => void
  enterReadingMode: (branchId: string, nodeId?: string) => void
  exitReadingMode: () => void
  navigateReading: (direction: 'prev' | 'next') => void
  jumpToNodeInReading: (nodeId: string) => void
  updateReadingPreferences: (prefs: Partial<ReadingPreferences>) => void
  
  // Phase A: Keyboard navigation
  navigateGraph: (direction: 'up' | 'down' | 'left' | 'right') => void
  selectNextNode: () => void
  selectPreviousNode: () => void
  editSelectedNode: () => void
  deleteSelectedNode: () => void
  
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
  
  // Error handling
  clearError: (key: 'nodes' | 'content') => void
}

const API_BASE = '/api'

// ==================== STORE IMPLEMENTATION ====================

export const useAppStore = create<AppState>((set, get) => ({
  // ==================== INITIAL STATE ====================
  nodes: [],
  edges: [],
  selectedNodeId: null,
  zoom: 1,
  viewport: { x: 0, y: 0, width: 1200, height: 800 },
  
  // Phase A: Content editing
  editingNodeId: null,
  showNodePreview: true,
  
  // Phase A: Reading view
  readingMode: false,
  readingBranchId: null,
  readingNodeId: null,
  readingPreferences: {
    fontSize: 'medium',
    theme: 'dark',
    lineSpacing: 'normal',
  },
  
  // Phase A: Characters
  characters: [],
  
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
  loading: { nodes: false, content: false, generation: false },
  error: { nodes: null, content: null },
  
  // ==================== INITIALIZATION ====================
  initialize: () => {
    // Set up keyboard shortcuts
    set({
      keyboardShortcuts: {
        'ctrl+z': () => get().undo(),
        'ctrl+y': () => get().redo(),
        'ctrl+t': () => get().toggleTuner(),
        'ctrl+d': () => get().toggleDualView(),
        'ctrl+s': () => get().createAutosave('manual'),
        'ctrl+?': () => alert('Shortcuts: Ctrl+Z=Undo, Ctrl+Y=Redo, Ctrl+T=Tuner, Ctrl+D=Dual View, Ctrl+S=Save, Ctrl+N=New Node, Enter=Edit, Delete=Delete, Arrows=Navigate'),
        'ctrl+n': () => {
          const state = get()
          if (state.selectedNodeId) {
            const node = state.nodes.find(n => n.id === state.selectedNodeId)
            if (node) {
              get().addNode({
                label: 'New Node',
                branchId: node.branchId,
                sceneId: node.sceneId,
                x: node.x + 50,
                y: node.y + 50,
                importance: 0.5,
              })
            }
          }
        },
        'enter': () => get().editSelectedNode(),
        'delete': () => get().deleteSelectedNode(),
        'arrowup': () => get().navigateGraph('up'),
        'arrowdown': () => get().navigateGraph('down'),
        'arrowleft': () => get().navigateGraph('left'),
        'arrowright': () => get().navigateGraph('right'),
        'escape': () => {
          if (get().editingNodeId) {
            get().stopEditingNode()
          } else if (get().readingMode) {
            get().exitReadingMode()
          } else if (get().selectedNodeId) {
            get().selectNode(null)
          }
        },
      }
    })
    
    // Load initial data
    get().refreshMetrics()
    
    // Fetch branches
    fetch(`${API_BASE}/branches`)
      .then(r => r.json())
      .then(branches => set({ branches }))
      .catch(console.error)
    
    // Load sample characters for demo
    set({
      characters: [
        {
          id: 'char-1',
          name: 'Protagonist',
          aliases: ['Hero', 'MC'],
          traits: ['brave', 'determined'],
          description: 'The main character of the story',
        },
        {
          id: 'char-2',
          name: 'Antagonist',
          aliases: ['Villain'],
          traits: ['cunning', 'ruthless'],
          description: 'The opposing force',
        },
      ]
    })
  },
  
  // ==================== GRAPH ACTIONS ====================
  addNode: async (nodeData) => {
    set(state => ({ loading: { ...state.loading, nodes: true } }))
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
        await get().refreshMetrics()
      }
    } catch (error) {
      console.error('Failed to add node:', error)
      set(state => ({ error: { ...state.error, nodes: 'Failed to add node' } }))
    } finally {
      set(state => ({ loading: { ...state.loading, nodes: false } }))
    }
  },
  
  selectNode: (nodeId) => set({ selectedNodeId: nodeId }),
  
  deleteNode: async (nodeId) => {
    try {
      // In a real implementation, this would call the API
      set(state => ({
        nodes: state.nodes.filter(n => n.id !== nodeId),
        selectedNodeId: state.selectedNodeId === nodeId ? null : state.selectedNodeId,
      }))
      await get().refreshMetrics()
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
  
  // ==================== PHASE A: CONTENT EDITING ====================
  startEditingNode: (nodeId) => set({ editingNodeId: nodeId }),
  stopEditingNode: () => set({ editingNodeId: null }),
  
  updateNodeContent: async (nodeId, text) => {
    set(state => ({ loading: { ...state.loading, content: true } }))
    try {
      const wordCount = text.trim().split(/\s+/).filter(w => w.length > 0).length
      
      set(state => ({
        nodes: state.nodes.map(n =>
          n.id === nodeId
            ? {
                ...n,
                content: {
                  text,
                  version: n.content.version + 1,
                  lastModified: new Date().toISOString(),
                  wordCount,
                },
              }
            : n
        ),
      }))
    } catch (error) {
      console.error('Failed to update content:', error)
      set(state => ({ error: { ...state.error, content: 'Failed to save content' } }))
    } finally {
      set(state => ({ loading: { ...state.loading, content: false } }))
    }
  },
  
  updateNodeMetadata: async (nodeId, metadata) => {
    set(state => ({
      nodes: state.nodes.map(n =>
        n.id === nodeId
          ? { ...n, metadata: { ...n.metadata, ...metadata } }
          : n
      ),
    }))
  },
  
  updateNodeType: async (nodeId, type) => {
    set(state => ({
      nodes: state.nodes.map(n =>
        n.id === nodeId ? { ...n, type } : n
      ),
    }))
  },
  
  saveNodeVersion: async (nodeId) => {
    const node = get().nodes.find(n => n.id === nodeId)
    if (!node) return
    
    const newVersion: NodeVersion = {
      id: `v-${Date.now()}`,
      content: node.content.text,
      timestamp: new Date().toISOString(),
      wordCount: node.content.wordCount,
    }
    
    set(state => ({
      nodes: state.nodes.map(n =>
        n.id === nodeId
          ? { ...n, versions: [...n.versions.slice(-9), newVersion] }
          : n
      ),
    }))
  },
  
  restoreNodeVersion: async (nodeId, versionId) => {
    const node = get().nodes.find(n => n.id === nodeId)
    if (!node) return
    
    const version = node.versions.find(v => v.id === versionId)
    if (!version) return
    
    set(state => ({
      nodes: state.nodes.map(n =>
        n.id === nodeId
          ? {
              ...n,
              content: {
                text: version.content,
                version: n.content.version + 1,
                lastModified: new Date().toISOString(),
                wordCount: version.wordCount,
              },
            }
          : n
      ),
    }))
  },
  
  toggleNodePreview: () => set(state => ({ showNodePreview: !state.showNodePreview })),
  
  // ==================== PHASE A: CHARACTER MANAGEMENT ====================
  addCharacter: async (character) => {
    const newChar: Character = {
      ...character,
      id: `char-${Date.now()}`,
    }
    set(state => ({ characters: [...state.characters, newChar] }))
  },
  
  updateCharacter: async (characterId, updates) => {
    set(state => ({
      characters: state.characters.map(c =>
        c.id === characterId ? { ...c, ...updates } : c
      ),
    }))
  },
  
  deleteCharacter: async (characterId) => {
    set(state => ({
      characters: state.characters.filter(c => c.id !== characterId),
      nodes: state.nodes.map(n => ({
        ...n,
        characters: n.characters.filter(id => id !== characterId),
      })),
    }))
  },
  
  toggleCharacterInNode: async (nodeId, characterId) => {
    set(state => ({
      nodes: state.nodes.map(n => {
        if (n.id !== nodeId) return n
        const hasChar = n.characters.includes(characterId)
        return {
          ...n,
          characters: hasChar
            ? n.characters.filter(id => id !== characterId)
            : [...n.characters, characterId],
        }
      }),
    }))
  },
  
  // ==================== PHASE A: READING VIEW ====================
  toggleReadingMode: () => {
    const state = get()
    if (!state.readingMode) {
      // Enter reading mode on current branch/node
      const branchId = state.branches.find(b => b.status === 'active')?.branchId || 'main'
      const nodeId = state.selectedNodeId || state.nodes[0]?.id || null
      get().enterReadingMode(branchId, nodeId || undefined)
    } else {
      get().exitReadingMode()
    }
  },
  
  enterReadingMode: (branchId, nodeId) => {
    set({
      readingMode: true,
      readingBranchId: branchId,
      readingNodeId: nodeId || get().nodes.find(n => n.branchId === branchId)?.id || null,
    })
  },
  
  exitReadingMode: () => {
    set({
      readingMode: false,
      readingBranchId: null,
      readingNodeId: null,
    })
  },
  
  navigateReading: (direction) => {
    const state = get()
    if (!state.readingNodeId) return
    
    const currentIndex = state.nodes.findIndex(n => n.id === state.readingNodeId)
    if (currentIndex === -1) return
    
    const newIndex = direction === 'next'
      ? Math.min(currentIndex + 1, state.nodes.length - 1)
      : Math.max(currentIndex - 1, 0)
    
    set({ readingNodeId: state.nodes[newIndex].id })
  },
  
  jumpToNodeInReading: (nodeId) => {
    set({ readingNodeId: nodeId })
  },
  
  updateReadingPreferences: (prefs) => {
    set(state => ({
      readingPreferences: { ...state.readingPreferences, ...prefs },
    }))
  },
  
  // ==================== PHASE A: KEYBOARD NAVIGATION ====================
  navigateGraph: (direction) => {
    const state = get()
    if (state.nodes.length === 0) return
    
    const currentId = state.selectedNodeId
    if (!currentId) {
      // Select first node if none selected
      set({ selectedNodeId: state.nodes[0].id })
      return
    }
    
    const currentNode = state.nodes.find(n => n.id === currentId)
    if (!currentNode) return
    
    // Find nearest node in the direction
    const threshold = 50 // minimum distance
    let bestNode: GraphNode | null = null
    let bestScore = Infinity
    
    for (const node of state.nodes) {
      if (node.id === currentId) continue
      
      const dx = node.x - currentNode.x
      const dy = node.y - currentNode.y
      const distance = Math.sqrt(dx * dx + dy * dy)
      
      let score = distance
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
  
  selectNextNode: () => {
    const state = get()
    const currentIndex = state.nodes.findIndex(n => n.id === state.selectedNodeId)
    if (currentIndex < state.nodes.length - 1) {
      set({ selectedNodeId: state.nodes[currentIndex + 1].id })
    }
  },
  
  selectPreviousNode: () => {
    const state = get()
    const currentIndex = state.nodes.findIndex(n => n.id === state.selectedNodeId)
    if (currentIndex > 0) {
      set({ selectedNodeId: state.nodes[currentIndex - 1].id })
    }
  },
  
  editSelectedNode: () => {
    const state = get()
    if (state.selectedNodeId) {
      get().startEditingNode(state.selectedNodeId)
    }
  },
  
  deleteSelectedNode: () => {
    const state = get()
    if (state.selectedNodeId && confirm('Delete this node?')) {
      get().deleteNode(state.selectedNodeId)
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
  
  // ==================== TUNER ACTIONS ====================
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
  
  // ==================== DUAL VIEW ACTIONS ====================
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
  ingestFile: async (file: File) => {
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
  
  // ==================== ERROR HANDLING ====================
  clearError: (key) => {
    set(state => ({ error: { ...state.error, [key]: null } }))
  },
}))
