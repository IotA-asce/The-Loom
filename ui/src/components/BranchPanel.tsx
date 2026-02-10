import { useState, useEffect } from 'react'
import { useAppStore } from '../store'
import './BranchPanel.css'

export function BranchPanel() {
  const { 
    branches, 
    selectedNodeId, 
    createBranch, 
    archiveBranch, 
    mergeBranch,
    previewBranchImpact,
  } = useAppStore()
  
  const [newBranchLabel, setNewBranchLabel] = useState('')
  const [impactPreview, setImpactPreview] = useState<{
    descendantCount: number
    divergenceScore: number
    summary: string
  } | null>(null)
  const [isCreating, setIsCreating] = useState(false)

  // Load impact preview when node is selected
  useEffect(() => {
    if (selectedNodeId) {
      previewBranchImpact(selectedNodeId).then(setImpactPreview)
    } else {
      setImpactPreview(null)
    }
  }, [selectedNodeId, previewBranchImpact])

  const handleCreateBranch = async () => {
    if (!selectedNodeId || !newBranchLabel.trim()) return
    
    setIsCreating(true)
    await createBranch(selectedNodeId, newBranchLabel.trim())
    setNewBranchLabel('')
    setIsCreating(false)
  }

  const activeBranches = branches.filter(b => b.status === 'active')
  const archivedBranches = branches.filter(b => b.status === 'archived')
  const mergedBranches = branches.filter(b => b.status === 'merged')

  return (
    <div className="branch-panel">
      <h2 className="panel-title">Branches</h2>
      
      {/* Create branch section */}
      <section className="branch-create" aria-labelledby="create-branch-title">
        <h3 id="create-branch-title" className="section-title">
          Create Branch
        </h3>
        
        {selectedNodeId ? (
          <>
            <p className="selected-node">
              From: <code>{selectedNodeId}</code>
            </p>
            
            {impactPreview && (
              <div className="impact-preview" role="status">
                <p className="impact-summary">{impactPreview.summary}</p>
                <div className="impact-metrics">
                  <span className="impact-metric">
                    ↳ {impactPreview.descendantCount} affected
                  </span>
                  <span className={`impact-score ${impactPreview.divergenceScore > 0.7 ? 'high' : ''}`}>
                    Impact: {(impactPreview.divergenceScore * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            )}
            
            <div className="create-form">
              <input
                type="text"
                value={newBranchLabel}
                onChange={(e) => setNewBranchLabel(e.target.value)}
                placeholder="Branch label..."
                className="branch-input"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleCreateBranch()
                }}
                aria-label="New branch label"
              />
              <button
                onClick={handleCreateBranch}
                disabled={!newBranchLabel.trim() || isCreating}
                className="create-button"
                aria-label="Create new branch"
              >
                {isCreating ? '...' : 'Create'}
              </button>
            </div>
          </>
        ) : (
          <p className="hint">
            Select a node in the graph to create a branch
          </p>
        )}
      </section>
      
      {/* Active branches */}
      <section className="branch-list" aria-labelledby="active-branches-title">
        <h3 id="active-branches-title" className="section-title">
          Active ({activeBranches.length})
        </h3>
        
        {activeBranches.length === 0 ? (
          <p className="empty-state">No active branches</p>
        ) : (
          <ul className="branches" role="list">
            {activeBranches.map(branch => (
              <li key={branch.branchId} className="branch-item">
                <div className="branch-info">
                  <span className="branch-name">{branch.label}</span>
                  <span className="branch-id">{branch.branchId}</span>
                </div>
                <div className="branch-actions">
                  <button
                    onClick={() => {
                      const reason = prompt('Archive reason:')
                      if (reason) archiveBranch(branch.branchId, reason)
                    }}
                    className="action-button archive"
                    title="Archive branch"
                    aria-label={`Archive ${branch.label}`}
                  >
                    🗃️
                  </button>
                  {branch.parentBranchId && (
                    <button
                      onClick={() => mergeBranch(branch.branchId, branch.parentBranchId!)}
                      className="action-button merge"
                      title="Merge into parent"
                      aria-label={`Merge ${branch.label} into parent`}
                    >
                      🔀
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
      
      {/* Archived branches */}
      {archivedBranches.length > 0 && (
        <section className="branch-list archived" aria-labelledby="archived-branches-title">
          <h3 id="archived-branches-title" className="section-title">
            Archived ({archivedBranches.length})
          </h3>
          <ul className="branches" role="list">
            {archivedBranches.map(branch => (
              <li key={branch.branchId} className="branch-item">
                <div className="branch-info">
                  <span className="branch-name">{branch.label}</span>
                  <span className="branch-id">{branch.branchId}</span>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}
      
      {/* Merged branches */}
      {mergedBranches.length > 0 && (
        <section className="branch-list merged" aria-labelledby="merged-branches-title">
          <h3 id="merged-branches-title" className="section-title">
            Merged ({mergedBranches.length})
          </h3>
          <ul className="branches" role="list">
            {mergedBranches.map(branch => (
              <li key={branch.branchId} className="branch-item">
                <div className="branch-info">
                  <span className="branch-name">{branch.label}</span>
                  <span className="branch-id">{branch.branchId}</span>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}
