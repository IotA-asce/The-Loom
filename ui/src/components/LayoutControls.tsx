import { useState } from 'react'
import { useEdgeStore, type LayoutConfig } from '../stores/edgeStore'
import { useAppStore } from '../store'
import './LayoutControls.css'

export function LayoutControls() {
  const { layout, setLayoutConfig, applyLayout } = useEdgeStore()
  const { nodes, updateNodePosition } = useAppStore()
  const [isApplying, setIsApplying] = useState(false)
  
  const layoutOptions: { type: LayoutConfig['type']; label: string; description: string; icon: string }[] = [
    { type: 'manual', label: 'Manual', description: 'Free positioning', icon: '✋' },
    { type: 'hierarchical', label: 'Hierarchical', description: 'Top-down tree', icon: '🌳' },
    { type: 'force', label: 'Force-Directed', description: 'Physics-based', icon: '🌐' },
    { type: 'circular', label: 'Circular', description: 'Radial layout', icon: '⭕' },
    { type: 'timeline', label: 'Timeline', description: 'Left-to-right', icon: '📅' },
  ]
  
  const handleApplyLayout = async () => {
    if (layout.config.type === 'manual' || nodes.length === 0) return
    
    setIsApplying(true)
    
    try {
      const newPositions = await applyLayout(
        layout.config.type,
        nodes.map(n => ({ id: n.id, x: n.x, y: n.y, branchId: n.branchId }))
      )
      
      // Animate to new positions
      if (layout.config.animate) {
        const duration = 500
        const startTime = performance.now()
        const startPositions = new Map(nodes.map(n => [n.id, { x: n.x, y: n.y }]))
        
        const animate = (currentTime: number) => {
          const elapsed = currentTime - startTime
          const progress = Math.min(elapsed / duration, 1)
          
          // Easing function (ease-out-cubic)
          const easeOut = 1 - Math.pow(1 - progress, 3)
          
          newPositions.forEach(({ id, x, y }) => {
            const start = startPositions.get(id)
            if (start) {
              const newX = start.x + (x - start.x) * easeOut
              const newY = start.y + (y - start.y) * easeOut
              updateNodePosition(id, newX, newY)
            }
          })
          
          if (progress < 1) {
            requestAnimationFrame(animate)
          }
        }
        
        requestAnimationFrame(animate)
      } else {
        // Immediate update
        newPositions.forEach(({ id, x, y }) => {
          updateNodePosition(id, x, y)
        })
      }
    } finally {
      setTimeout(() => setIsApplying(false), layout.config.animate ? 600 : 100)
    }
  }
  
  return (
    <div className="layout-controls">
      <div className="layout-header">
        <span className="layout-icon">📐</span>
        <span className="layout-title">Layout</span>
      </div>
      
      <div className="layout-selector">
        {layoutOptions.map(({ type, label, description, icon }) => (
          <button
            key={type}
            className={`layout-option ${layout.config.type === type ? 'active' : ''}`}
            onClick={() => setLayoutConfig({ type })}
            title={description}
          >
            <span className="layout-option-icon">{icon}</span>
            <span className="layout-option-label">{label}</span>
          </button>
        ))}
      </div>
      
      <div className="layout-options">
        <label className="layout-checkbox">
          <input
            type="checkbox"
            checked={layout.config.animate}
            onChange={(e) => setLayoutConfig({ animate: e.target.checked })}
          />
          <span>Animate transitions</span>
        </label>
        
        <label className="layout-checkbox">
          <input
            type="checkbox"
            checked={layout.config.branchClustering}
            onChange={(e) => setLayoutConfig({ branchClustering: e.target.checked })}
            disabled={layout.config.type === 'force'}
          />
          <span>Group by branch</span>
        </label>
      </div>
      
      <button
        className="layout-apply-btn"
        onClick={handleApplyLayout}
        disabled={layout.config.type === 'manual' || nodes.length === 0 || isApplying}
      >
        {isApplying ? (
          <>
            <span className="spinner-small" />
            Applying...
          </>
        ) : (
          <>
            <span>✨</span>
            Apply Layout
          </>
        )}
      </button>
    </div>
  )
}
