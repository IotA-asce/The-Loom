import { create } from 'zustand'

// ==================== TYPES ====================

export interface TunerSettings {
  violence: number
  humor: number
  romance: number
}

export interface TunerResolution extends TunerSettings {
  warnings: string[]
  precedenceOrder: string[]
}

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
  contextChunks: string[]
  styleExemplars: string[]
  characterIds: string[]
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

// ==================== GENERATION STATE ====================

export interface GenerationState {
  // Text generation state
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
  expandedContradictions: string[]
  styleProfile: StyleProfile | null
  tunerSettings: TunerSettings
  tunerResolution: TunerResolution | null
  tunerOpen: boolean

  // Image generation state
  artistPanelOpen: boolean
  sceneBlueprints: Record<string, SceneBlueprint>
  atmosphereSettings: AtmosphereSettings
  generatedPanels: GeneratedPanel[]
  generationQueue: GenerationQueueItem[]
  activeGeneration: ActiveGeneration | null
  viewerMode: 'grid' | 'sequential' | 'split'
  selectedPanelId: string | null
  continuityIssues: ContinuityIssue[]

  // References for cross-store operations
  selectedNodeId: string | null
  nodes: { id: string; characters: string[] }[]
}

export interface GenerationActions {
  // Panel toggles
  toggleWriterPanel: () => void
  toggleArtistPanel: () => void
  toggleTuner: () => void

  // Context management
  retrieveContext: (query: string, branchId: string) => Promise<void>
  toggleContextChunk: (chunkId: string) => void
  expandContextChunk: (chunkId: string, expanded: boolean) => void
  removeContextChunk: (chunkId: string) => void
  reorderContextChunks: (chunkIds: string[]) => void

  // Style management
  retrieveStyleExemplars: (queryText: string) => Promise<void>
  toggleStyleExemplar: (exemplarId: string) => void
  setStyleGuide: (exemplarId: string) => void

  // Generation control
  generateText: (request: Partial<GenerationRequest>) => Promise<void>
  cancelGeneration: () => void
  acceptGeneration: (generationId: string, updateNodeContent?: (nodeId: string, text: string) => Promise<void>) => void
  rejectGeneration: (generationId: string) => void
  checkContradictions: (generatedText: string) => Promise<void>
  expandContradiction: (contradictionId: string, expanded: boolean) => void
  updateGenerationParams: (params: Partial<GenerationState['generationParams']>) => void

  // Context presets
  saveContextPreset: (name: string) => void
  loadContextPreset: (presetId: string) => void
  deleteContextPreset: (presetId: string) => void

  // Tuner
  updateTuner: (settings: TunerSettings) => Promise<void>

  // Inline editing
  editGenerationInline: (generationId: string, newText: string) => void

  // Image generation
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

  // Cross-store setters
  setSelectedNodeId: (nodeId: string | null) => void
  setNodes: (nodes: { id: string; characters: string[] }[]) => void
}

const API_BASE = '/api'

// ==================== STORE IMPLEMENTATION ====================

export const useGenerationStore = create<GenerationState & GenerationActions>((set, get) => ({
  // ==================== INITIAL STATE ====================
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
  tunerSettings: { violence: 0.5, humor: 0.5, romance: 0.5 },
  tunerResolution: null,
  tunerOpen: false,

  artistPanelOpen: false,
  sceneBlueprints: {},
  atmosphereSettings: {
    presetId: 'neutral',
    direction: 'top',
    intensity: 0.6,
    contrast: 0.5,
    shadowHardness: 0.5,
    textureDetail: 0.6,
    textureStyle: 'clean',
    weathering: 0.3,
  },
  generatedPanels: [],
  generationQueue: [],
  activeGeneration: null,
  viewerMode: 'grid',
  selectedPanelId: null,
  continuityIssues: [],

  selectedNodeId: null,
  nodes: [],

  // ==================== PANEL TOGGLES ====================
  toggleWriterPanel: () => set(state => ({ writerPanelOpen: !state.writerPanelOpen })),
  toggleArtistPanel: () => set(state => ({ artistPanelOpen: !state.artistPanelOpen })),
  toggleTuner: () => set(state => ({ tunerOpen: !state.tunerOpen })),

  // ==================== CONTEXT MANAGEMENT ====================
  retrieveContext: async (query, branchId) => {
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
    }
  },

  toggleContextChunk: (chunkId) => {
    set(state => ({
      contextChunks: state.contextChunks.map(c =>
        c.id === chunkId ? { ...c, pinned: !c.pinned } : c
      ),
    }))
  },

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

  reorderContextChunks: (chunkIds) => {
    set(state => ({
      contextChunks: chunkIds
        .map(id => state.contextChunks.find(c => c.id === id))
        .filter(Boolean) as ContextChunk[],
    }))
  },

  // ==================== STYLE MANAGEMENT ====================
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

  setStyleGuide: (exemplarId) => {
    set(state => ({
      styleExemplars: state.styleExemplars.map(e =>
        e.id === exemplarId ? { ...e, isStyleGuide: !e.isStyleGuide } : { ...e, isStyleGuide: false }
      ),
    }))
  },

  // ==================== GENERATION CONTROL ====================
  generateText: async (request) => {
    const state = get()

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

        await get().checkContradictions(result.generatedText)
      }
    } catch (error) {
      console.error('Failed to generate text:', error)
    }
  },

  cancelGeneration: () => {
    // Cancel ongoing generation
  },

  acceptGeneration: (generationId, updateNodeContent) => {
    const state = get()
    const generation = state.generationResults.find(g => g.id === generationId)
    if (generation && state.selectedNodeId && updateNodeContent) {
      updateNodeContent(state.selectedNodeId, generation.generatedText)
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

  expandContradiction: (contradictionId, expanded) => {
    set(state => ({
      expandedContradictions: expanded
        ? [...state.expandedContradictions, contradictionId]
        : state.expandedContradictions.filter(id => id !== contradictionId),
    }))
  },

  updateGenerationParams: (params) => {
    set(state => ({
      generationParams: { ...state.generationParams, ...params },
    }))
  },

  // ==================== CONTEXT PRESETS ====================
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

  // ==================== TUNER ====================
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

  // ==================== INLINE EDITING ====================
  editGenerationInline: (generationId, newText) => {
    const wordCount = newText.split(/\s+/).filter(w => w.length > 0).length
    set(state => ({
      generationResults: state.generationResults.map(g =>
        g.id === generationId
          ? { ...g, generatedText: newText, wordCount }
          : g
      ),
      currentGeneration: state.currentGeneration?.id === generationId
        ? { ...state.currentGeneration, generatedText: newText, wordCount }
        : state.currentGeneration,
    }))
  },

  // ==================== IMAGE GENERATION ====================
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

  // ==================== CROSS-STORE SETTERS ====================
  setSelectedNodeId: (nodeId) => set({ selectedNodeId: nodeId }),
  setNodes: (nodes) => set({ nodes }),
}))
