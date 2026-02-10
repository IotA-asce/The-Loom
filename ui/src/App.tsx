import { useEffect, useState, useCallback } from 'react'
import { GraphCanvas } from './components/GraphCanvas'
import { TunerPanel } from './components/TunerPanel'
import { DualView } from './components/DualView'
import { BranchPanel } from './components/BranchPanel'
import { ImportPanel } from './components/ImportPanel'
import { SceneMetadata } from './components/SceneMetadata'
import { ReadingView } from './components/ReadingView'
import { WriterPanel } from './components/WriterPanel'
import { ArtistPanel } from './components/ArtistPanel'
import { SearchPanel } from './components/SearchPanel'
import { MemoryBrowser } from './components/MemoryBrowser'
import { ConsequenceSimulator } from './components/ConsequenceSimulator'
import { ToneHeatmap } from './components/ToneHeatmap'
import { StatusBar } from './components/StatusBar'
import { ToastContainer } from './components/Toast'
import { ErrorBoundary } from './components/ErrorBoundary'
import { OnboardingModal } from './components/OnboardingModal'
import { TutorialOverlay, useTutorial, type TutorialStep } from './components/TutorialOverlay'
import { TemplateGallery } from './components/TemplateGallery'
import { useAppStore } from './store'
import { useIsMobile } from './hooks/useMediaQuery'
import type { Template } from './components/TemplateGallery'
import { NodeSearch } from './components/NodeSearch'
import { CharacterGallery } from './components/CharacterGallery'
import { QCDashboard } from './components/QCDashboard'
import './App.css'

// Tutorial steps configuration
const TUTORIAL_STEPS: TutorialStep[] = [
  {
    target: '.app-header',
    title: 'Welcome to The Loom',
    content: 'This is your story workspace. Use the toolbar to access writing, art, and analysis tools.',
    position: 'bottom',
  },
  {
    target: '.sidebar-tabs',
    title: 'Manage Your Story',
    content: 'Switch between branches, metadata editing, and file import here.',
    position: 'right',
  },
  {
    target: '.app-content',
    title: 'Visualize Your Narrative',
    content: 'Your story graph lives here. Click nodes to select, drag to reposition, and use arrow keys to navigate.',
    position: 'left',
  },
  {
    target: '.nav-button[title="Writer (Generate Text)"]',
    title: 'AI Writing Assistant',
    content: 'Generate text with style consistency, character voices, and context awareness.',
    position: 'bottom',
  },
  {
    target: '.nav-button[title="Artist (Generate Images)"]',
    title: 'Visual Storytelling',
    content: 'Create manga panels with scene blueprints, atmosphere controls, and continuity management.',
    position: 'bottom',
  },
  {
    target: '.app-nav',
    title: 'Explore More Tools',
    content: 'Search your story, browse memory hierarchies, simulate changes, and analyze tone.',
    position: 'bottom',
  },
]

function App() {
  const { 
    initialize, 
    keyboardShortcuts,
    selectedNodeId,
    toggleReadingMode,
    showNodePreview,
    toggleNodePreview,
    addToast,
  } = useAppStore()
  
  const [sidebarTab, setSidebarTab] = useState<'branches' | 'import' | 'metadata'>('branches')
  const [showShortcuts, setShowShortcuts] = useState(false)
  const [showOnboarding, setShowOnboarding] = useState(false)
  const [showTemplates, setShowTemplates] = useState(false)
  const [showNodeSearch, setShowNodeSearch] = useState(false)
  const [showCharacterGallery, setShowCharacterGallery] = useState(false)
  const [showQCDashboard, setShowQCDashboard] = useState(false)
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)
  const [mobilePanelOpen, setMobilePanelOpen] = useState(false)
  const isMobile = useIsMobile()
  
  // Get navigation history from store
  const { 
    recentNodes, 
    navigationHistory, 
    historyIndex, 
    navigateHistory,
    clearHistory,
    selectNode,
    nodes 
  } = useAppStore()
  
  // Tutorial state
  const { 
    isActive: tutorialActive, 
    start: startTutorial, 
    complete: completeTutorial,
    skip: skipTutorial,
  } = useTutorial({
    steps: TUTORIAL_STEPS,
    onComplete: () => {
      addToast({ message: 'Tutorial complete! Happy weaving 🧵', type: 'success' })
      localStorage.setItem('loom:tutorialComplete', 'true')
    },
    onSkip: () => {
      addToast({ message: 'Tutorial skipped. You can restart it anytime from Help.', type: 'info' })
    },
  })

  useEffect(() => {
    initialize()
    
    // Check if user has seen onboarding
    const hasSeenOnboarding = localStorage.getItem('loom:onboardingComplete')
    const hasSeenTutorial = localStorage.getItem('loom:tutorialComplete')
    
    if (!hasSeenOnboarding) {
      setShowOnboarding(true)
    } else if (!hasSeenTutorial) {
      // Auto-start tutorial for returning users who skipped it
      setTimeout(() => startTutorial(), 500)
    }
  }, [initialize, startTutorial])
  
  const handleOnboardingClose = useCallback(() => {
    setShowOnboarding(false)
  }, [])
  
  const handleDontShowAgain = useCallback(() => {
    localStorage.setItem('loom:onboardingComplete', 'true')
    setShowOnboarding(false)
    // Start tutorial after onboarding
    setTimeout(() => startTutorial(), 300)
  }, [startTutorial])
  
  const handleImportTemplate = useCallback((template: Template) => {
    addToast({ message: `Importing "${template.name}"...`, type: 'info' })
    // Template import logic would go here
    setTimeout(() => {
      addToast({ message: `Template "${template.name}" imported successfully!`, type: 'success' })
      setShowTemplates(false)
    }, 1500)
  }, [addToast])

  // Keyboard shortcuts handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Skip if typing in input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return
      }

      const key = `${e.ctrlKey ? 'ctrl+' : ''}${e.key.toLowerCase()}`
      const action = keyboardShortcuts[key]
      
      if (action) {
        e.preventDefault()
        action()
      }
      
      // Toggle shortcuts help
      if (e.ctrlKey && e.key === '?') {
        e.preventDefault()
        setShowShortcuts(true)
      }
      
      // Toggle node search
      if (e.ctrlKey && e.key.toLowerCase() === 'f') {
        e.preventDefault()
        setShowNodeSearch(true)
      }
      
      // Navigate back
      if (e.altKey && e.key === 'ArrowLeft') {
        e.preventDefault()
        navigateHistory('back')
      }
      
      // Navigate forward
      if (e.altKey && e.key === 'ArrowRight') {
        e.preventDefault()
        navigateHistory('forward')
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [keyboardShortcuts])
  
  // Auto-switch to metadata tab when node selected
  useEffect(() => {
    if (selectedNodeId && sidebarTab !== 'import') {
      setSidebarTab('metadata')
    }
  }, [selectedNodeId])

  return (
    <ErrorBoundary>
    <div className="app" role="application" aria-label="The Loom Story Editor">
      {/* Toast Notifications */}
      <ToastContainer />
      
      {/* Reading View Overlay */}
      <ReadingView />
      
      {/* Onboarding Modal */}
      <OnboardingModal
        isOpen={showOnboarding}
        onClose={handleOnboardingClose}
        onDontShowAgain={handleDontShowAgain}
      />
      
      {/* Tutorial Overlay */}
      <TutorialOverlay
        isActive={tutorialActive}
        steps={TUTORIAL_STEPS}
        onComplete={completeTutorial}
        onSkip={skipTutorial}
      />
      
      {/* Template Gallery */}
      <TemplateGallery
        isOpen={showTemplates}
        onClose={() => setShowTemplates(false)}
        onImport={handleImportTemplate}
      />
      
      {/* Node Search */}
      <NodeSearch
        isOpen={showNodeSearch}
        onClose={() => setShowNodeSearch(false)}
      />
      
      {/* Character Gallery */}
      <CharacterGallery
        isOpen={showCharacterGallery}
        onClose={() => setShowCharacterGallery(false)}
      />
      
      {/* QC Dashboard */}
      <QCDashboard
        isOpen={showQCDashboard}
        onClose={() => setShowQCDashboard(false)}
      />
      
      {/* Shortcuts Help Modal */}
      {showShortcuts && (
        <div 
          className="shortcuts-modal"
          onClick={() => setShowShortcuts(false)}
        >
          <div className="shortcuts-content" onClick={e => e.stopPropagation()}>
            <h2>Keyboard Shortcuts</h2>
            <div className="shortcuts-grid">
              <div className="shortcut-item">
                <kbd>←</kbd><kbd>↑</kbd><kbd>↓</kbd><kbd>→</kbd>
                <span>Navigate between nodes</span>
              </div>
              <div className="shortcut-item">
                <kbd>Enter</kbd>
                <span>Edit selected node</span>
              </div>
              <div className="shortcut-item">
                <kbd>Delete</kbd>
                <span>Delete selected node</span>
              </div>
              <div className="shortcut-item">
                <kbd>Ctrl</kbd>+<kbd>N</kbd>
                <span>Create new node</span>
              </div>
              <div className="shortcut-item">
                <kbd>Ctrl</kbd>+<kbd>Z</kbd>
                <span>Undo</span>
              </div>
              <div className="shortcut-item">
                <kbd>Ctrl</kbd>+<kbd>Y</kbd>
                <span>Redo</span>
              </div>
              <div className="shortcut-item">
                <kbd>Ctrl</kbd>+<kbd>S</kbd>
                <span>Save checkpoint</span>
              </div>
              <div className="shortcut-item">
                <kbd>Ctrl</kbd>+<kbd>T</kbd>
                <span>Toggle tuner panel</span>
              </div>
              <div className="shortcut-item">
                <kbd>Ctrl</kbd>+<kbd>D</kbd>
                <span>Toggle dual view</span>
              </div>
              <div className="shortcut-item">
                <kbd>Ctrl</kbd>+<kbd>R</kbd>
                <span>Toggle reading mode</span>
              </div>
              <div className="shortcut-item">
                <kbd>Ctrl</kbd>+<kbd>?</kbd>
                <span>Show this help</span>
              </div>
              <div className="shortcut-item">
                <kbd>Escape</kbd>
                <span>Cancel / Close</span>
              </div>
              <div className="shortcut-item">
                <kbd>Ctrl</kbd>+<kbd>H</kbd>
                <span>Restart tutorial</span>
              </div>
              <div className="shortcut-item">
                <kbd>Ctrl</kbd>+<kbd>F</kbd>
                <span>Find node</span>
              </div>
              <div className="shortcut-item">
                <kbd>Alt</kbd>+<kbd>←</kbd>
                <span>Navigate back</span>
              </div>
              <div className="shortcut-item">
                <kbd>Alt</kbd>+<kbd>→</kbd>
                <span>Navigate forward</span>
              </div>
            </div>
            <div className="shortcuts-footer">
              <button 
                className="secondary-button"
                onClick={() => {
                  setShowShortcuts(false)
                  setShowTemplates(true)
                }}
              >
                📚 Template Gallery
              </button>
              <button 
                className="secondary-button"
                onClick={() => {
                  setShowShortcuts(false)
                  startTutorial()
                }}
              >
                🎓 Start Tutorial
              </button>
              <button 
                className="close-button"
                onClick={() => setShowShortcuts(false)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      <header className="app-header">
        <div className="app-header-left">
          {isMobile && (
            <button
              className="mobile-menu-toggle"
              onClick={() => setMobileSidebarOpen(!mobileSidebarOpen)}
              aria-label="Toggle sidebar"
              aria-expanded={mobileSidebarOpen}
            >
              ☰
            </button>
          )}
          <h1>🧵 The Loom</h1>
        </div>
        <nav className="app-nav" aria-label="Main navigation">
          <button 
            className="nav-button" 
            onClick={() => toggleReadingMode()}
            aria-label="Toggle reading mode (Ctrl+R)"
            title="Reading Mode (Ctrl+R)"
          >
            📖 Read
          </button>
          <button 
            className="nav-button" 
            onClick={() => useAppStore.getState().toggleWriterPanel()}
            aria-label="Open writer panel"
            title="Writer (Generate Text)"
          >
            ✍️ Write
          </button>
          <button 
            className="nav-button" 
            onClick={() => useAppStore.getState().toggleArtistPanel()}
            aria-label="Open artist panel"
            title="Artist (Generate Images)"
          >
            🎨 Art
          </button>
          <button 
            className="nav-button" 
            onClick={() => useAppStore.getState().toggleSearchPanel()}
            aria-label="Open search panel"
            title="Search"
          >
            🔎 Search
          </button>
          <button 
            className="nav-button" 
            onClick={() => useAppStore.getState().toggleMemoryBrowser()}
            aria-label="Open memory browser"
            title="Memory Browser"
          >
            🧠 Memory
          </button>
          <button 
            className="nav-button" 
            onClick={() => useAppStore.getState().toggleSimulator()}
            aria-label="Open consequence simulator"
            title="What-If Simulator"
          >
            🔮 What-If
          </button>
          <button 
            className="nav-button" 
            onClick={() => useAppStore.getState().toggleToneHeatmap()}
            aria-label="Open tone analysis"
            title="Tone Analysis"
          >
            🎭 Tones
          </button>
          <button 
            className="nav-button" 
            onClick={() => useAppStore.getState().toggleTuner()}
            aria-label="Open tuner panel (Ctrl+T)"
            title="Tuner (Ctrl+T)"
          >
            ⚙️ Tuner
          </button>
          <button 
            className="nav-button" 
            onClick={() => useAppStore.getState().toggleDualView()}
            aria-label="Toggle dual view (Ctrl+D)"
            title="Dual View (Ctrl+D)"
          >
            🖼️ Dual View
          </button>
          <button 
            className="nav-button" 
            onClick={() => useAppStore.getState().createAutosave('manual')}
            aria-label="Save checkpoint (Ctrl+S)"
            title="Save (Ctrl+S)"
          >
            💾 Save
          </button>
          <button 
            className="nav-button" 
            onClick={() => setShowNodeSearch(true)}
            aria-label="Search nodes (Ctrl+F)"
            title="Find Node (Ctrl+F)"
          >
            🔍 Find
          </button>
          <button 
            className="nav-button" 
            onClick={() => setShowCharacterGallery(true)}
            aria-label="Character gallery"
            title="Characters"
          >
            🎭 Characters
          </button>
          <button 
            className="nav-button" 
            onClick={() => setShowQCDashboard(true)}
            aria-label="Quality Control"
            title="QC Dashboard"
          >
            🔍 QC
          </button>
          <button 
            className="nav-button" 
            onClick={() => navigateHistory('back')}
            disabled={historyIndex <= 0}
            aria-label="Go back (Alt+←)"
            title="Back (Alt+←)"
          >
            ← Back
          </button>
          <button 
            className="nav-button" 
            onClick={() => navigateHistory('forward')}
            disabled={historyIndex >= navigationHistory.length - 1}
            aria-label="Go forward (Alt+→)"
            title="Forward (Alt+→)"
          >
            → Fwd
          </button>
          <button 
            className="nav-button" 
            onClick={() => setShowTemplates(true)}
            aria-label="Template gallery"
            title="Templates"
          >
            📚 Templates
          </button>
          <button 
            className="nav-button" 
            onClick={() => startTutorial()}
            aria-label="Start tutorial"
            title="Tutorial"
          >
            🎓 Help
          </button>
          <button 
            className="nav-button" 
            onClick={() => setShowShortcuts(true)}
            aria-label="Keyboard shortcuts (Ctrl+?)"
            title="Shortcuts (Ctrl+?)"
          >
            ⌨️ ?
          </button>
          {isMobile && (
            <button
              className="mobile-panel-toggle"
              onClick={() => setMobilePanelOpen(!mobilePanelOpen)}
              aria-label="Toggle control panel"
              aria-expanded={mobilePanelOpen}
            >
              ⚙️
            </button>
          )}
        </nav>
      </header>

      <main className="app-main">
        <aside 
          className={`app-sidebar ${mobileSidebarOpen ? 'open' : ''}`} 
          aria-label="Left panel"
        >
          {isMobile && (
            <button
              className="mobile-sidebar-close"
              onClick={() => setMobileSidebarOpen(false)}
              aria-label="Close sidebar"
            >
              ×
            </button>
          )}
          <div className="sidebar-tabs" role="tablist" aria-label="Sidebar tabs">
            <button
              role="tab"
              aria-selected={sidebarTab === 'branches'}
              aria-controls="branches-panel"
              id="branches-tab"
              className={`sidebar-tab ${sidebarTab === 'branches' ? 'active' : ''}`}
              onClick={() => setSidebarTab('branches')}
            >
              🌿 Branches
            </button>
            <button
              role="tab"
              aria-selected={sidebarTab === 'metadata'}
              aria-controls="metadata-panel"
              id="metadata-tab"
              className={`sidebar-tab ${sidebarTab === 'metadata' ? 'active' : ''}`}
              onClick={() => setSidebarTab('metadata')}
            >
              📝 Metadata
            </button>
            <button
              role="tab"
              aria-selected={sidebarTab === 'import'}
              aria-controls="import-panel"
              id="import-tab"
              className={`sidebar-tab ${sidebarTab === 'import' ? 'active' : ''}`}
              onClick={() => setSidebarTab('import')}
            >
              📥 Import
            </button>
          </div>
          <div className="sidebar-content">
            {sidebarTab === 'branches' && (
              <div id="branches-panel" role="tabpanel" aria-labelledby="branches-tab">
                <BranchPanel />
                
                {/* Recent Nodes Section */}
                {recentNodes.length > 0 && (
                  <div className="recent-nodes-section">
                    <div className="recent-nodes-header">
                      <h3>Recent Nodes</h3>
                      <button 
                        className="clear-history-btn"
                        onClick={clearHistory}
                        aria-label="Clear history"
                      >
                        Clear
                      </button>
                    </div>
                    <ul className="recent-nodes-list">
                      {recentNodes.slice(0, 10).map(nodeId => {
                        const node = nodes.find(n => n.id === nodeId)
                        if (!node) return null
                        return (
                          <li 
                            key={nodeId}
                            className={`recent-node-item ${selectedNodeId === nodeId ? 'selected' : ''}`}
                            onClick={() => {
                              selectNode(nodeId)
                              if (isMobile) setMobileSidebarOpen(false)
                            }}
                          >
                            <span className="recent-node-label">{node.label}</span>
                            {selectedNodeId === nodeId && <span className="current-indicator">●</span>}
                          </li>
                        )
                      })}
                    </ul>
                  </div>
                )}
              </div>
            )}
            {sidebarTab === 'metadata' && (
              <div id="metadata-panel" role="tabpanel" aria-labelledby="metadata-tab">
                {selectedNodeId ? (
                  <SceneMetadata nodeId={selectedNodeId} />
                ) : (
                  <div className="empty-panel">
                    <p>Select a node to view and edit its metadata</p>
                    <p className="hint">Use arrow keys to navigate the graph</p>
                  </div>
                )}
              </div>
            )}
            {sidebarTab === 'import' && (
              <div id="import-panel" role="tabpanel" aria-labelledby="import-tab">
                <ImportPanel />
              </div>
            )}
          </div>
        </aside>
        
        <section className={`app-content ${isMobile ? 'mobile' : ''}`} aria-label="Graph workspace">
          <GraphCanvas />
          
          {/* Floating toggle for node preview */}
          {!isMobile && (
            <div className="floating-toggles">
              <label className="toggle-label">
                <input
                  type="checkbox"
                  checked={showNodePreview}
                  onChange={toggleNodePreview}
                />
                <span>👁 Node Preview</span>
              </label>
            </div>
          )}
        </section>
        
        <aside 
          className={`app-panel ${mobilePanelOpen ? 'open' : ''}`} 
          aria-label="Control panel"
        >
          {isMobile && (
            <button
              className="mobile-panel-close"
              onClick={() => setMobilePanelOpen(false)}
              aria-label="Close panel"
            >
              ×
            </button>
          )}
          <SearchPanel />
          <MemoryBrowser />
          <ConsequenceSimulator />
          <ToneHeatmap />
          <WriterPanel />
          <ArtistPanel />
          <TunerPanel />
          <DualView />
        </aside>
      </main>

      <StatusBar />
    </div>
    </ErrorBoundary>
  )
}

export default App
