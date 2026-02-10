import { create } from 'zustand'

// ==================== TYPES ====================

export type EdgeType = 'causal' | 'temporal' | 'parallel'
export type LineStyle = 'solid' | 'dashed' | 'dotted'

export interface Edge {
  id: string
  source: string
  target: string
  type: EdgeType
  label?: string
  style: LineStyle
  color?: string
  weight?: number
}

export interface EdgeCreationState {
  isCreating: boolean
  sourceNodeId: string | null
  currentX: number
  currentY: number
  targetNodeId: string | null
}

export interface LayoutConfig {
  type: 'hierarchical' | 'force' | 'circular' | 'timeline' | 'manual'
  animate: boolean
  branchClustering: boolean
}

export interface LayoutState {
  config: LayoutConfig
  isApplying: boolean
}

// ==================== EDGE STORE ====================

export interface EdgeState {
  // Edge data
  edges: Edge[]
  
  // Edge creation state
  edgeCreation: EdgeCreationState
  
  // Edge configuration
  defaultEdgeType: EdgeType
  defaultLineStyle: LineStyle
  defaultColor: string
  
  // Layout state
  layout: LayoutState
  
  // Actions
  startEdgeCreation: (sourceNodeId: string) => void
  updateEdgeCreationPosition: (x: number, y: number) => void
  setEdgeCreationTarget: (targetNodeId: string | null) => void
  completeEdgeCreation: () => void
  cancelEdgeCreation: () => void
  addEdge: (edge: Omit<Edge, 'id'>) => void
  removeEdge: (edgeId: string) => void
  updateEdge: (edgeId: string, updates: Partial<Edge>) => void
  setDefaultEdgeType: (type: EdgeType) => void
  setDefaultLineStyle: (style: LineStyle) => void
  setDefaultColor: (color: string) => void
  
  // Layout actions
  applyLayout: (layoutType: LayoutConfig['type'], nodes: Array<{ id: string; x: number; y: number; branchId: string }>) => Promise<Array<{ id: string; x: number; y: number }>>
  setLayoutConfig: (config: Partial<LayoutConfig>) => void
}

// ==================== STORE IMPLEMENTATION ====================

export const useEdgeStore = create<EdgeState>((set, get) => ({
  // ==================== INITIAL STATE ====================
  edges: [],
  
  edgeCreation: {
    isCreating: false,
    sourceNodeId: null,
    currentX: 0,
    currentY: 0,
    targetNodeId: null,
  },
  
  defaultEdgeType: 'causal',
  defaultLineStyle: 'solid',
  defaultColor: '#888888',
  
  layout: {
    config: {
      type: 'manual',
      animate: true,
      branchClustering: true,
    },
    isApplying: false,
  },
  
  // ==================== EDGE CREATION ACTIONS ====================
  startEdgeCreation: (sourceNodeId) => {
    set({
      edgeCreation: {
        isCreating: true,
        sourceNodeId,
        currentX: 0,
        currentY: 0,
        targetNodeId: null,
      },
    })
  },
  
  updateEdgeCreationPosition: (x, y) => {
    set(state => ({
      edgeCreation: {
        ...state.edgeCreation,
        currentX: x,
        currentY: y,
      },
    }))
  },
  
  setEdgeCreationTarget: (targetNodeId) => {
    set(state => ({
      edgeCreation: {
        ...state.edgeCreation,
        targetNodeId,
      },
    }))
  },
  
  completeEdgeCreation: () => {
    const state = get()
    const { sourceNodeId, targetNodeId } = state.edgeCreation
    
    if (sourceNodeId && targetNodeId && sourceNodeId !== targetNodeId) {
      // Check if edge already exists
      const exists = state.edges.some(
        e => e.source === sourceNodeId && e.target === targetNodeId
      )
      
      if (!exists) {
        const newEdge: Edge = {
          id: `edge-${Date.now()}`,
          source: sourceNodeId,
          target: targetNodeId,
          type: state.defaultEdgeType,
          style: state.defaultLineStyle,
          color: state.defaultColor,
          weight: 1,
        }
        
        set({
          edges: [...state.edges, newEdge],
          edgeCreation: {
            isCreating: false,
            sourceNodeId: null,
            currentX: 0,
            currentY: 0,
            targetNodeId: null,
          },
        })
      }
    }
    
    // Reset creation state
    set({
      edgeCreation: {
        isCreating: false,
        sourceNodeId: null,
        currentX: 0,
        currentY: 0,
        targetNodeId: null,
      },
    })
  },
  
  cancelEdgeCreation: () => {
    set({
      edgeCreation: {
        isCreating: false,
        sourceNodeId: null,
        currentX: 0,
        currentY: 0,
        targetNodeId: null,
      },
    })
  },
  
  // ==================== EDGE MANAGEMENT ACTIONS ====================
  addEdge: (edgeData) => {
    const newEdge: Edge = {
      ...edgeData,
      id: `edge-${Date.now()}`,
    }
    set(state => ({ edges: [...state.edges, newEdge] }))
  },
  
  removeEdge: (edgeId) => {
    set(state => ({
      edges: state.edges.filter(e => e.id !== edgeId),
    }))
  },
  
  updateEdge: (edgeId, updates) => {
    set(state => ({
      edges: state.edges.map(e =>
        e.id === edgeId ? { ...e, ...updates } : e
      ),
    }))
  },
  
  setDefaultEdgeType: (type) => {
    set({ defaultEdgeType: type })
  },
  
  setDefaultLineStyle: (style) => {
    set({ defaultLineStyle: style })
  },
  
  setDefaultColor: (color) => {
    set({ defaultColor: color })
  },
  
  // ==================== LAYOUT ACTIONS ====================
  applyLayout: async (layoutType, nodes) => {
    const state = get()
    set({ layout: { ...state.layout, isApplying: true } })
    
    let result: Array<{ id: string; x: number; y: number }> = []
    
    switch (layoutType) {
      case 'hierarchical':
        result = applyHierarchicalLayout(nodes, state.layout.config.branchClustering)
        break
      case 'force':
        result = applyForceDirectedLayout(nodes, state.edges)
        break
      case 'circular':
        result = applyCircularLayout(nodes, state.layout.config.branchClustering)
        break
      case 'timeline':
        result = applyTimelineLayout(nodes)
        break
      default:
        result = nodes.map(n => ({ id: n.id, x: n.x, y: n.y }))
    }
    
    set({ layout: { ...state.layout, isApplying: false } })
    return result
  },
  
  setLayoutConfig: (config) => {
    set(state => ({
      layout: {
        ...state.layout,
        config: { ...state.layout.config, ...config },
      },
    }))
  },
}))

// ==================== LAYOUT ALGORITHMS ====================

function applyHierarchicalLayout(
  nodes: Array<{ id: string; x: number; y: number; branchId: string }>,
  branchClustering: boolean
): Array<{ id: string; x: number; y: number }> {
  const levels = new Map<string, number>()
  const levelWidth = 200
  const levelHeight = 100
  
  // Group by branch if clustering enabled
  const branchGroups = branchClustering
    ? groupByBranch(nodes)
    : { main: nodes }
  
  const result: Array<{ id: string; x: number; y: number }> = []
  let branchOffsetX = 0
  
  Object.entries(branchGroups).forEach(([_branchId, branchNodes]) => {
    // Simple level assignment based on x position
    branchNodes.forEach((node, index) => {
      const level = Math.floor(index / 3) // 3 nodes per level
      levels.set(node.id, level)
    })
    
    // Position nodes
    const maxLevel = Math.max(...Array.from(levels.values()))
    
    branchNodes.forEach(node => {
      const level = levels.get(node.id) || 0
      const nodesInLevel = branchNodes.filter(n => levels.get(n.id) === level)
      const indexInLevel = nodesInLevel.indexOf(node)
      
      result.push({
        id: node.id,
        x: branchOffsetX + level * levelWidth,
        y: indexInLevel * levelHeight + (maxLevel > 0 ? level * 50 : 0),
      })
    })
    
    // Update offset for next branch
    const maxX = Math.max(...result.filter(r => branchNodes.some(n => n.id === r.id)).map(r => r.x))
    branchOffsetX = maxX + levelWidth * 2
  })
  
  return result
}

function applyForceDirectedLayout(
  nodes: Array<{ id: string; x: number; y: number }>,
  edges: Edge[]
): Array<{ id: string; x: number; y: number }> {
  const iterations = 100
  const k = 100 // Spring constant
  const c = 500 // Repulsion constant
  const damping = 0.9
  
  // Initialize positions
  const positions = new Map<string, { x: number; y: number; vx: number; vy: number }>()
  nodes.forEach(node => {
    positions.set(node.id, {
      x: node.x || Math.random() * 800,
      y: node.y || Math.random() * 600,
      vx: 0,
      vy: 0,
    })
  })
  
  // Run simulation
  for (let i = 0; i < iterations; i++) {
    // Repulsion between all nodes
    nodes.forEach(nodeA => {
      nodes.forEach(nodeB => {
        if (nodeA.id === nodeB.id) return
        
        const posA = positions.get(nodeA.id)!
        const posB = positions.get(nodeB.id)!
        
        const dx = posA.x - posB.x
        const dy = posA.y - posB.y
        const distance = Math.sqrt(dx * dx + dy * dy) || 1
        
        const force = c / (distance * distance)
        const fx = (dx / distance) * force
        const fy = (dy / distance) * force
        
        posA.vx += fx
        posA.vy += fy
      })
    })
    
    // Attraction along edges
    edges.forEach(edge => {
      const posA = positions.get(edge.source)
      const posB = positions.get(edge.target)
      if (!posA || !posB) return
      
      const dx = posB.x - posA.x
      const dy = posB.y - posA.y
      const distance = Math.sqrt(dx * dx + dy * dy) || 1
      
      const force = (distance - k) * 0.01
      const fx = (dx / distance) * force
      const fy = (dy / distance) * force
      
      posA.vx += fx
      posA.vy += fy
      posB.vx -= fx
      posB.vy -= fy
    })
    
    // Apply velocity and damping
    positions.forEach(pos => {
      pos.vx *= damping
      pos.vy *= damping
      pos.x += pos.vx
      pos.y += pos.vy
    })
  }
  
  return nodes.map(node => {
    const pos = positions.get(node.id)!
    return { id: node.id, x: pos.x, y: pos.y }
  })
}

function applyCircularLayout(
  nodes: Array<{ id: string; x: number; y: number; branchId: string }>,
  branchClustering: boolean
): Array<{ id: string; x: number; y: number }> {
  const centerX = 400
  const centerY = 300
  
  if (branchClustering) {
    const branchGroups = groupByBranch(nodes)
    const result: Array<{ id: string; x: number; y: number }> = []
    
    Object.entries(branchGroups).forEach(([_branchId, branchNodes], groupIndex) => {
      const radius = 150 + groupIndex * 100
      const angleStep = (2 * Math.PI) / branchNodes.length
      
      branchNodes.forEach((node, index) => {
        const angle = index * angleStep - Math.PI / 2
        result.push({
          id: node.id,
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle),
        })
      })
    })
    
    return result
  } else {
    const radius = 200
    const angleStep = (2 * Math.PI) / nodes.length
    
    return nodes.map((node, index) => {
      const angle = index * angleStep - Math.PI / 2
      return {
        id: node.id,
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      }
    })
  }
}

function applyTimelineLayout(
  nodes: Array<{ id: string; x: number; y: number }>
): Array<{ id: string; x: number; y: number }> {
  const startX = 100
  const startY = 300
  const stepX = 150
  
  // Sort by original x position as a proxy for time
  const sortedNodes = [...nodes].sort((a, b) => a.x - b.x)
  
  return sortedNodes.map((node, index) => ({
    id: node.id,
    x: startX + index * stepX,
    y: startY + (index % 2 === 0 ? 0 : 100), // Alternating y for visual interest
  }))
}

function groupByBranch<T extends { branchId: string }>(nodes: T[]): Record<string, T[]> {
  return nodes.reduce((acc, node) => {
    if (!acc[node.branchId]) {
      acc[node.branchId] = []
    }
    acc[node.branchId].push(node)
    return acc
  }, {} as Record<string, T[]>)
}
