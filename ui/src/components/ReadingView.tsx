import { useMemo } from 'react'
import { useAppStore } from '../store'
import './ReadingView.css'

export function ReadingView() {
  const {
    readingMode,
    readingBranchId,
    readingNodeId,
    readingPreferences,
    nodes,
    branches,
    characters,
    navigateReading,
    jumpToNodeInReading,
    exitReadingMode,
    updateReadingPreferences,
    selectNode,
  } = useAppStore()
  
  if (!readingMode) return null
  
  // Filter nodes by branch
  const branchNodes = useMemo(() => {
    return nodes
      .filter(n => n.branchId === readingBranchId)
      .sort((a, b) => {
        // Simple sorting by y position for demo
        if (Math.abs(a.y - b.y) < 50) return a.x - b.x
        return a.y - b.y
      })
  }, [nodes, readingBranchId])
  
  const currentNode = branchNodes.find(n => n.id === readingNodeId)
  const currentIndex = branchNodes.findIndex(n => n.id === readingNodeId)
  const currentBranch = branches.find(b => b.branchId === readingBranchId)
  
  // Safely get metadata with defaults
  const metadata = currentNode?.metadata || {
    title: '',
    location: '',
    timeOfDay: '',
    estimatedReadingTime: 0,
    moodTags: [],
  }
  
  // Safely get content with defaults
  const content = currentNode?.content || {
    text: '',
    version: 1,
    lastModified: new Date().toISOString(),
    wordCount: 0,
  }
  
  // Safely get characters
  const nodeCharacters = currentNode?.characters || []
  
  const progress = branchNodes.length > 0
    ? ((currentIndex + 1) / branchNodes.length) * 100
    : 0
  
  const getFontSize = () => {
    switch (readingPreferences.fontSize) {
      case 'small': return '0.9375rem'
      case 'large': return '1.25rem'
      default: return '1.0625rem'
    }
  }
  
  const getLineHeight = () => {
    switch (readingPreferences.lineSpacing) {
      case 'compact': return 1.5
      case 'relaxed': return 2
      default: return 1.7
    }
  }
  
  const getThemeClass = () => {
    return `theme-${readingPreferences.theme}`
  }
  
  const handleExit = () => {
    // Select the current node in the graph before exiting
    if (currentNode) {
      selectNode(currentNode.id)
    }
    exitReadingMode()
  }
  
  const handleNodeClick = (nodeId: string) => {
    jumpToNodeInReading(nodeId)
  }
  
  // Get character names for display
  const getCharacterNames = (characterIds: string[]) => {
    return characterIds
      .map(id => characters.find(c => c.id === id)?.name)
      .filter(Boolean)
      .join(', ') || 'None'
  }
  
  return (
    <div className={`reading-view ${getThemeClass()}`} role="region" aria-label="Reading mode">
      {/* Header */}
      <header className="reading-header">
        <div className="reading-header-left">
          <button 
            onClick={handleExit}
            className="exit-button"
            aria-label="Exit reading mode"
          >
            ← Back to Graph
          </button>
          <div className="reading-branch">
            <span className="branch-label">Branch:</span>
            <span className="branch-name">{currentBranch?.label || 'Main'}</span>
          </div>
        </div>
        
        <div className="reading-progress">
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="progress-text">
            {currentIndex + 1} / {branchNodes.length}
          </span>
        </div>
        
        <div className="reading-preferences">
          <div className="pref-group">
            <label htmlFor="font-size">Size</label>
            <select
              id="font-size"
              value={readingPreferences.fontSize}
              onChange={(e) => updateReadingPreferences({ fontSize: e.target.value as any })}
            >
              <option value="small">Small</option>
              <option value="medium">Medium</option>
              <option value="large">Large</option>
            </select>
          </div>
          
          <div className="pref-group">
            <label htmlFor="theme">Theme</label>
            <select
              id="theme"
              value={readingPreferences.theme}
              onChange={(e) => updateReadingPreferences({ theme: e.target.value as any })}
            >
              <option value="dark">Dark</option>
              <option value="light">Light</option>
              <option value="sepia">Sepia</option>
            </select>
          </div>
          
          <div className="pref-group">
            <label htmlFor="spacing">Spacing</label>
            <select
              id="spacing"
              value={readingPreferences.lineSpacing}
              onChange={(e) => updateReadingPreferences({ lineSpacing: e.target.value as any })}
            >
              <option value="compact">Compact</option>
              <option value="normal">Normal</option>
              <option value="relaxed">Relaxed</option>
            </select>
          </div>
        </div>
      </header>
      
      {/* Content */}
      <main 
        className="reading-content"
        style={{
          fontSize: getFontSize(),
          lineHeight: getLineHeight(),
        }}
      >
        {currentNode ? (
          <article className="reading-article">
            {/* Scene Header */}
            <header className="scene-header">
              {metadata.title && (
                <h1 className="scene-title">{metadata.title}</h1>
              )}
              
              <div className="scene-meta">
                {metadata.location && (
                  <span className="meta-item">
                    📍 {metadata.location}
                  </span>
                )}
                {metadata.timeOfDay && (
                  <span className="meta-item">
                    🕐 {metadata.timeOfDay}
                  </span>
                )}
                {nodeCharacters.length > 0 && (
                  <span className="meta-item">
                    👥 {getCharacterNames(nodeCharacters)}
                  </span>
                )}
              </div>
              
              {metadata.moodTags && metadata.moodTags.length > 0 && (
                <div className="scene-moods">
                  {metadata.moodTags.map(mood => (
                    <span key={mood} className="mood-badge">{mood}</span>
                  ))}
                </div>
              )}
            </header>
            
            {/* Scene Content */}
            <div className="scene-content">
              {content.text ? (
                content.text.split('\n\n').map((paragraph, i) => (
                  <p key={i} className="scene-paragraph">
                    {paragraph}
                  </p>
                ))
              ) : (
                <p className="empty-content">
                  This scene has no content yet. 
                  <button 
                    onClick={() => { exitReadingMode(); currentNode && selectNode(currentNode.id); }}
                    className="inline-link"
                  >
                    Edit this node
                  </button> 
                  to add content.
                </p>
              )}
            </div>
            
            {/* Scene Footer */}
            <footer className="scene-footer">
              <span className="word-count">
                {content.wordCount} words
              </span>
              <span className="reading-time">
                ~{Math.ceil(content.wordCount / 200)} min read
              </span>
            </footer>
          </article>
        ) : (
          <div className="empty-state">
            <p>No content available for this branch.</p>
          </div>
        )}
      </main>
      
      {/* Navigation */}
      <nav className="reading-nav" aria-label="Reading navigation">
        <button
          onClick={() => navigateReading('prev')}
          disabled={currentIndex <= 0}
          className="nav-button"
          aria-label="Previous scene"
        >
          ← Previous
        </button>
        
        {/* Chapter/Scene Jump */}
        <select
          value={readingNodeId || ''}
          onChange={(e) => handleNodeClick(e.target.value)}
          className="scene-jump"
          aria-label="Jump to scene"
        >
          {branchNodes.map((node, index) => (
            <option key={node.id} value={node.id}>
              {index + 1}. {node.metadata.title || node.label}
              {node.content.wordCount > 0 ? ` (${node.content.wordCount} words)` : ' (empty)'}
            </option>
          ))}
        </select>
        
        <button
          onClick={() => navigateReading('next')}
          disabled={currentIndex >= branchNodes.length - 1}
          className="nav-button"
          aria-label="Next scene"
        >
          Next →
        </button>
      </nav>
    </div>
  )
}
