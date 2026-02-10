import { useState } from 'react'
import { useAppStore } from '../store'
import './MemoryBrowser.css'

interface MemoryNode {
  id: string
  type: 'arc' | 'chapter' | 'scene' | 'thread'
  title: string
  summary: string
  children?: MemoryNode[]
  isStale?: boolean
  lastUpdated?: string
  status?: 'active' | 'resolved' | 'unresolved'
}

export function MemoryBrowser() {
  const {
    memoryBrowserOpen,
    toggleMemoryBrowser,
  } = useAppStore()

  const [viewMode, setViewMode] = useState<'hierarchy' | 'threads'>('hierarchy')
  const [selectedLevel, setSelectedLevel] = useState<'arc' | 'chapter' | 'scene'>('chapter')
  const [expandedNodes, setExpandedNodes] = useState<string[]>(['root'])
  const [selectedNode, setSelectedNode] = useState<string | null>(null)

  // Mock hierarchical memory data
  const memoryData: MemoryNode[] = [
    {
      id: 'arc-1',
      type: 'arc',
      title: 'The Beginning',
      summary: 'Introduction to the world and main characters. Establishing the central conflict.',
      lastUpdated: '2024-01-15T10:00:00Z',
      children: [
        {
          id: 'chapter-1',
          type: 'chapter',
          title: 'Chapter 1: Arrival',
          summary: 'The protagonist arrives in the mysterious town. Meets key characters.',
          lastUpdated: '2024-01-15T10:00:00Z',
          children: [
            {
              id: 'scene-1-1',
              type: 'scene',
              title: 'The Journey',
              summary: 'Traveling through the forest, protagonist reflects on past decisions.',
              lastUpdated: '2024-01-14T16:30:00Z',
            },
            {
              id: 'scene-1-2',
              type: 'scene',
              title: 'First Encounter',
              summary: 'Meeting the mysterious stranger at the town gates.',
              lastUpdated: '2024-01-15T10:00:00Z',
              isStale: true,
            },
          ],
        },
        {
          id: 'chapter-2',
          type: 'chapter',
          title: 'Chapter 2: Revelations',
          summary: 'Secrets are revealed. The true nature of the threat becomes clear.',
          lastUpdated: '2024-01-16T14:20:00Z',
          children: [
            {
              id: 'scene-2-1',
              type: 'scene',
              title: 'The Library',
              summary: 'Discovering ancient texts that hint at the coming danger.',
              lastUpdated: '2024-01-16T14:20:00Z',
            },
          ],
        },
      ],
    },
  ]

  // Mock thread data
  const threadData: MemoryNode[] = [
    {
      id: 'thread-1',
      type: 'thread',
      title: 'The Prophecy',
      summary: 'Ancient prophecy about the end of times. Scattered clues throughout.',
      status: 'unresolved',
      lastUpdated: '2024-01-16T14:20:00Z',
    },
    {
      id: 'thread-2',
      type: 'thread',
      title: 'Missing Artifact',
      summary: 'Powerful artifact that went missing years ago. Connected to main antagonist.',
      status: 'active',
      lastUpdated: '2024-01-15T10:00:00Z',
    },
    {
      id: 'thread-3',
      type: 'thread',
      title: 'Character Backstory',
      summary: 'Protagonist mysterious past slowly being revealed through flashbacks.',
      status: 'active',
      lastUpdated: '2024-01-14T16:30:00Z',
    },
    {
      id: 'thread-4',
      type: 'thread',
      title: 'The Betrayal',
      summary: 'Trusted ally revealed to be working with the enemy. Resolved.',
      status: 'resolved',
      lastUpdated: '2024-01-10T09:00:00Z',
    },
  ]

  if (!memoryBrowserOpen) return null

  const toggleNode = (id: string) => {
    setExpandedNodes(prev =>
      prev.includes(id) ? prev.filter(n => n !== id) : [...prev, id]
    )
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    return date.toLocaleDateString()
  }

  const isStale = (dateStr?: string) => {
    if (!dateStr) return false
    const date = new Date(dateStr)
    const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
    return date < weekAgo
  }

  const renderMemoryNode = (node: MemoryNode, level: number = 0) => {
    const isExpanded = expandedNodes.includes(node.id)
    const hasChildren = node.children && node.children.length > 0
    const isSelected = selectedNode === node.id
    const stale = node.isStale || isStale(node.lastUpdated)

    return (
      <div key={node.id} className={`memory-node level-${level} ${isSelected ? 'selected' : ''}`}>
        <div
          className={`memory-node-header ${stale ? 'stale' : ''}`}
          onClick={() => setSelectedNode(node.id)}
        >
          {hasChildren && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                toggleNode(node.id)
              }}
              className="expand-btn"
            >
              {isExpanded ? '▼' : '▶'}
            </button>
          )}
          
          <span className="node-icon">
            {node.type === 'arc' && '📚'}
            {node.type === 'chapter' && '📖'}
            {node.type === 'scene' && '🎬'}
            {node.type === 'thread' && '🧵'}
          </span>
          
          <div className="node-info">
            <span className="node-title">{node.title}</span>
            <span className="node-meta">
              {stale && <span className="stale-badge">⚠️ Stale</span>}
              {node.lastUpdated && <span>Updated {formatDate(node.lastUpdated)}</span>}
            </span>
          </div>
          
          {node.status && (
            <span className={`status-badge ${node.status}`}>
              {node.status}
            </span>
          )}
        </div>
        
        {isSelected && (
          <div className="node-details">
            <p className="node-summary">{node.summary}</p>
            <div className="node-actions">
              <button className="edit-btn">✏️ Edit Summary</button>
              <button className="refresh-btn">🔄 Refresh</button>
              {node.type === 'thread' && node.status === 'unresolved' && (
                <button className="resolve-btn">✓ Mark Resolved</button>
              )}
            </div>
          </div>
        )}
        
        {hasChildren && isExpanded && (
          <div className="node-children">
            {node.children!.map(child => renderMemoryNode(child, level + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="memory-browser" role="region" aria-labelledby="memory-title">
      <div className="panel-header">
        <h2 id="memory-title" className="panel-title">🧠 Memory</h2>
        <button
          onClick={toggleMemoryBrowser}
          className="close-button"
          aria-label="Close memory browser"
        >
          ×
        </button>
      </div>

      <div className="memory-content">
        {/* View Toggle */}
        <div className="view-toggle">
          <button
            onClick={() => setViewMode('hierarchy')}
            className={viewMode === 'hierarchy' ? 'active' : ''}
          >
            📚 Hierarchy
          </button>
          <button
            onClick={() => setViewMode('threads')}
            className={viewMode === 'threads' ? 'active' : ''}
          >
            🧵 Threads
          </button>
        </div>

        {viewMode === 'hierarchy' && (
          <>
            {/* Level Filter */}
            <div className="level-filter">
              <label>View Level:</label>
              <div className="level-buttons">
                {(['arc', 'chapter', 'scene'] as const).map(level => (
                  <button
                    key={level}
                    onClick={() => setSelectedLevel(level)}
                    className={selectedLevel === level ? 'active' : ''}
                  >
                    {level.charAt(0).toUpperCase() + level.slice(1)}s
                  </button>
                ))}
              </div>
            </div>

            {/* Breadcrumb */}
            <div className="breadcrumb">
              <span className="breadcrumb-item active">Story</span>
              <span className="breadcrumb-separator">›</span>
              <span className="breadcrumb-item">{selectedLevel}s</span>
            </div>

            {/* Memory Tree */}
            <div className="memory-tree">
              {memoryData.map(node => renderMemoryNode(node))}
            </div>
          </>
        )}

        {viewMode === 'threads' && (
          <>
            {/* Thread Stats */}
            <div className="thread-stats">
              <div className="stat-item">
                <span className="stat-value">{threadData.length}</span>
                <span className="stat-label">Total</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">
                  {threadData.filter(t => t.status === 'active').length}
                </span>
                <span className="stat-label">Active</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">
                  {threadData.filter(t => t.status === 'unresolved').length}
                </span>
                <span className="stat-label">Unresolved</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">
                  {threadData.filter(t => t.status === 'resolved').length}
                </span>
                <span className="stat-label">Resolved</span>
              </div>
            </div>

            {/* Thread List */}
            <div className="thread-list">
              {threadData.map(thread => renderMemoryNode(thread))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
