import { useState, useRef, useEffect } from 'react'
import { useBookmarkStore, BOOKMARK_COLORS } from '../stores/bookmarkStore'
import { useAppStore } from '../store'
import './BookmarkDropdown.css'

export function BookmarkDropdown() {
  const [isOpen, setIsOpen] = useState(false)
  const [showAddForm, setShowAddForm] = useState(false)
  const [newLabel, setNewLabel] = useState('')
  const [selectedColor, setSelectedColor] = useState(BOOKMARK_COLORS[0].value)
  const dropdownRef = useRef<HTMLDivElement>(null)
  
  const { bookmarks, addBookmark, removeBookmark, isNodeBookmarked, getBookmarkForNode } = useBookmarkStore()
  const { selectedNodeId, nodes, selectNode } = useAppStore()
  
  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false)
        setShowAddForm(false)
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])
  
  // Reset add form when selected node changes
  useEffect(() => {
    if (selectedNodeId) {
      const bookmark = getBookmarkForNode(selectedNodeId)
      if (bookmark) {
        setNewLabel(bookmark.label)
        setSelectedColor(bookmark.color)
      } else {
        const node = nodes.find(n => n.id === selectedNodeId)
        setNewLabel(node?.label || 'Bookmark')
        setSelectedColor(BOOKMARK_COLORS[bookmarks.length % BOOKMARK_COLORS.length].value)
      }
    }
  }, [selectedNodeId, bookmarks.length, getBookmarkForNode, nodes])
  
  const handleAddBookmark = () => {
    if (!selectedNodeId || !newLabel.trim()) return
    
    addBookmark(selectedNodeId, newLabel.trim(), selectedColor)
    setShowAddForm(false)
    setNewLabel('')
  }
  
  const handleNavigateToBookmark = (nodeId: string) => {
    selectNode(nodeId)
    setIsOpen(false)
  }
  
  const isCurrentNodeBookmarked = selectedNodeId ? isNodeBookmarked(selectedNodeId) : false
  
  return (
    <div ref={dropdownRef} className="bookmark-dropdown">
      <button
        className={`bookmark-toggle ${isCurrentNodeBookmarked ? 'active' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        title="Bookmarks"
      >
        <span className="bookmark-icon">🔖</span>
        <span className="bookmark-count">{bookmarks.length}</span>
      </button>
      
      {isOpen && (
        <div className="bookmark-menu">
          <div className="bookmark-header">
            <h4>Bookmarks</h4>
            {selectedNodeId && (
              <button
                className="bookmark-add-btn"
                onClick={() => setShowAddForm(!showAddForm)}
              >
                {isCurrentNodeBookmarked ? '✏️ Edit' : '+ Add'}
              </button>
            )}
          </div>
          
          {showAddForm && selectedNodeId && (
            <div className="bookmark-form">
              <input
                type="text"
                value={newLabel}
                onChange={(e) => setNewLabel(e.target.value)}
                placeholder="Bookmark label"
                className="bookmark-input"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleAddBookmark()
                  if (e.key === 'Escape') setShowAddForm(false)
                }}
              />
              <div className="bookmark-colors">
                {BOOKMARK_COLORS.map(({ value }) => (
                  <button
                    key={value}
                    className={`bookmark-color-btn ${selectedColor === value ? 'active' : ''}`}
                    style={{ backgroundColor: value }}
                    onClick={() => setSelectedColor(value)}
                  />
                ))}
              </div>
              <div className="bookmark-form-actions">
                <button
                  className="bookmark-cancel"
                  onClick={() => setShowAddForm(false)}
                >
                  Cancel
                </button>
                <button
                  className="bookmark-save"
                  onClick={handleAddBookmark}
                  disabled={!newLabel.trim()}
                >
                  {isCurrentNodeBookmarked ? 'Update' : 'Add'}
                </button>
              </div>
            </div>
          )}
          
          {bookmarks.length === 0 ? (
            <div className="bookmark-empty">
              <p>No bookmarks yet</p>
              {selectedNodeId ? (
                <p className="bookmark-hint">Add a bookmark for the selected node</p>
              ) : (
                <p className="bookmark-hint">Select a node to add a bookmark</p>
              )}
            </div>
          ) : (
            <ul className="bookmark-list">
              {bookmarks
                .sort((a, b) => a.order - b.order)
                .map(bookmark => {
                  const node = nodes.find(n => n.id === bookmark.nodeId)
                  const isSelected = selectedNodeId === bookmark.nodeId
                  
                  return (
                    <li
                      key={bookmark.id}
                      className={`bookmark-item ${isSelected ? 'selected' : ''}`}
                      onClick={() => handleNavigateToBookmark(bookmark.nodeId)}
                    >
                      <span
                        className="bookmark-indicator"
                        style={{ backgroundColor: bookmark.color }}
                      />
                      <span className="bookmark-label">{bookmark.label}</span>
                      {node && (
                        <span className="bookmark-node-label">{node.label}</span>
                      )}
                      <button
                        className="bookmark-delete"
                        onClick={(e) => {
                          e.stopPropagation()
                          removeBookmark(bookmark.id)
                        }}
                        title="Remove bookmark"
                      >
                        ×
                      </button>
                    </li>
                  )
                })}
            </ul>
          )}
          
          {bookmarks.length > 0 && (
            <button
              className="bookmark-clear-all"
              onClick={() => {
                if (confirm('Remove all bookmarks?')) {
                  useBookmarkStore.getState().clearAllBookmarks()
                }
              }}
            >
              Clear All
            </button>
          )}
        </div>
      )}
    </div>
  )
}
