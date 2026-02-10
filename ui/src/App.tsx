import { useEffect, useState } from 'react'
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
import { useAppStore } from './store'
import './App.css'

function App() {
  const { 
    initialize, 
    keyboardShortcuts,
    selectedNodeId,
    toggleReadingMode,
    showNodePreview,
    toggleNodePreview,
  } = useAppStore()
  
  const [sidebarTab, setSidebarTab] = useState<'branches' | 'import' | 'metadata'>('branches')
  const [showShortcuts, setShowShortcuts] = useState(false)

  useEffect(() => {
    initialize()
  }, [initialize])

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
            </div>
            <button 
              className="close-button"
              onClick={() => setShowShortcuts(false)}
            >
              Close
            </button>
          </div>
        </div>
      )}

      <header className="app-header">
        <h1>🧵 The Loom</h1>
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
            onClick={() => setShowShortcuts(true)}
            aria-label="Keyboard shortcuts (Ctrl+?)"
            title="Shortcuts (Ctrl+?)"
          >
            ⌨️ ?
          </button>
        </nav>
      </header>

      <main className="app-main">
        <aside className="app-sidebar" aria-label="Left panel">
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
        
        <section className="app-content" aria-label="Graph workspace">
          <GraphCanvas />
          
          {/* Floating toggle for node preview */}
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
        </section>
        
        <aside className="app-panel" aria-label="Control panel">
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
