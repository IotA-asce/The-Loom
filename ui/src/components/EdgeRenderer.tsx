import { useEffect, useRef, useCallback } from 'react'
import { useEdgeStore, type Edge, type EdgeType, type LineStyle } from '../stores/edgeStore'
import { useAppStore } from '../store'
import './EdgeRenderer.css'

// Edge type styles
const EDGE_TYPE_STYLES: Record<EdgeType, { color: string; arrowhead: string }> = {
  causal: { color: '#4a9eff', arrowhead: 'url(#arrow-causal)' },
  temporal: { color: '#4caf50', arrowhead: 'url(#arrow-temporal)' },
  parallel: { color: '#ff9800', arrowhead: 'url(#arrow-parallel)' },
}

interface EdgeRendererProps {
  width: number
  height: number
  zoom: number
}

export function EdgeRenderer({ width, height, zoom }: EdgeRendererProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const { nodes, selectedNodeId } = useAppStore()
  const {
    edges,
    edgeCreation,
    defaultColor,
    startEdgeCreation,
    updateEdgeCreationPosition,
    setEdgeCreationTarget,
    completeEdgeCreation,
    cancelEdgeCreation,
  } = useEdgeStore()
  
  // Get node position considering zoom
  const getNodeCenter = useCallback((nodeId: string) => {
    const node = nodes.find(n => n.id === nodeId)
    if (!node) return null
    return {
      x: node.x + 60, // Approximate center (node width ~120)
      y: node.y + 25, // Approximate center (node height ~50)
    }
  }, [nodes])
  
  // Handle mouse move during edge creation
  useEffect(() => {
    if (!edgeCreation.isCreating) return
    
    const handleMouseMove = (e: MouseEvent) => {
      const svg = svgRef.current
      if (!svg) return
      
      const rect = svg.getBoundingClientRect()
      const x = (e.clientX - rect.left) / zoom
      const y = (e.clientY - rect.top) / zoom
      
      updateEdgeCreationPosition(x, y)
      
      // Check for node hover (snap target)
      let targetNodeId: string | null = null
      nodes.forEach(node => {
        const nodeCenter = getNodeCenter(node.id)
        if (!nodeCenter) return
        
        const dx = x - nodeCenter.x
        const dy = y - nodeCenter.y
        const distance = Math.sqrt(dx * dx + dy * dy)
        
        if (distance < 40 && node.id !== edgeCreation.sourceNodeId) {
          targetNodeId = node.id
        }
      })
      
      setEdgeCreationTarget(targetNodeId)
    }
    
    const handleMouseUp = () => {
      completeEdgeCreation()
    }
    
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        cancelEdgeCreation()
      }
    }
    
    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseup', handleMouseUp)
    window.addEventListener('keydown', handleKeyDown)
    
    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [edgeCreation.isCreating, edgeCreation.sourceNodeId, zoom, nodes, getNodeCenter, updateEdgeCreationPosition, setEdgeCreationTarget, completeEdgeCreation, cancelEdgeCreation])
  
  // Start edge creation from selected node
  const handleStartEdgeCreation = useCallback(() => {
    if (selectedNodeId) {
      startEdgeCreation(selectedNodeId)
    }
  }, [selectedNodeId, startEdgeCreation])
  
  // Get straight line path
  const getStraightPath = (source: { x: number; y: number }, target: { x: number; y: number }) => {
    return `M${source.x},${source.y}L${target.x},${target.y}`
  }
  
  // Get line style
  const getLineStyle = (style: LineStyle) => {
    switch (style) {
      case 'dashed':
        return '8,4'
      case 'dotted':
        return '2,2'
      default:
        return ''
    }
  }
  
  // Render edge
  const renderEdge = (edge: Edge) => {
    const source = getNodeCenter(edge.source)
    const target = getNodeCenter(edge.target)
    
    if (!source || !target) return null
    
    const typeStyle = EDGE_TYPE_STYLES[edge.type]
    const path = getStraightPath(source, target)
    
    return (
      <g key={edge.id} className="graph-edge">
        {/* Edge line */}
        <path
          d={path}
          stroke={edge.color || typeStyle.color}
          strokeWidth={2}
          fill="none"
          markerEnd={typeStyle.arrowhead}
          strokeDasharray={getLineStyle(edge.style)}
          className="edge-line"
        />
        
        {/* Edge label */}
        {edge.label && (
          <text
            x={(source.x + target.x) / 2}
            y={(source.y + target.y) / 2 - 8}
            fill={edge.color || typeStyle.color}
            fontSize={12}
            textAnchor="middle"
            className="edge-label"
          >
            {edge.label}
          </text>
        )}
        
        {/* Invisible wider line for easier hovering */}
        <path
          d={path}
          stroke="transparent"
          strokeWidth={15}
          fill="none"
          className="edge-hit-area"
          data-edge-id={edge.id}
        />
      </g>
    )
  }
  
  // Render preview line during edge creation
  const renderPreview = () => {
    if (!edgeCreation.isCreating || !edgeCreation.sourceNodeId) return null
    
    const source = getNodeCenter(edgeCreation.sourceNodeId)
    if (!source) return null
    
    const target = edgeCreation.targetNodeId
      ? getNodeCenter(edgeCreation.targetNodeId)
      : { x: edgeCreation.currentX, y: edgeCreation.currentY }
    
    if (!target) return null
    
    const path = getStraightPath(source, target)
    const isValid = edgeCreation.targetNodeId !== null
    
    return (
      <g className="edge-preview">
        <path
          d={path}
          stroke={isValid ? '#22c55e' : defaultColor}
          strokeWidth={2}
          fill="none"
          strokeDasharray="5,5"
          opacity={0.7}
          markerEnd={isValid ? 'url(#arrow-valid)' : 'url(#arrow-preview)'}
        />
        
        {/* Snap indicator */}
        {edgeCreation.targetNodeId && (
          <circle
            cx={target.x}
            cy={target.y}
            r={25}
            fill="none"
            stroke="#22c55e"
            strokeWidth={2}
            strokeDasharray="4,4"
            className="snap-indicator"
          />
        )}
      </g>
    )
  }
  
  return (
    <>
      {/* Edge creation button */}
      {selectedNodeId && !edgeCreation.isCreating && (
        <button
          className="edge-creation-button"
          onClick={handleStartEdgeCreation}
          title="Create connection from selected node"
        >
          🔗 Connect
        </button>
      )}
      
      {/* Cancel edge creation button */}
      {edgeCreation.isCreating && (
        <button
          className="edge-creation-button cancel"
          onClick={cancelEdgeCreation}
          title="Cancel connection (Esc)"
        >
          ✕ Cancel
        </button>
      )}
      
      <svg
        ref={svgRef}
        className="edge-layer"
        width={width}
        height={height}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          pointerEvents: edgeCreation.isCreating ? 'all' : 'none',
          zIndex: 5,
        }}
      >
        <defs>
          {/* Arrow markers */}
          <marker
            id="arrow-causal"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <path d="M0,0 L0,6 L9,3 z" fill="#4a9eff" />
          </marker>
          <marker
            id="arrow-temporal"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <path d="M0,0 L0,6 L9,3 z" fill="#4caf50" />
          </marker>
          <marker
            id="arrow-parallel"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <path d="M0,0 L0,6 L9,3 z" fill="#ff9800" />
          </marker>
          <marker
            id="arrow-preview"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <path d="M0,0 L0,6 L9,3 z" fill={defaultColor} opacity="0.5" />
          </marker>
          <marker
            id="arrow-valid"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <path d="M0,0 L0,6 L9,3 z" fill="#22c55e" />
          </marker>
        </defs>
        
        {/* Render existing edges */}
        {edges.map(renderEdge)}
        
        {/* Render preview line */}
        {renderPreview()}
      </svg>
    </>
  )
}
