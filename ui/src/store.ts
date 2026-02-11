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
  importance?: number
  appearanceCount?: number
  voiceProfile?: {
    speechPatterns: string[]
    vocabulary: string[]
    sampleQuotes: string[]
  }
  voiceEnforced?: boolean
  focusMode?: boolean
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

// Phase B: Generation types
export interface ContextChunk {
  id: string
  text: string
  relevanceScore: number
  source: string
  branchId: string
  pinned?: boolean
  expanded?: boolean
  tokenCount?: number
}

export interface ContextPreset {
  id: string
  name: string
  chunkIds: string[]
  createdAt: string
}

export interface StyleExemplar {
  id: string
  text: string
  similarityScore: number
  features: string[]
  selected?: boolean
  isStyleGuide?: boolean
}

export interface StyleProfile {
  name: string
  confidence: number
  attributes: Record<string, number>
}

export interface GenerationRequest {
  nodeId: string
  userPrompt: string
  temperature: number
  maxTokens: number
  contextChunks: string[] // IDs of selected chunks
  styleExemplars: string[] // IDs of selected exemplars
  characterIds: string[] // IDs of characters to include
  tunerSettings: TunerSettings
}

export interface GenerationResult {
  id: string
  generatedText: string
  wordCount: number
  timestamp: string
  requestId: string
  appliedSettings: {
    tuner: TunerSettings
    contextCount: number
    exemplarCount: number
  }
}

export interface Contradiction {
  severity: 'low' | 'medium' | 'high'
  type: string
  description: string
  suggestedFix: string
}

// Phase C: Image Generation types
export interface SceneBlueprint {
  setting: string
  timeOfDay: string
  weather: string
  lightingDirection: string
  lightingIntensity: number
  shotType: string
  cameraAngle: string
  focusPoint: string
  props: string[]
  characters: Array<{
    characterId: string
    position: 'left' | 'center' | 'right' | 'background'
    pose: string
    expression: string
  }>
}

export interface AtmosphereSettings {
  presetId: string
  direction: string
  intensity: number
  contrast: number
  shadowHardness: number
  textureDetail: number
  textureStyle: 'clean' | 'gritty'
  weathering: number
}

export interface GeneratedPanel {
  id: string
  nodeId: string
  url: string | null
  seed: number
  status: 'pending' | 'generating' | 'completed' | 'failed'
  createdAt: string
}

export interface GenerationQueueItem {
  id: string
  nodeId: string
  panelCount: number
  aspectRatio: string
  status: 'pending' | 'processing' | 'completed' | 'cancelled'
}

export interface ActiveGeneration {
  id: string
  progress: number
  currentStep: string
  eta: number
}

export interface ContinuityIssue {
  panelId: string
  severity: 'low' | 'medium' | 'high'
  message: string
  type: 'character_drift' | 'lighting_mismatch' | 'pose_inconsistency'
}

// Phase D: Search types
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

// Phase E: Simulator types
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

export interface Toast {
  id: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  duration?: number
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
  
  // Phase B: Generation state
  writerPanelOpen: boolean
  contextChunks: ContextChunk[]
  styleExemplars: StyleExemplar[]
  generationResults: GenerationResult[]
  currentGeneration: GenerationResult | null
  generationParams: {
    temperature: number
    maxTokens: number
    userPrompt: string
    contextWindow: number
    model: string
  }
  contextPresets: ContextPreset[]
  activePresetId: string | null
  contradictions: Contradiction[]
  expandedContradictions: string[] // IDs of expanded contradiction details
  styleProfile: StyleProfile | null
  
  // Phase C: Image Generation state
  artistPanelOpen: boolean
  sceneBlueprints: Record<string, SceneBlueprint>
  atmosphereSettings: AtmosphereSettings
  generatedPanels: GeneratedPanel[]
  generationQueue: GenerationQueueItem[]
  activeGeneration: ActiveGeneration | null
  viewerMode: 'grid' | 'sequential' | 'split'
  selectedPanelId: string | null
  continuityIssues: ContinuityIssue[]
  
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
  
  // Toast notifications
  toasts: Toast[]
  
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
  
  // Phase B: Generation actions
  toggleWriterPanel: () => void
  retrieveContext: (query: string, branchId: string) => Promise<void>
  toggleContextChunk: (chunkId: string) => void
  expandContextChunk: (chunkId: string, expanded: boolean) => void
  removeContextChunk: (chunkId: string) => void
  reorderContextChunks: (chunkIds: string[]) => void
  retrieveStyleExemplars: (queryText: string) => Promise<void>
  toggleStyleExemplar: (exemplarId: string) => void
  setStyleGuide: (exemplarId: string) => void
  generateText: (request: Partial<GenerationRequest>) => Promise<void>
  cancelGeneration: () => void
  acceptGeneration: (generationId: string) => void
  rejectGeneration: (generationId: string) => void
  checkContradictions: (generatedText: string) => Promise<void>
  expandContradiction: (contradictionId: string, expanded: boolean) => void
  updateGenerationParams: (params: Partial<AppState['generationParams']>) => void
  
  // Context presets
  saveContextPreset: (name: string) => void
  loadContextPreset: (presetId: string) => void
  deleteContextPreset: (presetId: string) => void
  
  // Character voice management
  toggleVoiceEnforcement: (characterId: string) => void
  toggleCharacterFocus: (characterId: string) => void
  filterCharacters: (query: string) => Character[]
  sortCharacters: (by: 'name' | 'importance' | 'appearance') => void
  
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
  
  // Toast notifications
  addToast: (toast: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void
  
  // Inline editing
  editGenerationInline: (generationId: string, newText: string) => void
  
  // Phase C: Image Generation actions
  toggleArtistPanel: () => void
  createSceneBlueprint: (nodeId: string, blueprint: SceneBlueprint) => void
  updateSceneBlueprint: (nodeId: string, updates: Partial<SceneBlueprint>) => void
  setAtmospherePreset: (presetId: string) => void
  updateAtmosphereSettings: (settings: Partial<AtmosphereSettings>) => void
  generatePanels: (request: { nodeId: string; blueprint: SceneBlueprint; atmosphere: AtmosphereSettings; params: Record<string, unknown> }) => Promise<void>
  cancelPanelGeneration: () => void
  queuePanelGeneration: (request: Omit<GenerationQueueItem, 'id' | 'status'>) => void
  deleteGeneratedPanel: (panelId: string) => void
  regeneratePanel: (panelId: string) => void
  setViewerMode: (mode: 'grid' | 'sequential' | 'split') => void
  selectPanel: (panelId: string | null) => void
  
  // Manga Storage
  mangaVolumes: Array<{
    volume_id: string
    title: string
    page_count: number
    source_hash: string
    graph_node_id?: string
    created_at: string
  }>
  fetchMangaVolumes: () => Promise<void>
  deleteMangaVolume: (volume_id: string) => Promise<boolean>
  
  // Graph Persistence
  loadGraphNodes: () => Promise<void>
  
  // Phase D: Search & Memory
  searchPanelOpen: boolean
  toggleSearchPanel: () => void
  performSearch: (query: string, filters: Record<string, string>) => Promise<SearchResult[]>
  addToContext: (resultId: string) => void
  searchResults: SearchResult[]
  memoryBrowserOpen: boolean
  toggleMemoryBrowser: () => void
  
  // Phase E: Consequence Simulator
  simulatorOpen: boolean
  toggleSimulator: () => void
  simulateChange: (request: { nodeId: string; changeType: string; description: string }) => Promise<SimulationResult>
  
  // Phase F: Tone Analysis
  toneHeatmapOpen: boolean
  toggleToneHeatmap: () => void
  
  // Sprint 11: WebSocket & Real-time
  wsConnection: WebSocket | null
  wsConnected: boolean
  generationProgress: { jobId: string; step: string; label: string; progress: number } | null
  subscribeToJob: (jobId: string) => void
  initializeWebSocket: () => void
  closeWebSocket: () => void
  
  // Sprint 12: Navigation History
  recentNodes: string[]
  navigationHistory: string[]
  historyIndex: number
  addToRecentNodes: (nodeId: string) => void
  navigateHistory: (direction: 'back' | 'forward') => void
  clearHistory: () => void
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
  
  // Phase B: Generation state
  writerPanelOpen: false,
  contextChunks: [],
  styleExemplars: [],
  generationResults: [],
  currentGeneration: null,
  generationParams: {
    temperature: 0.7,
    maxTokens: 500,
    userPrompt: '',
    contextWindow: 4096,
    model: 'default',
  },
  contextPresets: [],
  activePresetId: null,
  contradictions: [],
  expandedContradictions: [],
  styleProfile: null,
  
  // Phase C: Image Generation initial state
  artistPanelOpen: false,
  sceneBlueprints: {},
  atmosphereSettings: {
    presetId: 'neutral',
    direction: 'top',
    intensity: 0.6,
    contrast: 0.5,
    shadowHardness: 0.5,
    textureDetail: 0.6,
    textureStyle: 'clean' as const,
    weathering: 0.3,
  },
  generatedPanels: [],
  generationQueue: [],
  activeGeneration: null,
  viewerMode: 'grid',
  selectedPanelId: null,
  continuityIssues: [],
  
  // Phase D: Search & Memory state
  searchPanelOpen: false,
  searchResults: [],
  memoryBrowserOpen: false,
  
  // Phase E: Simulator state
  simulatorOpen: false,
  
  // Phase F: Tone Analysis state
  toneHeatmapOpen: false,
  
  // Sprint 11: WebSocket state
  wsConnection: null,
  wsConnected: false,
  generationProgress: null,
  
  // Sprint 12: Navigation History state
  recentNodes: [],
  navigationHistory: [],
  historyIndex: -1,
  
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
  toasts: [],
  
  // ==================== INITIALIZATION ====================
  initialize: async () => {
    // Load existing graph nodes
    await get().loadGraphNodes()
    
    // Initialize WebSocket connection
    get().initializeWebSocket()
    
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
  
  selectNode: (nodeId) => {
    set({ selectedNodeId: nodeId })
    if (nodeId) {
      get().addToRecentNodes(nodeId)
    }
  },
  
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
  
  // ==================== PHASE B: TEXT GENERATION ====================
  toggleWriterPanel: () => set(state => ({ writerPanelOpen: !state.writerPanelOpen })),
  
  retrieveContext: async (query, branchId) => {
    set(state => ({ loading: { ...state.loading, generation: true } }))
    try {
      const response = await fetch(`${API_BASE}/retrieve/context`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, branchId, topK: 6 }),
      })
      if (response.ok) {
        const result = await response.json()
        set({ contextChunks: result.chunks })
      }
    } catch (error) {
      console.error('Failed to retrieve context:', error)
    } finally {
      set(state => ({ loading: { ...state.loading, generation: false } }))
    }
  },
  
  toggleContextChunk: (chunkId) => {
    set(state => ({
      contextChunks: state.contextChunks.map(c =>
        c.id === chunkId ? { ...c, pinned: !c.pinned } : c
      ),
    }))
  },
  
  reorderContextChunks: (chunkIds) => {
    set(state => ({
      contextChunks: chunkIds
        .map(id => state.contextChunks.find(c => c.id === id))
        .filter(Boolean) as ContextChunk[],
    }))
  },
  
  retrieveStyleExemplars: async (queryText) => {
    try {
      const response = await fetch(`${API_BASE}/retrieve/style-exemplars`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ queryText, topK: 3 }),
      })
      if (response.ok) {
        const result = await response.json()
        set({ styleExemplars: result.exemplars })
      }
    } catch (error) {
      console.error('Failed to retrieve style exemplars:', error)
    }
  },
  
  toggleStyleExemplar: (exemplarId) => {
    set(state => ({
      styleExemplars: state.styleExemplars.map(e =>
        e.id === exemplarId ? { ...e, selected: !e.selected } : e
      ),
    }))
  },
  
  generateText: async (request) => {
    const state = get()
    set(state => ({ loading: { ...state.loading, generation: true } }))
    
    try {
      const payload = {
        nodeId: request.nodeId || state.selectedNodeId,
        userPrompt: request.userPrompt || state.generationParams.userPrompt,
        temperature: request.temperature || state.generationParams.temperature,
        maxTokens: request.maxTokens || state.generationParams.maxTokens,
        context: state.contextChunks.filter(c => c.pinned).map(c => c.id),
        styleExemplars: state.styleExemplars.filter(e => e.selected).map(e => e.id),
        characterIds: state.nodes.find(n => n.id === (request.nodeId || state.selectedNodeId))?.characters || [],
        tuner: state.tunerSettings,
      }
      
      const response = await fetch(`${API_BASE}/generate/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      
      if (response.ok) {
        const result = await response.json()
        const generation: GenerationResult = {
          id: `gen-${Date.now()}`,
          generatedText: result.generatedText,
          wordCount: result.wordCount,
          timestamp: new Date().toISOString(),
          requestId: result.requestId,
          appliedSettings: {
            tuner: result.tunerApplied,
            contextCount: result.contextUsed,
            exemplarCount: payload.styleExemplars.length,
          },
        }
        
        set(state => ({
          generationResults: [generation, ...state.generationResults],
          currentGeneration: generation,
        }))
        
        // Auto-check for contradictions
        await get().checkContradictions(result.generatedText)
      }
    } catch (error) {
      console.error('Failed to generate text:', error)
      set(state => ({
        error: { ...state.error, content: 'Generation failed' },
      }))
    } finally {
      set(state => ({ loading: { ...state.loading, generation: false } }))
    }
  },
  
  acceptGeneration: (generationId) => {
    const state = get()
    const generation = state.generationResults.find(g => g.id === generationId)
    if (generation && state.selectedNodeId) {
      get().updateNodeContent(state.selectedNodeId, generation.generatedText)
    }
  },
  
  rejectGeneration: (generationId) => {
    set(state => ({
      generationResults: state.generationResults.filter(g => g.id !== generationId),
      currentGeneration: state.currentGeneration?.id === generationId 
        ? null 
        : state.currentGeneration,
    }))
  },
  
  checkContradictions: async (generatedText) => {
    try {
      const response = await fetch(`${API_BASE}/check/contradictions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ generatedText }),
      })
      if (response.ok) {
        const result = await response.json()
        set({ contradictions: result.contradictions })
      }
    } catch (error) {
      console.error('Failed to check contradictions:', error)
    }
  },
  
  updateGenerationParams: (params) => {
    set(state => ({
      generationParams: { ...state.generationParams, ...params },
    }))
  },
  
  // ==================== PHASE B: CONTEXT MANAGEMENT ====================
  expandContextChunk: (chunkId, expanded) => {
    set(state => ({
      contextChunks: state.contextChunks.map(c =>
        c.id === chunkId ? { ...c, expanded } : c
      ),
    }))
  },
  
  removeContextChunk: (chunkId) => {
    set(state => ({
      contextChunks: state.contextChunks.filter(c => c.id !== chunkId),
    }))
  },
  
  // ==================== PHASE B: STYLE MANAGEMENT ====================
  setStyleGuide: (exemplarId) => {
    set(state => ({
      styleExemplars: state.styleExemplars.map(e =>
        e.id === exemplarId ? { ...e, isStyleGuide: !e.isStyleGuide } : { ...e, isStyleGuide: false }
      ),
    }))
  },
  
  // ==================== PHASE B: GENERATION CONTROL ====================
  cancelGeneration: () => {
    set(state => ({
      loading: { ...state.loading, generation: false },
    }))
  },
  
  // ==================== PHASE B: CONTRADICTION MANAGEMENT ====================
  expandContradiction: (contradictionId, expanded) => {
    set(state => ({
      expandedContradictions: expanded
        ? [...state.expandedContradictions, contradictionId]
        : state.expandedContradictions.filter(id => id !== contradictionId),
    }))
  },
  
  // ==================== PHASE B: CONTEXT PRESETS ====================
  saveContextPreset: (name) => {
    const state = get()
    const newPreset: ContextPreset = {
      id: `preset-${Date.now()}`,
      name,
      chunkIds: state.contextChunks.filter(c => c.pinned).map(c => c.id),
      createdAt: new Date().toISOString(),
    }
    set(state => ({
      contextPresets: [...state.contextPresets, newPreset],
    }))
  },
  
  loadContextPreset: (presetId) => {
    const state = get()
    const preset = state.contextPresets.find(p => p.id === presetId)
    if (!preset) return
    
    set(state => ({
      contextChunks: state.contextChunks.map(c => ({
        ...c,
        pinned: preset.chunkIds.includes(c.id),
      })),
      activePresetId: presetId,
    }))
  },
  
  deleteContextPreset: (presetId) => {
    set(state => ({
      contextPresets: state.contextPresets.filter(p => p.id !== presetId),
      activePresetId: state.activePresetId === presetId ? null : state.activePresetId,
    }))
  },
  
  // ==================== PHASE B: CHARACTER VOICE MANAGEMENT ====================
  toggleVoiceEnforcement: (characterId) => {
    set(state => ({
      characters: state.characters.map(c =>
        c.id === characterId ? { ...c, voiceEnforced: !c.voiceEnforced } : c
      ),
    }))
  },
  
  toggleCharacterFocus: (characterId) => {
    set(state => ({
      characters: state.characters.map(c =>
        c.id === characterId ? { ...c, focusMode: !c.focusMode } : { ...c, focusMode: false }
      ),
    }))
  },
  
  filterCharacters: (query) => {
    const state = get()
    if (!query.trim()) return state.characters
    const lower = query.toLowerCase()
    return state.characters.filter(c =>
      c.name.toLowerCase().includes(lower) ||
      c.aliases.some(a => a.toLowerCase().includes(lower))
    )
  },
  
  sortCharacters: (by) => {
    set(state => ({
      characters: [...state.characters].sort((a, b) => {
        switch (by) {
          case 'name':
            return a.name.localeCompare(b.name)
          case 'importance':
            return (b.importance || 0) - (a.importance || 0)
          case 'appearance':
            return (b.appearanceCount || 0) - (a.appearanceCount || 0)
          default:
            return 0
        }
      }),
    }))
  },
  
  // ==================== PHASE B: INLINE EDITING ====================
  editGenerationInline: (generationId, newText) => {
    set(state => ({
      generationResults: state.generationResults.map(g =>
        g.id === generationId
          ? { ...g, generatedText: newText, wordCount: newText.split(/\s+/).filter(w => w.length > 0).length }
          : g
      ),
      currentGeneration: state.currentGeneration?.id === generationId
        ? { ...state.currentGeneration, generatedText: newText, wordCount: newText.split(/\s+/).filter(w => w.length > 0).length }
        : state.currentGeneration,
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
  
  // ==================== GRAPH PERSISTENCE ====================
  loadGraphNodes: async () => {
    try {
      const response = await fetch(`${API_BASE}/graph/nodes`)
      if (response.ok) {
        const result = await response.json()
        if (result.nodes && result.nodes.length > 0) {
          // Convert backend nodes to frontend format
          const nodes: GraphNode[] = result.nodes.map((n: any) => ({
            id: n.node_id,
            label: n.label,
            branchId: n.branch_id,
            sceneId: n.scene_id,
            x: n.x,
            y: n.y,
            importance: n.importance,
            // Extract type from metadata or default to 'scene'
            type: (n.metadata?.type as NodeType) || 'scene',
            content: {
              text: '',
              version: 1,
              lastModified: n.updated_at,
              wordCount: 0,
            },
            metadata: {
              title: n.label,
              location: n.metadata?.location || '',
              timeOfDay: n.metadata?.time_of_day || '',
              estimatedReadingTime: 0,
              moodTags: n.metadata?.mood_tags || [],
              ...n.metadata,
            },
            versions: [],
            characters: n.metadata?.characters || [],
          }))
          
          set({ nodes })
          console.log(`Loaded ${nodes.length} nodes from graph database`)
        }
      }
    } catch (error) {
      console.error('Failed to load graph nodes:', error)
    }
  },
  
  // ==================== MANGA STORAGE ====================
  mangaVolumes: [],
  
  fetchMangaVolumes: async () => {
    try {
      const response = await fetch(`${API_BASE}/manga`)
      if (response.ok) {
        const result = await response.json()
        if (result.success) {
          set({ mangaVolumes: result.volumes })
        }
      }
    } catch (error) {
      console.error('Failed to fetch manga volumes:', error)
    }
  },
  
  deleteMangaVolume: async (volume_id: string) => {
    try {
      const response = await fetch(`${API_BASE}/manga/${volume_id}`, {
        method: 'DELETE',
      })
      if (response.ok) {
        // Refresh the list
        await get().fetchMangaVolumes()
        return true
      }
      return false
    } catch (error) {
      console.error('Failed to delete manga volume:', error)
      return false
    }
  },
  
  // ==================== ERROR HANDLING ====================
  clearError: (key) => {
    set(state => ({ error: { ...state.error, [key]: null } }))
  },
  
  // ==================== TOAST NOTIFICATIONS ====================
  addToast: (toast) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    set(state => ({
      toasts: [...state.toasts, { ...toast, id }]
    }))
    // Auto-remove after duration
    setTimeout(() => {
      get().removeToast(id)
    }, toast.duration || 5000)
  },
  
  removeToast: (id) => {
    set(state => ({
      toasts: state.toasts.filter(t => t.id !== id)
    }))
  },
  
  // ==================== PHASE C: IMAGE GENERATION ====================
  toggleArtistPanel: () => set(state => ({ artistPanelOpen: !state.artistPanelOpen })),
  
  createSceneBlueprint: (nodeId, blueprint) => {
    set(state => ({
      sceneBlueprints: { ...state.sceneBlueprints, [nodeId]: blueprint }
    }))
  },
  
  updateSceneBlueprint: (nodeId, updates) => {
    set(state => ({
      sceneBlueprints: {
        ...state.sceneBlueprints,
        [nodeId]: { ...state.sceneBlueprints[nodeId], ...updates }
      }
    }))
  },
  
  setAtmospherePreset: (presetId) => {
    set(state => ({
      atmosphereSettings: { ...state.atmosphereSettings, presetId }
    }))
  },
  
  updateAtmosphereSettings: (settings) => {
    set(state => ({
      atmosphereSettings: { ...state.atmosphereSettings, ...settings }
    }))
  },
  
  generatePanels: async (request) => {
    set({ activeGeneration: { id: `gen-${Date.now()}`, progress: 0, currentStep: 'Initializing...', eta: 30 } })
    
    // Simulate generation progress
    const steps = ['Analyzing blueprint...', 'Generating panels...', 'Applying atmosphere...', 'Finalizing...']
    let progress = 0
    
    const interval = setInterval(() => {
      progress += 10
      const stepIndex = Math.min(Math.floor(progress / 25), steps.length - 1)
      set({
        activeGeneration: {
          id: `gen-${Date.now()}`,
          progress,
          currentStep: steps[stepIndex],
          eta: Math.max(0, 30 - progress)
        }
      })
      
      if (progress >= 100) {
        clearInterval(interval)
        // Create mock panels
        const newPanels: GeneratedPanel[] = Array.from({ length: 4 }, (_, i) => ({
          id: `panel-${Date.now()}-${i}`,
          nodeId: request.nodeId,
          url: null,
          seed: Math.floor(Math.random() * 1000000),
          status: 'completed',
          createdAt: new Date().toISOString(),
        }))
        
        set(state => ({
          generatedPanels: [...state.generatedPanels, ...newPanels],
          activeGeneration: null
        }))
      }
    }, 500)
  },
  
  cancelPanelGeneration: () => {
    set({ activeGeneration: null })
  },
  
  queuePanelGeneration: (request) => {
    const newItem: GenerationQueueItem = {
      id: `queue-${Date.now()}`,
      ...request,
      status: 'pending'
    }
    set(state => ({
      generationQueue: [...state.generationQueue, newItem]
    }))
  },
  
  deleteGeneratedPanel: (panelId) => {
    set(state => ({
      generatedPanels: state.generatedPanels.filter(p => p.id !== panelId)
    }))
  },
  
  regeneratePanel: (panelId) => {
    set(state => ({
      generatedPanels: state.generatedPanels.map(p =>
        p.id === panelId ? { ...p, status: 'pending' as const } : p
      )
    }))
  },
  
  setViewerMode: (mode) => set({ viewerMode: mode }),
  
  selectPanel: (panelId) => set({ selectedPanelId: panelId }),
  
  // ==================== PHASE D: SEARCH & MEMORY ====================
  toggleSearchPanel: () => set(state => ({ searchPanelOpen: !state.searchPanelOpen })),
  
  performSearch: async (_query, _filters) => {
    // Mock search implementation
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
  
  addToContext: (resultId) => {
    // Add search result to writer panel context
    const result = get().searchResults.find(r => r.id === resultId)
    if (result) {
      // Implementation would add to context chunks
      console.log('Added to context:', result)
    }
  },
  
  toggleMemoryBrowser: () => set(state => ({ memoryBrowserOpen: !state.memoryBrowserOpen })),
  
  // ==================== PHASE E: CONSEQUENCE SIMULATOR ====================
  toggleSimulator: () => set(state => ({ simulatorOpen: !state.simulatorOpen })),
  
  simulateChange: async (_request) => {
    // Mock simulation
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
  
  // ==================== PHASE F: TONE ANALYSIS ====================
  toggleToneHeatmap: () => set(state => ({ toneHeatmapOpen: !state.toneHeatmapOpen })),
  
  // ==================== SPRINT 11: WEBSOCKET & REAL-TIME ====================
  initializeWebSocket: () => {
    const clientId = `client-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    const ws = new WebSocket(`ws://localhost:8000/api/ws/${clientId}`)
    
    ws.onopen = () => {
      console.log('WebSocket connected')
      set({ wsConnection: ws, wsConnected: true })
      
      // Send ping to keep alive
      setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ action: 'ping' }))
        }
      }, 30000)
    }
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      
      switch (message.type) {
        case 'generation_progress':
          set({ generationProgress: message.data })
          break
        case 'job_complete':
          set({ generationProgress: null })
          // Add toast notification
          get().addToast({
            message: message.data.message || 'Generation complete',
            type: 'success',
          })
          break
        case 'subscribed':
          console.log('Subscribed to job:', message.jobId)
          break
        case 'pong':
          // Keep-alive response
          break
      }
    }
    
    ws.onclose = () => {
      console.log('WebSocket disconnected')
      set({ wsConnection: null, wsConnected: false })
      // Attempt reconnect after 3 seconds
      setTimeout(() => get().initializeWebSocket(), 3000)
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  },
  
  closeWebSocket: () => {
    const ws = get().wsConnection
    if (ws) {
      ws.close()
      set({ wsConnection: null, wsConnected: false })
    }
  },
  
  subscribeToJob: (jobId) => {
    const ws = get().wsConnection
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'subscribe', jobId }))
    }
  },
  
  // ==================== SPRINT 12: NAVIGATION HISTORY ====================
  addToRecentNodes: (nodeId) => {
    const state = get()
    
    // Add to recent nodes (keep last 20)
    const newRecent = [nodeId, ...state.recentNodes.filter(id => id !== nodeId)].slice(0, 20)
    
    // Add to navigation history
    const newHistory = state.navigationHistory.slice(0, state.historyIndex + 1)
    if (newHistory[newHistory.length - 1] !== nodeId) {
      newHistory.push(nodeId)
    }
    
    set({
      recentNodes: newRecent,
      navigationHistory: newHistory,
      historyIndex: newHistory.length - 1,
    })
  },
  
  navigateHistory: (direction) => {
    const state = get()
    const newIndex = direction === 'back' 
      ? Math.max(0, state.historyIndex - 1)
      : Math.min(state.navigationHistory.length - 1, state.historyIndex + 1)
    
    if (newIndex !== state.historyIndex && state.navigationHistory[newIndex]) {
      set({ historyIndex: newIndex })
      get().selectNode(state.navigationHistory[newIndex])
    }
  },
  
  clearHistory: () => {
    set({
      recentNodes: [],
      navigationHistory: [],
      historyIndex: -1,
    })
  },
}))
