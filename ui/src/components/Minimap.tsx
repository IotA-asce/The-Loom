import { useRef, useCallback, useState, useEffect } from 'react'
import { useAppStore } from '../store'
import { useBookmarkStore } from '../stores/bookmarkStore'
import './Minimap.css'

interface MinimapProps {
  width?: number
  height?: number
}

export function Minimap({ width = 200, height = 150 }: MinimapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const { nodes, selectedNodeId, viewport, setViewport, zoom } = useAppStore()
  const { bookmarks } = useBookmarkStore()
  const [isDragging, setIsDragging] = useState(false)
  
  // Calculate bounds of all nodes
  const calculateBounds = useCallback(() => {
    if (nodes.length === 0) {
      return { minX: 0, minY: 0, maxX: width, maxY: height }
    }
    
    const padding = 50
    const minX = Math.min(...nodes.map(n => n.x)) - padding
    const minY = Math.min(...nodes.map(n => n.y)) - padding
    const maxX = Math.max(...nodes.map(n => n.x + 120)) + padding // 120 = node width
    const maxY = Math.max(...nodes.map(n => n.y + 50)) + padding // 50 = node height
    
    return { minX, minY, maxX, maxY }
  }, [nodes, width, height])
  
  // Scale coordinates from world to minimap
  const worldToMinimap = useCallback((x: number, y: number, bounds: { minX: number; minY: number; maxX: number; maxY: number }) => {
    const scaleX = width / (bounds.maxX - bounds.minX)
    const scaleY = height / (bounds.maxY - bounds.minY)
    const scale = Math.min(scaleX, scaleY)
    
    return {
      x: (x - bounds.minX) * scale,
      y: (y - bounds.minY) * scale,
      scale,
    }
  }, [width, height])
  
  // Scale coordinates from minimap to world
  const minimapToWorld = useCallback((mx: number, my: number, bounds: { minX: number; minY: number; maxX: number; maxY: number }) => {
    const scaleX = width / (bounds.maxX - bounds.minX)
    const scaleY = height / (bounds.maxY - bounds.minY)
    const scale = Math.min(scaleX, scaleY)
    
    return {
      x: mx / scale + bounds.minX,
      y: my / scale + bounds.minY,
    }
  }, [width, height])
  
  // Draw minimap
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    
    const bounds = calculateBounds()
    const { scale } = worldToMinimap(0, 0, bounds)
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height)
    
    // Draw background
    ctx.fillStyle = 'rgba(0, 0, 0, 0.3)'
    ctx.fillRect(0, 0, width, height)
    
    // Draw grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)'
    ctx.lineWidth = 1
    const gridSize = 20 * scale
    for (let x = 0; x < width; x += gridSize) {
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, height)
      ctx.stroke()
    }
    for (let y = 0; y < height; y += gridSize) {
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(width, y)
      ctx.stroke()
    }
    
    // Draw edges (simplified as lines)
    ctx.strokeStyle = 'rgba(136, 136, 136, 0.3)'
    ctx.lineWidth = 1
    // Note: Edges would need to come from edgeStore
    
    // Draw nodes
    nodes.forEach(node => {
      const pos = worldToMinimap(node.x + 60, node.y + 25, bounds)
      const isSelected = node.id === selectedNodeId
      const bookmark = bookmarks.find(b => b.nodeId === node.id)
      
      // Node body
      ctx.beginPath()
      ctx.arc(pos.x, pos.y, isSelected ? 5 : 3, 0, Math.PI * 2)
      ctx.fillStyle = bookmark?.color || (isSelected ? '#4a9eff' : '#888')
      ctx.fill()
      
      // Selection ring
      if (isSelected) {
        ctx.beginPath()
        ctx.arc(pos.x, pos.y, 7, 0, Math.PI * 2)
        ctx.strokeStyle = '#4a9eff'
        ctx.lineWidth = 2
        ctx.stroke()
      }
    })
    
    // Draw viewport rectangle
    const viewportPos = worldToMinimap(viewport.x, viewport.y, bounds)
    const viewportSize = {
      width: viewport.width / (bounds.maxX - bounds.minX) * width,
      height: viewport.height / (bounds.maxY - bounds.minY) * height,
    }
    
    // Clamp viewport rect to minimap bounds
    const clampedX = Math.max(0, Math.min(width - 10, viewportPos.x))
    const clampedY = Math.max(0, Math.min(height - 10, viewportPos.y))
    const clampedW = Math.min(width - clampedX, viewportSize.width / zoom)
    const clampedH = Math.min(height - clampedY, viewportSize.height / zoom)
    
    ctx.strokeStyle = '#4a9eff'
    ctx.lineWidth = 2
    ctx.strokeRect(clampedX, clampedY, clampedW, clampedH)
    
    ctx.fillStyle = 'rgba(74, 158, 255, 0.1)'
    ctx.fillRect(clampedX, clampedY, clampedW, clampedH)
    
  }, [nodes, selectedNodeId, viewport, zoom, bookmarks, calculateBounds, worldToMinimap, width, height])
  
  // Handle click to jump
  const handleClick = useCallback((e: React.MouseEvent) => {
    const container = containerRef.current
    if (!container) return
    
    const rect = container.getBoundingClientRect()
    const mx = e.clientX - rect.left
    const my = e.clientY - rect.top
    
    const bounds = calculateBounds()
    const worldPos = minimapToWorld(mx, my, bounds)
    
    // Center viewport on clicked position
    setViewport({
      ...viewport,
      x: worldPos.x - viewport.width / (2 * zoom),
      y: worldPos.y - viewport.height / (2 * zoom),
    })
  }, [calculateBounds, minimapToWorld, viewport, zoom, setViewport])
  
  // Handle drag to pan
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true)
    handleClick(e)
  }
  
  useEffect(() => {
    if (!isDragging) return
    
    const handleMouseMove = (e: MouseEvent) => {
      const container = containerRef.current
      if (!container) return
      
      const rect = container.getBoundingClientRect()
      const mx = e.clientX - rect.left
      const my = e.clientY - rect.top
      
      const bounds = calculateBounds()
      const worldPos = minimapToWorld(mx, my, bounds)
      
      setViewport({
        ...viewport,
        x: worldPos.x - viewport.width / (2 * zoom),
        y: worldPos.y - viewport.height / (2 * zoom),
      })
    }
    
    const handleMouseUp = () => {
      setIsDragging(false)
    }
    
    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseup', handleMouseUp)
    
    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isDragging, calculateBounds, minimapToWorld, viewport, zoom, setViewport])
  
  if (nodes.length === 0) return null
  
  return (
    <div 
      ref={containerRef}
      className="minimap"
      style={{ width, height }}
      onClick={handleClick}
      onMouseDown={handleMouseDown}
    >
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        className="minimap-canvas"
      />
      <div className="minimap-label">Overview</div>
    </div>
  )
}
