import { useState, useCallback, useMemo } from 'react'
import { useAppStore } from '../store'
import './CharacterGallery.css'

interface Character {
  id: string
  name: string
  importance: number
  appearanceCount: number
  portrait?: string
  description?: string
  traits?: string[]
}

type SortBy = 'name' | 'importance' | 'appearance'
type FilterBy = 'all' | 'main' | 'supporting' | 'minor'

interface CharacterGalleryProps {
  isOpen: boolean
  onClose: () => void
  onSelectCharacter?: (characterId: string) => void
  selectedCharacterId?: string
}

export function CharacterGallery({ 
  isOpen, 
  onClose, 
  onSelectCharacter,
  selectedCharacterId 
}: CharacterGalleryProps) {
  const { characters } = useAppStore()
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<SortBy>('name')
  const [filterBy, setFilterBy] = useState<FilterBy>('all')
  const [showIdentityBuilder, setShowIdentityBuilder] = useState(false)
  const [selectedChar, setSelectedChar] = useState<Character | null>(null)

  // Convert store characters to gallery format
  const galleryCharacters: Character[] = useMemo(() => {
    return characters.map(c => ({
      id: c.id,
      name: c.name,
      importance: c.importance || 0.5,
      appearanceCount: c.appearanceCount || 0,
      description: c.description,
      traits: c.traits,
    }))
  }, [characters])

  // Filter characters
  const filteredCharacters = useMemo(() => {
    let result = [...galleryCharacters]

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      result = result.filter(c => 
        c.name.toLowerCase().includes(query) ||
        c.description?.toLowerCase().includes(query) ||
        c.traits?.some(t => t.toLowerCase().includes(query))
      )
    }

    // Apply importance filter
    if (filterBy !== 'all') {
      result = result.filter(c => {
        switch (filterBy) {
          case 'main': return c.importance >= 0.7
          case 'supporting': return c.importance >= 0.4 && c.importance < 0.7
          case 'minor': return c.importance < 0.4
          default: return true
        }
      })
    }

    // Apply sort
    result.sort((a, b) => {
      switch (sortBy) {
        case 'name': return a.name.localeCompare(b.name)
        case 'importance': return b.importance - a.importance
        case 'appearance': return b.appearanceCount - a.appearanceCount
        default: return 0
      }
    })

    return result
  }, [galleryCharacters, searchQuery, filterBy, sortBy])

  const handleCharacterClick = useCallback((character: Character) => {
    setSelectedChar(character)
    onSelectCharacter?.(character.id)
  }, [onSelectCharacter])

  const handleTrainLoRA = useCallback((characterId: string) => {
    // Trigger LoRA training
    console.log('Training LoRA for character:', characterId)
    setShowIdentityBuilder(true)
  }, [])

  if (!isOpen) return null

  return (
    <div className="character-gallery-overlay" onClick={onClose}>
      <div className="character-gallery-container" onClick={e => e.stopPropagation()}>
        <header className="character-gallery-header">
          <h2>🎭 Character Gallery</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </header>

        <div className="character-gallery-filters">
          <div className="search-box">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              placeholder="Search characters..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button className="clear-btn" onClick={() => setSearchQuery('')}>
                ×
              </button>
            )}
          </div>

          <div className="filter-controls">
            <select
              value={filterBy}
              onChange={(e) => setFilterBy(e.target.value as FilterBy)}
              aria-label="Filter by importance"
            >
              <option value="all">All Characters</option>
              <option value="main">Main Characters</option>
              <option value="supporting">Supporting</option>
              <option value="minor">Minor</option>
            </select>

            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortBy)}
              aria-label="Sort by"
            >
              <option value="name">Sort by Name</option>
              <option value="importance">Sort by Importance</option>
              <option value="appearance">Sort by Appearances</option>
            </select>
          </div>
        </div>

        <div className="character-gallery-stats">
          Showing {filteredCharacters.length} of {galleryCharacters.length} characters
        </div>

        <div className="character-gallery-grid">
          {filteredCharacters.map(character => (
            <CharacterCard
              key={character.id}
              character={character}
              isSelected={selectedCharacterId === character.id}
              onClick={() => handleCharacterClick(character)}
              onTrain={() => handleTrainLoRA(character.id)}
            />
          ))}
        </div>

        {filteredCharacters.length === 0 && (
          <div className="no-results">
            <p>No characters found matching your criteria</p>
            <button onClick={() => { setSearchQuery(''); setFilterBy('all') }}>
              Clear filters
            </button>
          </div>
        )}

        {showIdentityBuilder && selectedChar && (
          <IdentityPackBuilder
            character={selectedChar}
            onClose={() => setShowIdentityBuilder(false)}
          />
        )}
      </div>
    </div>
  )
}

interface CharacterCardProps {
  character: Character
  isSelected: boolean
  onClick: () => void
  onTrain: () => void
}

function CharacterCard({ character, isSelected, onClick, onTrain }: CharacterCardProps) {
  const importanceLabel = character.importance >= 0.7 ? 'Main' : 
                         character.importance >= 0.4 ? 'Supporting' : 'Minor'
  
  const importanceColor = character.importance >= 0.7 ? '#4caf50' : 
                         character.importance >= 0.4 ? '#ff9800' : '#9e9e9e'

  return (
    <div 
      className={`character-card ${isSelected ? 'selected' : ''}`}
      onClick={onClick}
    >
      <div className="character-portrait">
        {character.portrait ? (
          <img src={character.portrait} alt={character.name} />
        ) : (
          <div className="portrait-placeholder">
            {character.name.charAt(0).toUpperCase()}
          </div>
        )}
      </div>

      <div className="character-info">
        <h3 className="character-name">{character.name}</h3>
        
        <div className="character-meta">
          <span 
            className="importance-badge"
            style={{ backgroundColor: importanceColor }}
          >
            {importanceLabel}
          </span>
          <span className="appearance-count">
            {character.appearanceCount} appearances
          </span>
        </div>

        {character.traits && character.traits.length > 0 && (
          <div className="character-traits">
            {character.traits.slice(0, 3).map((trait, i) => (
              <span key={i} className="trait-tag">{trait}</span>
            ))}
          </div>
        )}

        {character.description && (
          <p className="character-description">
            {character.description.slice(0, 80)}
            {character.description.length > 80 && '...'}
          </p>
        )}
      </div>

      <div className="character-actions">
        <button 
          className="train-btn"
          onClick={(e) => { e.stopPropagation(); onTrain(); }}
          title="Train LoRA model"
        >
          🎯 Train
        </button>
      </div>
    </div>
  )
}

interface IdentityPackBuilderProps {
  character: Character
  onClose: () => void
}

function IdentityPackBuilder({ character, onClose }: IdentityPackBuilderProps) {
  const [faceRef, setFaceRef] = useState<File | null>(null)
  const [, setSilhouetteRef] = useState<File | null>(null)
  const [, setCostumeRef] = useState<File | null>(null)
  const [previewUrls, setPreviewUrls] = useState<{
    face?: string
    silhouette?: string
    costume?: string
  }>({})
  const [isTraining, setIsTraining] = useState(false)
  const [trainingProgress, setTrainingProgress] = useState(0)

  const handleFileSelect = (
    type: 'face' | 'silhouette' | 'costume',
    file: File | null
  ) => {
    if (file) {
      const url = URL.createObjectURL(file)
      setPreviewUrls(prev => ({ ...prev, [type]: url }))
      
      switch (type) {
        case 'face': setFaceRef(file); break
        case 'silhouette': setSilhouetteRef(file); break
        case 'costume': setCostumeRef(file); break
      }
    }
  }

  const handleTrain = async () => {
    setIsTraining(true)
    setTrainingProgress(0)
    
    // Simulate training progress
    const interval = setInterval(() => {
      setTrainingProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval)
          setIsTraining(false)
          return 100
        }
        return prev + 5
      })
    }, 200)
  }

  return (
    <div className="identity-builder-overlay" onClick={onClose}>
      <div className="identity-builder" onClick={e => e.stopPropagation()}>
        <header>
          <h3>🎨 Identity Pack Builder: {character.name}</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </header>

        <div className="reference-uploads">
          <ReferenceUpload
            type="face"
            label="Face Reference"
            description="Front-facing portrait for facial features"
            preview={previewUrls.face}
            onSelect={(file) => handleFileSelect('face', file)}
          />
          <ReferenceUpload
            type="silhouette"
            label="Silhouette Reference"
            description="Profile view for distinctive shapes"
            preview={previewUrls.silhouette}
            onSelect={(file) => handleFileSelect('silhouette', file)}
          />
          <ReferenceUpload
            type="costume"
            label="Costume Reference"
            description="Outfit and styling details"
            preview={previewUrls.costume}
            onSelect={(file) => handleFileSelect('costume', file)}
          />
        </div>

        {isTraining && (
          <div className="training-progress">
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${trainingProgress}%` }}
              />
            </div>
            <span className="progress-text">{trainingProgress}% - Training LoRA...</span>
          </div>
        )}

        <div className="builder-actions">
          <button className="secondary-btn" onClick={onClose}>
            Cancel
          </button>
          <button 
            className="primary-btn"
            onClick={handleTrain}
            disabled={!faceRef || isTraining}
          >
            {isTraining ? 'Training...' : '🚀 Start Training'}
          </button>
        </div>
      </div>
    </div>
  )
}

interface ReferenceUploadProps {
  type: string
  label: string
  description: string
  preview?: string
  onSelect: (file: File | null) => void
}

function ReferenceUpload({ type, label, description, preview, onSelect }: ReferenceUploadProps) {
  const inputId = `ref-upload-${type}`

  return (
    <div className="reference-upload">
      <label className="upload-label">{label}</label>
      <p className="upload-description">{description}</p>
      
      <div className="upload-area">
        {preview ? (
          <div className="preview-container">
            <img src={preview} alt={`${label} preview`} />
            <button 
              className="remove-btn"
              onClick={() => onSelect(null)}
            >
              ×
            </button>
          </div>
        ) : (
          <label htmlFor={inputId} className="upload-placeholder">
            <span className="upload-icon">📷</span>
            <span>Click to upload</span>
          </label>
        )}
        <input
          id={inputId}
          type="file"
          accept="image/*"
          onChange={(e) => onSelect(e.target.files?.[0] || null)}
          hidden
        />
      </div>
    </div>
  )
}
