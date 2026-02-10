import { create } from 'zustand'

// ==================== TYPES ====================

export type NodeType = 'chapter' | 'scene' | 'beat' | 'dialogue'

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

export interface ReadingPreferences {
  fontSize: 'small' | 'medium' | 'large'
  theme: 'light' | 'dark' | 'sepia'
  lineSpacing: 'compact' | 'normal' | 'relaxed'
}

// ==================== CONTENT STATE ====================

export interface ContentState {
  // State
  editingNodeId: string | null
  showNodePreview: boolean
  readingMode: boolean
  readingBranchId: string | null
  readingNodeId: string | null
  readingPreferences: ReadingPreferences
  characters: Character[]
  nodes: GraphNode[] // Reference to nodes for content operations
}

export interface ContentActions {
  // Content editing actions
  startEditingNode: (nodeId: string) => void
  stopEditingNode: () => void
  updateNodeContent: (nodeId: string, text: string) => Promise<void>
  updateNodeMetadata: (nodeId: string, metadata: Partial<SceneMetadata>) => Promise<void>
  updateNodeType: (nodeId: string, type: NodeType) => Promise<void>
  saveNodeVersion: (nodeId: string) => Promise<void>
  restoreNodeVersion: (nodeId: string, versionId: string) => Promise<void>
  toggleNodePreview: () => void

  // Reading view actions
  toggleReadingMode: () => void
  enterReadingMode: (branchId: string, nodeId?: string) => void
  exitReadingMode: () => void
  navigateReading: (direction: 'prev' | 'next') => void
  jumpToNodeInReading: (nodeId: string) => void
  updateReadingPreferences: (prefs: Partial<ReadingPreferences>) => void

  // Character management
  addCharacter: (character: Omit<Character, 'id'>) => Promise<void>
  updateCharacter: (characterId: string, updates: Partial<Character>) => Promise<void>
  deleteCharacter: (characterId: string) => Promise<void>
  toggleCharacterInNode: (nodeId: string, characterId: string) => Promise<void>
  toggleVoiceEnforcement: (characterId: string) => void
  toggleCharacterFocus: (characterId: string) => void
  filterCharacters: (query: string) => Character[]
  sortCharacters: (by: 'name' | 'importance' | 'appearance') => void

  // Setters for shared state
  setNodes: (nodes: GraphNode[] | ((prev: GraphNode[]) => GraphNode[])) => void
  setSelectedNodeId: (nodeId: string | null) => void
  getSelectedNodeId: () => string | null
  getBranches: () => { branchId: string; status: string }[]
  initialize: () => void
}

// ==================== STORE IMPLEMENTATION ====================

export const useContentStore = create<ContentState & ContentActions>((set, get) => ({
  // ==================== INITIAL STATE ====================
  editingNodeId: null,
  showNodePreview: true,
  readingMode: false,
  readingBranchId: null,
  readingNodeId: null,
  readingPreferences: {
    fontSize: 'medium',
    theme: 'dark',
    lineSpacing: 'normal',
  },
  characters: [],
  nodes: [],

  // ==================== INITIALIZATION ====================
  initialize: () => {
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

  // ==================== CONTENT EDITING ====================
  startEditingNode: (nodeId) => set({ editingNodeId: nodeId }),
  stopEditingNode: () => set({ editingNodeId: null }),

  updateNodeContent: async (nodeId, text) => {
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

  // ==================== READING VIEW ====================
  toggleReadingMode: () => {
    const state = get()
    if (!state.readingMode) {
      const branches = get().getBranches()
      const branchId = branches.find(b => b.status === 'active')?.branchId || 'main'
      const nodeId = get().getSelectedNodeId() || state.nodes[0]?.id || null
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

  // ==================== CHARACTER MANAGEMENT ====================
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

  // ==================== SHARED STATE SETTERS ====================
  setNodes: (nodes) => {
    if (typeof nodes === 'function') {
      set(state => ({ nodes: nodes(state.nodes) }))
    } else {
      set({ nodes })
    }
  },

  setSelectedNodeId: () => {
    // This is a placeholder - actual selection happens in graphStore
    // This store is notified via the combined store
  },

  getSelectedNodeId: () => {
    // Returns the selected node ID from the combined store context
    return null
  },

  getBranches: () => {
    // Returns branches from the combined store context
    return []
  },
}))
