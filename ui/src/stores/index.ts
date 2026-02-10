import { useEffect } from 'react'

// Re-export all individual stores
export { useGraphStore } from './graphStore'
export { useContentStore } from './contentStore'
export { useGenerationStore } from './generationStore'
export { useUIStore } from './uiStore'

// Re-export all types
export type {
  NodeType,
  SceneMetadata,
  NodeContent,
  NodeVersion,
  GraphNode,
  GraphEdge,
  Branch,
  Viewport,
  GraphState,
  GraphActions,
} from './graphStore'

export type {
  Character,
  ReadingPreferences,
  ContentState,
  ContentActions,
} from './contentStore'

export type {
  TunerSettings,
  TunerResolution,
  ContextChunk,
  ContextPreset,
  StyleExemplar,
  StyleProfile,
  GenerationRequest,
  GenerationResult,
  Contradiction,
  SceneBlueprint,
  AtmosphereSettings,
  GeneratedPanel,
  GenerationQueueItem,
  ActiveGeneration,
  ContinuityIssue,
  GenerationState,
  GenerationActions,
} from './generationStore'

export type {
  Toast,
  SyncState,
  GraphMetrics,
  Phase8Metrics,
  SearchResult,
  SimulationResult,
  UIState,
  UIActions,
} from './uiStore'

// ==================== COMBINED APP STORE ====================

import { useGraphStore } from './graphStore'
import { useContentStore } from './contentStore'
import { useGenerationStore } from './generationStore'
import { useUIStore } from './uiStore'

/**
 * Combined hook that provides access to all domain stores.
 * Use this for components that need access to multiple domains,
 * or use individual stores for domain-specific components.
 */
export function useAppStore() {
  // Graph store
  const graph = useGraphStore()
  
  // Content store
  const content = useContentStore()
  
  // Generation store
  const generation = useGenerationStore()
  
  // UI store
  const ui = useUIStore()

  // Sync selectedNodeId across stores
  useEffect(() => {
    content.setSelectedNodeId(graph.selectedNodeId)
    generation.setSelectedNodeId(graph.selectedNodeId)
    ui.setSelectedNodeId(graph.selectedNodeId)
  }, [graph.selectedNodeId, content, generation, ui])

  // Sync nodes across stores
  useEffect(() => {
    content.setNodes(graph.nodes)
    generation.setNodes(graph.nodes.map(n => ({ id: n.id, characters: n.characters })))
    ui.setNodes(graph.nodes.map(n => ({ 
      id: n.id, 
      label: n.label, 
      x: n.x, 
      y: n.y, 
      branchId: n.branchId 
    })))
  }, [graph.nodes, content, generation, ui])

  // Sync branches to UI store
  useEffect(() => {
    ui.setBranches(graph.branches.map(b => ({ 
      branchId: b.branchId, 
      status: b.status 
    })))
  }, [graph.branches, ui])

  // Combined actions that orchestrate multiple stores
  const combinedActions = {
    // Initialization
    initialize: () => {
      graph.initialize()
      content.initialize()
      ui.initialize()
      
      // Set up keyboard shortcuts
      const shortcuts = {
        'ctrl+z': () => graph.undo(),
        'ctrl+y': () => graph.redo(),
        'ctrl+t': () => generation.toggleTuner(),
        'ctrl+d': () => ui.toggleDualView(),
        'ctrl+s': () => graph.createAutosave('manual'),
        'ctrl+?': () => alert('Shortcuts: Ctrl+Z=Undo, Ctrl+Y=Redo, Ctrl+T=Tuner, Ctrl+D=Dual View, Ctrl+S=Save, Ctrl+N=New Node, Enter=Edit, Delete=Delete, Arrows=Navigate'),
        'ctrl+n': () => {
          if (graph.selectedNodeId) {
            const node = graph.nodes.find(n => n.id === graph.selectedNodeId)
            if (node) {
              graph.addNode({
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
        'enter': () => {
          if (graph.selectedNodeId) {
            content.startEditingNode(graph.selectedNodeId)
          }
        },
        'delete': () => {
          if (graph.selectedNodeId && confirm('Delete this node?')) {
            graph.deleteNode(graph.selectedNodeId)
          }
        },
        'arrowup': () => graph.navigateGraph('up'),
        'arrowdown': () => graph.navigateGraph('down'),
        'arrowleft': () => graph.navigateGraph('left'),
        'arrowright': () => graph.navigateGraph('right'),
        'escape': () => {
          if (content.editingNodeId) {
            content.stopEditingNode()
          } else if (content.readingMode) {
            content.exitReadingMode()
          } else if (graph.selectedNodeId) {
            graph.selectNode(null)
          }
        },
      }
      ui.setKeyboardShortcuts(shortcuts)
    },

    // Content editing with graph integration
    startEditingNode: (nodeId: string) => {
      graph.selectNode(nodeId)
      content.startEditingNode(nodeId)
    },

    updateNodeContent: async (nodeId: string, text: string) => {
      await content.updateNodeContent(nodeId, text)
    },

    acceptGeneration: (generationId: string) => {
      const gen = generation.generationResults.find(g => g.id === generationId)
      if (gen && graph.selectedNodeId) {
        content.updateNodeContent(graph.selectedNodeId, gen.generatedText)
      }
    },

    // Navigation helpers
    selectNextNode: () => {
      const currentIndex = graph.nodes.findIndex(n => n.id === graph.selectedNodeId)
      if (currentIndex < graph.nodes.length - 1) {
        graph.selectNode(graph.nodes[currentIndex + 1].id)
      }
    },

    selectPreviousNode: () => {
      const currentIndex = graph.nodes.findIndex(n => n.id === graph.selectedNodeId)
      if (currentIndex > 0) {
        graph.selectNode(graph.nodes[currentIndex - 1].id)
      }
    },

    // Error handling with UI integration
    setLoading: (key: 'nodes' | 'content' | 'generation', value: boolean) => {
      ui.setLoading(key, value)
    },

    setError: (key: 'nodes' | 'content', message: string | null) => {
      ui.setError(key, message)
    },

    addToast: (toast: Omit<import('./uiStore').Toast, 'id'>) => {
      ui.addToast(toast)
    },

    // Toggle reading mode with proper state
    toggleReadingMode: () => {
      if (!content.readingMode) {
        const activeBranch = graph.branches.find(b => b.status === 'active')
        const branchId = activeBranch?.branchId || 'main'
        const nodeId = graph.selectedNodeId || graph.nodes[0]?.id
        content.enterReadingMode(branchId, nodeId)
      } else {
        content.exitReadingMode()
      }
    },
  }

  return {
    // Direct store access for granular control
    graph,
    content,
    generation,
    ui,
    
    // Combined state (flattened for backward compatibility)
    nodes: graph.nodes,
    edges: graph.edges,
    selectedNodeId: graph.selectedNodeId,
    zoom: graph.zoom,
    viewport: graph.viewport,
    branches: graph.branches,
    
    editingNodeId: content.editingNodeId,
    showNodePreview: content.showNodePreview,
    readingMode: content.readingMode,
    readingBranchId: content.readingBranchId,
    readingNodeId: content.readingNodeId,
    readingPreferences: content.readingPreferences,
    characters: content.characters,
    
    writerPanelOpen: generation.writerPanelOpen,
    artistPanelOpen: generation.artistPanelOpen,
    contextChunks: generation.contextChunks,
    styleExemplars: generation.styleExemplars,
    generationResults: generation.generationResults,
    currentGeneration: generation.currentGeneration,
    generationParams: generation.generationParams,
    contextPresets: generation.contextPresets,
    activePresetId: generation.activePresetId,
    contradictions: generation.contradictions,
    expandedContradictions: generation.expandedContradictions,
    styleProfile: generation.styleProfile,
    tunerSettings: generation.tunerSettings,
    tunerResolution: generation.tunerResolution,
    tunerOpen: generation.tunerOpen,
    sceneBlueprints: generation.sceneBlueprints,
    atmosphereSettings: generation.atmosphereSettings,
    generatedPanels: generation.generatedPanels,
    generationQueue: generation.generationQueue,
    activeGeneration: generation.activeGeneration,
    viewerMode: generation.viewerMode,
    selectedPanelId: generation.selectedPanelId,
    continuityIssues: generation.continuityIssues,
    
    toasts: ui.toasts,
    loading: ui.loading,
    error: ui.error,
    dualViewOpen: ui.dualViewOpen,
    syncState: ui.syncState,
    searchPanelOpen: ui.searchPanelOpen,
    searchResults: ui.searchResults,
    memoryBrowserOpen: ui.memoryBrowserOpen,
    simulatorOpen: ui.simulatorOpen,
    toneHeatmapOpen: ui.toneHeatmapOpen,
    graphMetrics: ui.graphMetrics,
    phase8Metrics: ui.phase8Metrics,
    
    // Combined actions
    ...combinedActions,
    
    // Direct actions from graph store
    addNode: graph.addNode,
    selectNode: graph.selectNode,
    deleteNode: graph.deleteNode,
    updateNodePosition: graph.updateNodePosition,
    setZoom: graph.setZoom,
    setViewport: graph.setViewport,
    undo: graph.undo,
    redo: graph.redo,
    createAutosave: graph.createAutosave,
    createBranch: graph.createBranch,
    archiveBranch: graph.archiveBranch,
    mergeBranch: graph.mergeBranch,
    previewBranchImpact: graph.previewBranchImpact,
    navigateGraph: graph.navigateGraph,
    
    // Direct actions from content store
    stopEditingNode: content.stopEditingNode,
    updateNodeMetadata: content.updateNodeMetadata,
    updateNodeType: content.updateNodeType,
    saveNodeVersion: content.saveNodeVersion,
    restoreNodeVersion: content.restoreNodeVersion,
    toggleNodePreview: content.toggleNodePreview,
    enterReadingMode: content.enterReadingMode,
    exitReadingMode: content.exitReadingMode,
    navigateReading: content.navigateReading,
    jumpToNodeInReading: content.jumpToNodeInReading,
    updateReadingPreferences: content.updateReadingPreferences,
    addCharacter: content.addCharacter,
    updateCharacter: content.updateCharacter,
    deleteCharacter: content.deleteCharacter,
    toggleCharacterInNode: content.toggleCharacterInNode,
    toggleVoiceEnforcement: content.toggleVoiceEnforcement,
    toggleCharacterFocus: content.toggleCharacterFocus,
    filterCharacters: content.filterCharacters,
    sortCharacters: content.sortCharacters,
    
    // Direct actions from generation store
    toggleWriterPanel: generation.toggleWriterPanel,
    toggleArtistPanel: generation.toggleArtistPanel,
    toggleTuner: generation.toggleTuner,
    retrieveContext: generation.retrieveContext,
    toggleContextChunk: generation.toggleContextChunk,
    expandContextChunk: generation.expandContextChunk,
    removeContextChunk: generation.removeContextChunk,
    reorderContextChunks: generation.reorderContextChunks,
    retrieveStyleExemplars: generation.retrieveStyleExemplars,
    toggleStyleExemplar: generation.toggleStyleExemplar,
    setStyleGuide: generation.setStyleGuide,
    generateText: generation.generateText,
    cancelGeneration: generation.cancelGeneration,
    rejectGeneration: generation.rejectGeneration,
    checkContradictions: generation.checkContradictions,
    expandContradiction: generation.expandContradiction,
    updateGenerationParams: generation.updateGenerationParams,
    saveContextPreset: generation.saveContextPreset,
    loadContextPreset: generation.loadContextPreset,
    deleteContextPreset: generation.deleteContextPreset,
    updateTuner: generation.updateTuner,
    editGenerationInline: generation.editGenerationInline,
    createSceneBlueprint: generation.createSceneBlueprint,
    updateSceneBlueprint: generation.updateSceneBlueprint,
    setAtmospherePreset: generation.setAtmospherePreset,
    updateAtmosphereSettings: generation.updateAtmosphereSettings,
    generatePanels: generation.generatePanels,
    cancelPanelGeneration: generation.cancelPanelGeneration,
    queuePanelGeneration: generation.queuePanelGeneration,
    deleteGeneratedPanel: generation.deleteGeneratedPanel,
    regeneratePanel: generation.regeneratePanel,
    setViewerMode: generation.setViewerMode,
    selectPanel: generation.selectPanel,
    
    // Direct actions from UI store
    removeToast: ui.removeToast,
    clearError: ui.clearError,
    toggleDualView: ui.toggleDualView,
    initializeDualView: ui.initializeDualView,
    editSentence: ui.editSentence,
    requestPanelRedraw: ui.requestPanelRedraw,
    reconcile: ui.reconcile,
    toggleSearchPanel: ui.toggleSearchPanel,
    performSearch: ui.performSearch,
    addToContext: ui.addToContext,
    toggleMemoryBrowser: ui.toggleMemoryBrowser,
    toggleSimulator: ui.toggleSimulator,
    simulateChange: ui.simulateChange,
    toggleToneHeatmap: ui.toggleToneHeatmap,
    refreshMetrics: ui.refreshMetrics,
    ingestFile: ui.ingestFile,
  }
}

// Default export for convenience
export default useAppStore
