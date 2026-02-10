import { useEffect, useRef, useCallback } from 'react'
import { useAppStore } from '../store'
import './GraphCanvas.css'

export function GraphCanvas() {
  const canvasRef = useRef<HTMLDivElement>(null)
  const {
    nodes,
    selectedNodeId,
    zoom,
    setZoom,
    setViewport,
    selectNode,
    graphMetrics,
  } = useAppStore()

  // Handle zoom with mouse wheel + ctrl
  const handleWheel = useCallback((e: WheelEvent) => {
    if (e.ctrlKey) {
      e.preventDefault()
      const delta = e.deltaY > 0 ? -0.1 : 0.1
      const newZoom = Math.max(0.25, Math.min(3, zoom + delta))
      setZoom(newZoom)
    }
  }, [zoom, setZoom])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    canvas.addEventListener('wheel', handleWheel, { passive: false })
    
    // Update viewport size
    const updateViewport = () => {
      const rect = canvas.getBoundingClientRect()
      setViewport({
        x: 0,
        y: 0,
        width: rect.width,
        height: rect.height,
      })
    }
    
    updateViewport()
    window.addEventListener('resize', updateViewport)
    
    return () => {
      canvas.removeEventListener('wheel', handleWheel)
      window.removeEventListener('resize', updateViewport)
    }
  }, [handleWheel, setViewport])

  // Get zoom mode label
  const getZoomModeLabel = () => {
    if (zoom < 0.75) return 'Overview'
    if (zoom < 1.6) return 'Scene'
    return 'Detail'
  }

  return (
    <div 
      ref={canvasRef}
      className="graph-canvas"
      role="region"
      aria-label="Story graph canvas"
    >
      {/* Grid background */}
      <div 
        className="graph-grid"
        style={{
          backgroundSize: `${20 * zoom}px ${20 * zoom}px`,
        }}
      />
      
      {/* Graph content */}
      <div 
        className="graph-content"
        style={{
          transform: `scale(${zoom})`,
          transformOrigin: 'top left',
        }}
      >
        {nodes.length === 0 ? (
          <div className="graph-empty" role="status" aria-live="polite">
            <p>No nodes yet. Create a branch to start.</p>
            <p className="graph-hint">Use the Branch Panel on the left</p>
          </div>
        ) : (
          nodes.map(node => (
            <div
              key={node.id}
              className={`graph-node ${selectedNodeId === node.id ? 'selected' : ''}`}
              style={{
                left: node.x,
                top: node.y,
              }}
              onClick={() => selectNode(node.id)}
              role="button"
              tabIndex={0}
              aria-label={`Node ${node.label} in ${node.branchId}`}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  selectNode(node.id)
                }
              }}
            >
              <span className="node-label">{node.label}</span>
              <span className="node-branch">{node.branchId}</span>
            </div>
          ))
        )}
      </div>
      
      {/* Zoom controls */}
      <div className="graph-controls" role="group" aria-label="Zoom controls">
        <button 
          onClick={() => setZoom(Math.max(0.25, zoom - 0.25))}
          aria-label="Zoom out"
          title="Zoom out (Ctrl + scroll)"
        >
          −
        </button>
        <span className="zoom-level" aria-live="polite">
          {Math.round(zoom * 100)}% ({getZoomModeLabel()})
        </span>
        <button 
          onClick={() => setZoom(Math.min(3, zoom + 0.25))}
          aria-label="Zoom in"
          title="Zoom in (Ctrl + scroll)"
        >
          +
        </button>
      </div>
      
      {/* Metrics overlay */}
      {graphMetrics && (
        <div className="graph-metrics" role="status" aria-label="Graph performance metrics">
          <span 
            className={`metric ${graphMetrics.performanceUsable ? 'good' : 'warning'}`}
            title="Virtualization ratio"
          >
            [V] {(graphMetrics.virtualizationRatio * 100).toFixed(0)}%
          </span>
          <span 
            className={`metric ${graphMetrics.estimatedFrameMs <= 16 ? 'good' : 'warning'}`}
            title="Estimated frame time"
          >
            [F] {graphMetrics.estimatedFrameMs.toFixed(1)}ms
          </span>
          <span className="metric">
            [M] {graphMetrics.mode}
          </span>
        </div>
      )}
    </div>
  )
}
