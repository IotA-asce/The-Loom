import { useEffect, useState } from 'react'
import { GraphCanvas } from './components/GraphCanvas'
import { TunerPanel } from './components/TunerPanel'
import { DualView } from './components/DualView'
import { BranchPanel } from './components/BranchPanel'
import { ImportPanel } from './components/ImportPanel'
import { StatusBar } from './components/StatusBar'
import { useAppStore } from './store'
import './App.css'

function App() {
  const { initialize, keyboardShortcuts } = useAppStore()
  const [sidebarTab, setSidebarTab] = useState<'branches' | 'import'>('branches')

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
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [keyboardShortcuts])

  return (
    <div className="app" role="application" aria-label="The Loom Story Editor">
      <header className="app-header">
        <h1>🧵 The Loom</h1>
        <nav className="app-nav" aria-label="Main navigation">
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
            {sidebarTab === 'import' && (
              <div id="import-panel" role="tabpanel" aria-labelledby="import-tab">
                <ImportPanel />
              </div>
            )}
          </div>
        </aside>
        
        <section className="app-content" aria-label="Graph workspace">
          <GraphCanvas />
        </section>
        
        <aside className="app-panel" aria-label="Control panel">
          <TunerPanel />
          <DualView />
        </aside>
      </main>

      <StatusBar />
    </div>
  )
}

export default App
