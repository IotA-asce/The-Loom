import { useState, useMemo, useEffect, useRef } from 'react'
import './TemplateGallery.css'

export type TemplateCategory = 'fiction' | 'manga' | 'script'

export interface Template {
  id: string
  name: string
  description: string
  category: TemplateCategory
  preview: string
  content: object
}

interface TemplateGalleryProps {
  isOpen: boolean
  onClose: () => void
  onImport: (template: Template) => void
}

const CATEGORY_LABELS: Record<TemplateCategory, string> = {
  fiction: '📚 Fiction',
  manga: '🎨 Manga',
  script: '🎬 Script',
}

const CATEGORY_COLORS: Record<TemplateCategory, string> = {
  fiction: '#4a9eff',
  manga: '#ff6b9d',
  script: '#9c27b0',
}

// Sample templates
const SAMPLE_TEMPLATES: Template[] = [
  {
    id: 'hero-journey',
    name: 'The Hero\'s Journey',
    description: 'Classic three-act structure following Campbell\'s monomyth. Perfect for fantasy and adventure novels with clear character arcs and transformative journeys.',
    category: 'fiction',
    preview: 'Act I: Departure — Ordinary World, Call to Adventure, Refusal...',
    content: {
      acts: 3,
      structure: 'hero-journey',
      nodes: [
        { type: 'chapter', label: 'Ordinary World', act: 1 },
        { type: 'chapter', label: 'Call to Adventure', act: 1 },
        { type: 'chapter', label: 'Crossing the Threshold', act: 1 },
        { type: 'chapter', label: 'Tests & Enemies', act: 2 },
        { type: 'chapter', label: 'The Ordeal', act: 2 },
        { type: 'chapter', label: 'The Return', act: 3 },
      ],
    },
  },
  {
    id: 'shonen-manga',
    name: 'Shonen Tournament Arc',
    description: 'High-energy tournament structure with escalating battles, rival introductions, and power progression. Ideal for action-focused manga with competitive elements.',
    category: 'manga',
    preview: 'Prelims → Group Stage → Finals → Championship...',
    content: {
      acts: 4,
      structure: 'tournament-arc',
      nodes: [
        { type: 'chapter', label: 'Registration & Meet Rivals', act: 1 },
        { type: 'chapter', label: 'Preliminary Rounds', act: 1 },
        { type: 'chapter', label: 'Group Battles', act: 2 },
        { type: 'chapter', label: 'Training Montage', act: 2 },
        { type: 'chapter', label: 'Semifinals', act: 3 },
        { type: 'chapter', label: 'Final Showdown', act: 4 },
      ],
    },
  },
  {
    id: 'screenplay-3-act',
    name: 'Feature Film 3-Act',
    description: 'Industry-standard screenplay structure with precise page counts. Includes beat sheet for inciting incident, midpoint twist, and climactic resolution.',
    category: 'script',
    preview: 'Act I (30pp) → Act II (60pp) → Act III (30pp)...',
    content: {
      acts: 3,
      structure: 'three-act-screenplay',
      format: 'screenplay',
      nodes: [
        { type: 'scene', label: 'Opening Image', page: 1 },
        { type: 'scene', label: 'Inciting Incident', page: 10 },
        { type: 'scene', label: 'First Plot Point', page: 25 },
        { type: 'scene', label: 'Midpoint', page: 55 },
        { type: 'scene', label: 'Second Plot Point', page: 85 },
        { type: 'scene', label: 'Climax', page: 110 },
      ],
    },
  },
  {
    id: 'slice-of-life',
    name: 'Slice of Life Anthology',
    description: 'Episodic structure for character-driven stories. Features interconnected short chapters focusing on daily moments, relationships, and emotional beats.',
    category: 'manga',
    preview: 'Ep 1: Cherry Blossoms → Ep 2: Summer Festival...',
    content: {
      acts: 1,
      structure: 'episodic',
      nodes: [
        { type: 'chapter', label: 'Spring: New Beginnings', episode: 1 },
        { type: 'chapter', label: 'Summer: Festival Days', episode: 2 },
        { type: 'chapter', label: 'Autumn: Changing Leaves', episode: 3 },
        { type: 'chapter', label: 'Winter: Warmth Within', episode: 4 },
        { type: 'chapter', label: 'Special: Future Dreams', episode: 5 },
      ],
    },
  },
]

export function TemplateGallery({ isOpen, onClose, onImport }: TemplateGalleryProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<TemplateCategory | 'all'>('all')
  const [importingId, setImportingId] = useState<string | null>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)

  // Focus search input when modal opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => searchInputRef.current?.focus(), 100)
    } else {
      // Reset state when closed
      setSearchQuery('')
      setSelectedCategory('all')
      setImportingId(null)
    }
  }, [isOpen])

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  // Filter templates
  const filteredTemplates = useMemo(() => {
    return SAMPLE_TEMPLATES.filter((template) => {
      const matchesCategory = selectedCategory === 'all' || template.category === selectedCategory
      const matchesSearch = searchQuery.trim() === '' ||
        template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        template.description.toLowerCase().includes(searchQuery.toLowerCase())
      return matchesCategory && matchesSearch
    })
  }, [searchQuery, selectedCategory])

  // Handle import with loading state
  const handleImport = async (template: Template) => {
    setImportingId(template.id)
    // Simulate brief loading for better UX
    await new Promise(resolve => setTimeout(resolve, 300))
    onImport(template)
    setImportingId(null)
  }

  if (!isOpen) return null

  return (
    <div 
      className="template-gallery-overlay"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="template-gallery-title"
    >
      <div className="template-gallery">
        {/* Header */}
        <div className="gallery-header">
          <h2 id="template-gallery-title" className="gallery-title">
            📋 Template Gallery
          </h2>
          <button
            onClick={onClose}
            className="gallery-close-button"
            aria-label="Close template gallery"
          >
            ×
          </button>
        </div>

        {/* Search and Filters */}
        <div className="gallery-controls">
          <div className="search-wrapper">
            <span className="search-icon" aria-hidden="true">🔎</span>
            <input
              ref={searchInputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search templates..."
              className="gallery-search-input"
              aria-label="Search templates"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="clear-search"
                aria-label="Clear search"
              >
                ×
              </button>
            )}
          </div>

          <div className="category-filters" role="group" aria-label="Filter by category">
            <button
              onClick={() => setSelectedCategory('all')}
              className={`category-btn ${selectedCategory === 'all' ? 'active' : ''}`}
              aria-pressed={selectedCategory === 'all'}
            >
              All
            </button>
            {(Object.keys(CATEGORY_LABELS) as TemplateCategory[]).map((category) => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`category-btn ${selectedCategory === category ? 'active' : ''}`}
                aria-pressed={selectedCategory === category}
                style={{
                  '--category-color': CATEGORY_COLORS[category],
                } as React.CSSProperties}
              >
                {CATEGORY_LABELS[category]}
              </button>
            ))}
          </div>
        </div>

        {/* Template Grid */}
        <div className="gallery-content">
          {filteredTemplates.length > 0 ? (
            <div className="template-grid" role="list">
              {filteredTemplates.map((template) => (
                <div
                  key={template.id}
                  className="template-card"
                  role="listitem"
                  style={{
                    '--card-accent': CATEGORY_COLORS[template.category],
                  } as React.CSSProperties}
                >
                  <div className="template-card-header">
                    <span 
                      className="template-category-badge"
                      style={{ backgroundColor: `${CATEGORY_COLORS[template.category]}20`, color: CATEGORY_COLORS[template.category] }}
                    >
                      {CATEGORY_LABELS[template.category]}
                    </span>
                  </div>

                  <h3 className="template-name">{template.name}</h3>
                  
                  <div className="template-preview">
                    <span className="preview-label">Preview:</span>
                    <p className="preview-text">{template.preview}</p>
                  </div>

                  <p className="template-description">{template.description}</p>

                  <div className="template-card-footer">
                    <button
                      onClick={() => handleImport(template)}
                      disabled={importingId === template.id}
                      className={`import-button ${importingId === template.id ? 'loading' : ''}`}
                      aria-label={`Import ${template.name} template`}
                    >
                      {importingId === template.id ? (
                        <>
                          <span className="button-spinner" aria-hidden="true" />
                          <span>Importing...</span>
                        </>
                      ) : (
                        <>
                          <span>📥</span>
                          <span>Import Template</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state" role="status">
              <div className="empty-icon">📭</div>
              <h3>No templates found</h3>
              <p>
                {searchQuery 
                  ? `No results for "${searchQuery}"${selectedCategory !== 'all' ? ` in ${CATEGORY_LABELS[selectedCategory]}` : ''}`
                  : 'No templates match the selected category'}
              </p>
              <button 
                onClick={() => { setSearchQuery(''); setSelectedCategory('all') }}
                className="reset-filters-btn"
              >
                Reset Filters
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="gallery-footer">
          <span className="results-count">
            {filteredTemplates.length} template{filteredTemplates.length !== 1 ? 's' : ''} available
          </span>
        </div>
      </div>
    </div>
  )
}
