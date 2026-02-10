import { useState, useCallback, useEffect, useRef } from 'react'
import { useAppStore } from '../store'
import './NodeSearch.css'

interface SearchResult {
  id: string
  label: string
  score: number
}

// Simple fuzzy matching algorithm
function fuzzyMatch(pattern: string, str: string): number {
  const patternLower = pattern.toLowerCase()
  const strLower = str.toLowerCase()
  
  // Exact match gets highest score
  if (strLower === patternLower) return 1
  
  // Starts with pattern gets high score
  if (strLower.startsWith(patternLower)) return 0.9
  
  // Contains pattern gets medium score
  if (strLower.includes(patternLower)) return 0.7
  
  // Fuzzy match - check if all chars in pattern appear in order
  let patternIdx = 0
  let strIdx = 0
  let matches = 0
  
  while (patternIdx < patternLower.length && strIdx < strLower.length) {
    if (patternLower[patternIdx] === strLower[strIdx]) {
      matches++
      patternIdx++
    }
    strIdx++
  }
  
  if (matches === patternLower.length) {
    // Calculate score based on match quality
    return 0.5 + (matches / strLower.length) * 0.3
  }
  
  return 0
}

interface NodeSearchProps {
  isOpen: boolean
  onClose: () => void
}

export function NodeSearch({ isOpen, onClose }: NodeSearchProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const { nodes, selectNode } = useAppStore()

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus()
      setQuery('')
      setResults([])
      setSelectedIndex(0)
    }
  }, [isOpen])

  // Perform fuzzy search
  const performSearch = useCallback((searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([])
      return
    }

    const scored = nodes
      .map(node => ({
        id: node.id,
        label: node.label,
        score: fuzzyMatch(searchQuery, node.label),
      }))
      .filter(result => result.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 10)

    setResults(scored)
    setSelectedIndex(0)
  }, [nodes])

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newQuery = e.target.value
    setQuery(newQuery)
    performSearch(newQuery)
  }

  // Handle node selection
  const handleSelectNode = useCallback((nodeId: string) => {
    selectNode(nodeId)
    onClose()
  }, [selectNode, onClose])

  // Handle keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex(prev => 
          prev < results.length - 1 ? prev + 1 : prev
        )
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex(prev => prev > 0 ? prev - 1 : 0)
        break
      case 'Enter':
        e.preventDefault()
        if (results[selectedIndex]) {
          handleSelectNode(results[selectedIndex].id)
        }
        break
      case 'Escape':
        e.preventDefault()
        onClose()
        break
    }
  }, [results, selectedIndex, handleSelectNode, onClose])

  if (!isOpen) return null

  return (
    <div className="node-search-overlay" onClick={onClose}>
      <div className="node-search-container" onClick={e => e.stopPropagation()}>
        <div className="node-search-input-wrapper">
          <span className="node-search-icon">🔍</span>
          <input
            ref={inputRef}
            type="text"
            className="node-search-input"
            placeholder="Search nodes..."
            value={query}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            aria-label="Search nodes"
            aria-autocomplete="list"
            aria-controls="node-search-results"
            aria-activedescendant={results[selectedIndex] ? `node-result-${results[selectedIndex].id}` : undefined}
          />
          {query && (
            <button 
              className="node-search-clear"
              onClick={() => {
                setQuery('')
                setResults([])
                inputRef.current?.focus()
              }}
              aria-label="Clear search"
            >
              ×
            </button>
          )}
        </div>

        {results.length > 0 && (
          <ul 
            id="node-search-results" 
            className="node-search-results"
            role="listbox"
          >
            {results.map((result, index) => (
              <li
                key={result.id}
                id={`node-result-${result.id}`}
                className={`node-search-result ${index === selectedIndex ? 'selected' : ''}`}
                onClick={() => handleSelectNode(result.id)}
                onMouseEnter={() => setSelectedIndex(index)}
                role="option"
                aria-selected={index === selectedIndex}
              >
                <span className="node-search-result-label">{result.label}</span>
                <span className="node-search-result-score">
                  {Math.round(result.score * 100)}% match
                </span>
              </li>
            ))}
          </ul>
        )}

        {query && results.length === 0 && (
          <div className="node-search-no-results">
            No nodes found matching "{query}"
          </div>
        )}

        <div className="node-search-hints">
          <span>↑↓ to navigate</span>
          <span>↵ to select</span>
          <span>Esc to close</span>
        </div>
      </div>
    </div>
  )
}
