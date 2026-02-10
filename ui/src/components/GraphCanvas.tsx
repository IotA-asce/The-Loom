import { useEffect, useRef, useCallback, useState } from 'react'
import { useAppStore, type NodeType, type GraphNode } from '../store'
import { RichTextEditor } from './RichTextEditor'
import './GraphCanvas.css'

const NODE_TYPE_STYLES: Record<NodeType, { icon: string; color: string; shape: string }> = {
  chapter: { icon: '📚', color: '#4a9eff', shape: 'diamond' },
  scene: { icon: '🎬', color: '#4caf50', shape: 'circle' },
  beat: { icon: '🎵', color: '#ff9800', shape: 'square' },
  dialogue: { icon: '💬', color: '#9c27b0', shape: 'speech' },
}

export function GraphCanvas() {
  const canvasRef = useRef<HTMLDivElement>(null)
  const [previewNode, setPreviewNode] = useState<GraphNode | null>(null)
  const [previewPosition, setPreviewPosition] = useState({ x: 0, y: 0 })
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; nodeId: string } | null>(null)
  
  const {
    nodes,
    selectedNodeId,
    editingNodeId,
    showNodePreview,
    zoom,
    setZoom,
    setViewport,
    selectNode,
    startEditingNode,
    stopEditingNode,
    addNode,
    deleteNode,
    updateNodePosition,
    navigateGraph,
    graphMetrics,
    loading,
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

  // Handle keyboard navigation
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Skip if typing in input
    if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
      return
    }

    // Arrow keys for navigation
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
      e.preventDefault()
      const direction = e.key.replace('Arrow', '').toLowerCase() as 'up' | 'down' | 'left' | 'right'
      navigateGraph(direction)
    }
    
    // Enter to edit
    if (e.key === 'Enter' && !e.ctrlKey && !e.metaKey) {
      e.preventDefault()
      if (selectedNodeId && !editingNodeId) {
        startEditingNode(selectedNodeId)
      }
    }
    
    // Delete to remove
    if (e.key === 'Delete' || e.key === 'Backspace') {
      if (selectedNodeId && !editingNodeId) {
        e.preventDefault()
        if (confirm('Delete this node?')) {
          deleteNode(selectedNodeId)
        }
      }
    }
    
    // Escape to deselect or stop editing
    if (e.key === 'Escape') {
      if (editingNodeId) {
        stopEditingNode()
      } else if (selectedNodeId) {
        selectNode(null)
      }
    }
    
    // N for new node
    if (e.key === 'n' || e.key === 'N') {
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault()
        if (selectedNodeId) {
          const node = nodes.find(n => n.id === selectedNodeId)
          if (node) {
            addNode({
              label: 'New Node',
              branchId: node.branchId,
              sceneId: node.sceneId,
              x: node.x + 50,
              y: node.y + 50,
              importance: 0.5,
            })
          }
        } else {
          // Add node at center
          addNode({
            label: 'New Node',
            branchId: 'main',
            sceneId: 'default',
            x: 100,
            y: 100,
            importance: 0.5,
          })
        }
      }
    }
  }, [selectedNodeId, editingNodeId, nodes, navigateGraph, startEditingNode, stopEditingNode, deleteNode, selectNode, addNode])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    canvas.addEventListener('wheel', handleWheel, { passive: false })
    window.addEventListener('keydown', handleKeyDown)
    
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
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('resize', updateViewport)
    }
  }, [handleWheel, handleKeyDown, setViewport])

  // Handle node drag
  const handleMouseDown = (e: React.MouseEvent, nodeId: string) => {
    if (e.button !== 0) return // Only left click
    e.stopPropagation()
    
    const node = nodes.find(n => n.id === nodeId)
    if (!node) return
    
    const startX = e.clientX
    const startY = e.clientY
    const startNodeX = node.x
    const startNodeY = node.y
    
    const handleMouseMove = (e: MouseEvent) => {
      const dx = (e.clientX - startX) / zoom
      const dy = (e.clientY - startY) / zoom
      updateNodePosition(nodeId, startNodeX + dx, startNodeY + dy)
    }
    
    const handleMouseUp = () => {
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
    }
    
    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseup', handleMouseUp)
  }

  // Get zoom mode label
  const getZoomModeLabel = () => {
    if (zoom < 0.75) return 'Overview'
    if (zoom < 1.6) return 'Scene'
    return 'Detail'
  }

  // Handle double click to edit
  const handleDoubleClick = (e: React.MouseEvent, nodeId: string) => {
    e.stopPropagation()
    selectNode(nodeId)
    startEditingNode(nodeId)
  }

  // Handle hover for preview
  const handleMouseEnter = (e: React.MouseEvent, node: GraphNode) => {
    if (!showNodePreview || editingNodeId) return
    const rect = (e.target as HTMLElement).getBoundingClientRect()
    setPreviewNode(node)
    setPreviewPosition({ 
      x: rect.right + 10, 
      y: rect.top 
    })
  }

  const handleMouseLeave = () => {
    setPreviewNode(null)
  }

  // Handle right click for context menu
  const handleContextMenu = (e: React.MouseEvent, nodeId: string) => {
    e.preventDefault()
    setContextMenu({ x: e.clientX, y: e.clientY, nodeId })
  }

  // Close context menu on click elsewhere
  useEffect(() => {
    const handleClick = () => setContextMenu(null)
    window.addEventListener('click', handleClick)
    return () => window.removeEventListener('click', handleClick)
  }, [])

  // Render node based on type
  const renderNode = (node: GraphNode) => {
    const style = NODE_TYPE_STYLES[node.type] || NODE_TYPE_STYLES.scene
    const isSelected = selectedNodeId === node.id
    const isEditing = editingNodeId === node.id
    
    const nodeStyle: React.CSSProperties = {
      left: node.x,
      top: node.y,
      borderColor: style.color,
      backgroundColor: isSelected ? `${style.color}30` : `${style.color}15`,
    }

    return (
      <div
        key={node.id}
        className={`graph-node ${node.type} ${isSelected ? 'selected' : ''} ${isEditing ? 'editing' : ''}`}
        style={nodeStyle}
        onClick={(e) => { e.stopPropagation(); selectNode(node.id) }}
        onDoubleClick={(e) => handleDoubleClick(e, node.id)}
        onMouseDown={(e) => handleMouseDown(e, node.id)}
        onMouseEnter={(e) => handleMouseEnter(e, node)}
        onMouseLeave={handleMouseLeave}
        onContextMenu={(e) => handleContextMenu(e, node.id)}
        role="button"
        tabIndex={0}
        aria-label={`${style.icon} ${node.type} node: ${node.label}. ${node.content.wordCount} words. Press Enter to edit, Delete to remove.`}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            selectNode(node.id)
          }
        }}
      >
        <span className="node-icon">{style.icon}</span>
        <span className="node-label">{node.label}</span>
        {node.content.wordCount > 0 && (
          <span className="node-wordcount">{node.content.wordCount}w</span>
        )}
        <span className="node-branch">{node.branchId}</span>
        
        {/* Quick actions on hover */}
        <div className="node-actions">
          <button 
            onClick={(e) => { e.stopPropagation(); startEditingNode(node.id); }}
            className="node-action"
            title="Edit content"
          >
            ✏️
          </button>
          <button 
            onClick={(e) => { e.stopPropagation(); deleteNode(node.id); }}
            className="node-action"
            title="Delete"
          >
            🗑️
          </button>
        </div>
      </div>
    )
  }

  return (
    <>
      <div 
        ref={canvasRef}
        className="graph-canvas"
        role="region"
        aria-label="Story graph canvas. Use arrow keys to navigate, Enter to edit, Delete to remove."
        onClick={() => selectNode(null)}
      >
        {/* Loading overlay */}
        {loading.nodes && (
          <div className="canvas-loading" role="status">
            <div className="spinner" />
            <span>Loading nodes...</span>
          </div>
        )}

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
              <p>No nodes yet.</p>
              <p className="graph-hint">
                Press <kbd>Ctrl</kbd>+<kbd>N</kbd> to create a node, or use the Import tab to load a story.
              </p>
            </div>
          ) : (
            nodes.map(renderNode)
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
            <span className="metric">
              [N] {nodes.length}
            </span>
          </div>
        )}

        {/* Keyboard hints */}
        <div className="keyboard-hints" aria-label="Keyboard shortcuts">
          <span>←→↑↓ Navigate</span>
          <span>Enter Edit</span>
          <span>Del Delete</span>
          <span>Ctrl+N New</span>
          <span>Ctrl+? Help</span>
        </div>
      </div>

      {/* Node content preview popup */}
      {previewNode && showNodePreview && !editingNodeId && (
        <div 
          className="node-preview-popup"
          style={{
            left: previewPosition.x,
            top: previewPosition.y,
          }}
          role="tooltip"
        >
          <div className="preview-header">
            <span className="preview-type">{NODE_TYPE_STYLES[previewNode.type].icon} {previewNode.type}</span>
            <span className="preview-title">{previewNode.metadata.title || previewNode.label}</span>
          </div>
          <div className="preview-content">
            {previewNode.content.text ? (
              previewNode.content.text.slice(0, 300) + 
              (previewNode.content.text.length > 300 ? '...' : '')
            ) : (
              <em className="empty-preview">No content</em>
            )}
          </div>
          <div className="preview-meta">
            {previewNode.metadata.location && (
              <span>📍 {previewNode.metadata.location}</span>
            )}
            {previewNode.metadata.timeOfDay && (
              <span>🕐 {previewNode.metadata.timeOfDay}</span>
            )}
            <span>{previewNode.content.wordCount} words</span>
          </div>
        </div>
      )}

      {/* Context menu */}
      {contextMenu && (
        <div 
          className="context-menu"
          style={{ left: contextMenu.x, top: contextMenu.y }}
          role="menu"
        >
          <button 
            onClick={() => { startEditingNode(contextMenu.nodeId); setContextMenu(null); }}
            role="menuitem"
          >
            ✏️ Edit Content
          </button>
          <button 
            onClick={() => { selectNode(contextMenu.nodeId); setContextMenu(null); }}
            role="menuitem"
          >
            👁 Select Node
          </button>
          <div className="menu-divider" />
          <button 
            onClick={() => { 
              const node = nodes.find(n => n.id === contextMenu.nodeId)
              if (node) {
                addNode({
                  label: 'New Node',
                  branchId: node.branchId,
                  sceneId: node.sceneId,
                  x: node.x + 50,
                  y: node.y + 50,
                })
              }
              setContextMenu(null)
            }}
            role="menuitem"
          >
            ➕ Add Connected Node
          </button>
          <div className="menu-divider" />
          <button 
            onClick={() => { deleteNode(contextMenu.nodeId); setContextMenu(null); }}
            role="menuitem"
            className="danger"
          >
            🗑️ Delete Node
          </button>
        </div>
      )}

      {/* Inline editor modal */}
      {editingNodeId && (
        <div 
          className="editor-modal-overlay"
          onClick={(e) => { if (e.target === e.currentTarget) stopEditingNode(); }}
        >
          <div className="editor-modal">
            <RichTextEditor 
              nodeId={editingNodeId}
              onSave={() => stopEditingNode()}
              onCancel={() => stopEditingNode()}
            />
          </div>
        </div>
      )}
    </>
  )
}
