import { useState, useEffect, useRef } from 'react'
import { useAppStore } from '../store'
import './SearchPanel.css'

interface SearchResult {
  id: string
  text: string
  source: string
  branchId: string
  relevanceScore: number
  entityType?: 'character' | 'location' | 'event'
  entityName?: string
  timestamp?: string
}

export function SearchPanel() {
  const {
    searchPanelOpen,
    toggleSearchPanel,
    branches,
    addToContext,
  } = useAppStore()

  const [query, setQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [results, setResults] = useState<SearchResult[]>([])
  const [selectedResult, setSelectedResult] = useState<string | null>(null)
  const [expandedResults, setExpandedResults] = useState<string[]>([])
  
  // Search history
  const [searchHistory, setSearchHistory] = useState<string[]>(() => {
    const saved = localStorage.getItem('loom_search_history')
    return saved ? JSON.parse(saved) : []
  })
  const [showHistory, setShowHistory] = useState(false)
  
  // Filters
  const [filters, setFilters] = useState({
    branch: 'all',
    entityType: 'all',
    contentType: 'all',
    dateRange: 'all',
  })
  
  const searchInputRef = useRef<HTMLInputElement>(null)

  // Save history when it changes
  useEffect(() => {
    localStorage.setItem('loom_search_history', JSON.stringify(searchHistory))
  }, [searchHistory])

  // Focus input when panel opens
  useEffect(() => {
    if (searchPanelOpen) {
      setTimeout(() => searchInputRef.current?.focus(), 100)
    }
  }, [searchPanelOpen])

  if (!searchPanelOpen) return null

  const handleSearch = async () => {
    if (!query.trim()) return
    
    setIsSearching(true)
    setShowHistory(false)
    
    // Add to history
    setSearchHistory(prev => {
      const filtered = prev.filter(h => h !== query)
      return [query, ...filtered].slice(0, 20)
    })
    
    // Mock search results
    const mockResults: SearchResult[] = [
      {
        id: 'result-1',
        text: 'The protagonist stood at the edge of the cliff, looking out over the vast expanse below. The wind whipped through their hair as they contemplated the journey ahead.',
        source: 'Chapter 3 - The Journey Begins',
        branchId: 'main',
        relevanceScore: 0.95,
        entityType: 'character',
        entityName: 'Protagonist',
        timestamp: '2024-01-15T10:30:00Z',
      },
      {
        id: 'result-2',
        text: 'Mountains stretched endlessly into the horizon, their peaks dusted with snow that gleamed in the afternoon sun.',
        source: 'Chapter 2 - The Wilderness',
        branchId: 'main',
        relevanceScore: 0.87,
        entityType: 'location',
        entityName: 'Northern Mountains',
        timestamp: '2024-01-14T16:45:00Z',
      },
      {
        id: 'result-3',
        text: '"I cannot go back," she said, her voice steady despite the trembling in her hands. "Not after what I\'ve seen."',
        source: 'Chapter 4 - The Decision',
        branchId: 'main',
        relevanceScore: 0.82,
        entityType: 'character',
        entityName: 'Protagonist',
        timestamp: '2024-01-16T09:15:00Z',
      },
    ]
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500))
    
    setResults(mockResults)
    setIsSearching(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    } else if (e.key === 'Escape') {
      setShowHistory(false)
    }
  }

  const toggleResultExpansion = (id: string) => {
    setExpandedResults(prev =>
      prev.includes(id) ? prev.filter(r => r !== id) : [...prev, id]
    )
  }

  const highlightQuery = (text: string, query: string) => {
    if (!query.trim()) return text
    const parts = text.split(new RegExp(`(${query})`, 'gi'))
    return parts.map((part, i) =>
      part.toLowerCase() === query.toLowerCase() ?
        <mark key={i} className="search-highlight">{part}</mark> : part
    )
  }

  return (
    <div className="search-panel" role="region" aria-labelledby="search-title">
      <div className="panel-header">
        <h2 id="search-title" className="panel-title">🔎 Search</h2>
        <button
          onClick={toggleSearchPanel}
          className="close-button"
          aria-label="Close search panel"
        >
          ×
        </button>
      </div>

      <div className="search-content">
        {/* Search Input */}
        <div className="search-input-wrapper">
          <input
            ref={searchInputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setShowHistory(true)}
            placeholder="Search your story..."
            className="search-input"
          />
          <button
            onClick={handleSearch}
            disabled={!query.trim() || isSearching}
            className="search-button"
          >
            {isSearching ? <span className="spinner" /> : '🔎'}
          </button>
        </div>

        {/* Search History */}
        {showHistory && searchHistory.length > 0 && (
          <div className="search-history">
            <div className="history-header">
              <span>Recent Searches</span>
              <button
                onClick={() => setSearchHistory([])}
                className="clear-history"
              >
                Clear
              </button>
            </div>
            {searchHistory.map((item, index) => (
              <button
                key={index}
                onClick={() => {
                  setQuery(item)
                  setShowHistory(false)
                }}
                className="history-item"
              >
                <span>🕐</span>
                {item}
              </button>
            ))}
          </div>
        )}

        {/* Filters */}
        <div className="search-filters">
          <div className="filter-row">
            <label>Branch</label>
            <select
              value={filters.branch}
              onChange={(e) => setFilters(prev => ({ ...prev, branch: e.target.value }))}
            >
              <option value="all">All Branches</option>
              {branches.map(b => (
                <option key={b.branchId} value={b.branchId}>{b.label}</option>
              ))}
            </select>
          </div>
          
          <div className="filter-row">
            <label>Entity</label>
            <select
              value={filters.entityType}
              onChange={(e) => setFilters(prev => ({ ...prev, entityType: e.target.value }))}
            >
              <option value="all">All Types</option>
              <option value="character">Characters</option>
              <option value="location">Locations</option>
              <option value="event">Events</option>
            </select>
          </div>
          
          <div className="filter-row">
            <label>Content</label>
            <select
              value={filters.contentType}
              onChange={(e) => setFilters(prev => ({ ...prev, contentType: e.target.value }))}
            >
              <option value="all">All Content</option>
              <option value="dialogue">Dialogue</option>
              <option value="description">Description</option>
              <option value="action">Action</option>
            </select>
          </div>
          
          <div className="filter-row">
            <label>Time</label>
            <select
              value={filters.dateRange}
              onChange={(e) => setFilters(prev => ({ ...prev, dateRange: e.target.value }))}
            >
              <option value="all">Any Time</option>
              <option value="today">Today</option>
              <option value="week">This Week</option>
              <option value="month">This Month</option>
            </select>
          </div>
        </div>

        {/* Results */}
        <div className="search-results">
          {isSearching ? (
            <div className="searching-state">
              <span className="spinner" />
              <p>Searching...</p>
            </div>
          ) : results.length > 0 ? (
            <>
              <div className="results-header">
                <span>{results.length} results found</span>
                <button
                  onClick={() => {
                    results.forEach(r => addToContext(r.id))
                  }}
                  className="add-all-btn"
                >
                  + Add All to Context
                </button>
              </div>
              
              {results.map(result => (
                <div
                  key={result.id}
                  className={`search-result ${selectedResult === result.id ? 'selected' : ''}`}
                  onClick={() => setSelectedResult(result.id)}
                >
                  <div className="result-header">
                    <span className="result-source">{result.source}</span>
                    <span className="result-score">
                      {(result.relevanceScore * 100).toFixed(0)}%
                    </span>
                  </div>
                  
                  <div className="result-entities">
                    {result.entityType && (
                      <span className={`entity-badge ${result.entityType}`}>
                        {result.entityType === 'character' && '👤'}
                        {result.entityType === 'location' && '📍'}
                        {result.entityType === 'event' && '⚡'}
                        {result.entityName}
                      </span>
                    )}
                    <span className="branch-badge">{result.branchId}</span>
                  </div>
                  
                  <p className="result-text">
                    {expandedResults.includes(result.id)
                      ? highlightQuery(result.text, query)
                      : highlightQuery(result.text.slice(0, 150) + (result.text.length > 150 ? '...' : ''), query)
                    }
                  </p>
                  
                  {result.text.length > 150 && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        toggleResultExpansion(result.id)
                      }}
                      className="expand-btn"
                    >
                      {expandedResults.includes(result.id) ? '▼ Show Less' : '▶ Show More'}
                    </button>
                  )}
                  
                  <div className="result-actions">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        addToContext(result.id)
                      }}
                      className="add-context-btn"
                    >
                      + Add to Context
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        // Navigate to source
                      }}
                      className="navigate-btn"
                    >
                      → Go to Source
                    </button>
                  </div>
                </div>
              ))}
            </>
          ) : query && !isSearching ? (
            <div className="no-results">
              <p>No results found for "{query}"</p>
              <p className="hint">Try adjusting your filters or search terms</p>
            </div>
          ) : (
            <div className="search-placeholder">
              <p>🔎 Enter a search query to find content</p>
              <p className="hint">Search for characters, locations, events, or specific text</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
