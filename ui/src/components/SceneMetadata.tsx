import { useState, useEffect } from 'react'
import { useAppStore, type NodeType } from '../store'
import './SceneMetadata.css'

interface SceneMetadataProps {
  nodeId: string
}

const MOOD_PRESETS = [
  { value: 'tense', label: 'Tense', color: '#ff5722' },
  { value: 'peaceful', label: 'Peaceful', color: '#4caf50' },
  { value: 'mysterious', label: 'Mysterious', color: '#9c27b0' },
  { value: 'joyful', label: 'Joyful', color: '#ffeb3b' },
  { value: 'sad', label: 'Sad', color: '#2196f3' },
  { value: 'angry', label: 'Angry', color: '#f44336' },
  { value: 'romantic', label: 'Romantic', color: '#e91e63' },
  { value: 'fearful', label: 'Fearful', color: '#795548' },
]

const TIME_PRESETS = [
  'Dawn', 'Morning', 'Noon', 'Afternoon', 'Evening', 'Dusk', 'Night', 'Midnight'
]

// Type-specific field definitions
const TYPE_SPECIFIC_FIELDS: Record<NodeType, {
  label: string
  fields: Array<{
    key: string
    label: string
    type: 'text' | 'select' | 'number' | 'textarea'
    options?: string[]
    placeholder?: string
    required?: boolean
  }>
}> = {
  chapter: {
    label: '📚 Chapter Details',
    fields: [
      { key: 'chapterNumber', label: 'Chapter Number', type: 'number', placeholder: 'e.g., 1', required: true },
      { key: 'arcName', label: 'Story Arc', type: 'text', placeholder: 'e.g., The Beginning' },
      { key: 'summary', label: 'Chapter Summary', type: 'textarea', placeholder: 'Brief summary of this chapter...' },
    ]
  },
  scene: {
    label: '🎬 Scene Details',
    fields: [
      { key: 'location', label: 'Location', type: 'text', placeholder: 'Where does this take place?', required: true },
      { key: 'timeOfDay', label: 'Time of Day', type: 'select', options: TIME_PRESETS },
      { key: 'weather', label: 'Weather', type: 'text', placeholder: 'e.g., Rainy, Sunny, Foggy' },
      { key: 'povCharacter', label: 'POV Character', type: 'text', placeholder: 'Whose perspective is this?' },
    ]
  },
  beat: {
    label: '🎵 Beat Details',
    fields: [
      { key: 'beatType', label: 'Beat Type', type: 'select', options: ['Action', 'Reaction', 'Decision', 'Revelation', 'Emotional', 'Transition'], required: true },
      { key: 'goal', label: 'Character Goal', type: 'text', placeholder: 'What does the character want?' },
      { key: 'outcome', label: 'Outcome', type: 'select', options: ['Success', 'Partial Success', 'Failure', 'Complication', 'Twist'] },
      { key: 'stakes', label: 'Stakes Level', type: 'select', options: ['Low', 'Medium', 'High', 'Life-changing'] },
    ]
  },
  dialogue: {
    label: '💬 Dialogue Details',
    fields: [
      { key: 'speaker', label: 'Speaker', type: 'text', placeholder: 'Who is speaking?', required: true },
      { key: 'emotion', label: 'Emotion', type: 'select', options: ['Neutral', 'Happy', 'Sad', 'Angry', 'Fearful', 'Excited', 'Confused', 'Sarcastic'] },
      { key: 'action', label: 'Speaking Action', type: 'text', placeholder: 'e.g., shouted, whispered, muttered' },
      { key: 'listener', label: 'Listening To', type: 'text', placeholder: 'Who are they speaking to?' },
    ]
  },
  manga: {
    label: '📖 Manga Details',
    fields: [
      { key: 'volume_id', label: 'Volume ID', type: 'text', placeholder: 'Internal volume reference', required: true },
      { key: 'page_count', label: 'Total Pages', type: 'number', placeholder: 'e.g., 200', required: true },
      { key: 'chapter_range', label: 'Chapter Range', type: 'text', placeholder: 'e.g., Ch. 1-5' },
      { key: 'notes', label: 'Notes', type: 'textarea', placeholder: 'Additional notes about this volume...' },
    ]
  },
}

// Validation rules per type
const VALIDATION_RULES: Record<NodeType, Array<{ field: string; validate: (value: unknown) => string | null }>> = {
  chapter: [
    { field: 'chapterNumber', validate: (v) => !v || Number(v) < 1 ? 'Chapter number must be at least 1' : null },
    { field: 'title', validate: (v) => !v || String(v).length < 3 ? 'Title should be at least 3 characters' : null },
  ],
  scene: [
    { field: 'location', validate: (v) => !v || String(v).length < 2 ? 'Location should be at least 2 characters' : null },
  ],
  beat: [
    { field: 'beatType', validate: (v) => !v ? 'Beat type is required' : null },
  ],
  dialogue: [
    { field: 'speaker', validate: (v) => !v || String(v).length < 1 ? 'Speaker is required' : null },
  ],
  manga: [
    { field: 'volume_id', validate: (v) => !v || String(v).length < 1 ? 'Volume ID is required' : null },
    { field: 'page_count', validate: (v) => !v || Number(v) < 1 ? 'Page count must be at least 1' : null },
  ],
}

export function SceneMetadata({ nodeId }: SceneMetadataProps) {
  const { nodes, updateNodeMetadata, updateNodeType, characters, toggleCharacterInNode } = useAppStore()
  const node = nodes.find(n => n.id === nodeId)
  
  const [title, setTitle] = useState('')
  const [location, setLocation] = useState('')
  const [timeOfDay, setTimeOfDay] = useState('')
  const [moodTags, setMoodTags] = useState<string[]>([])
  const [customMood, setCustomMood] = useState('')
  const [isDirty, setIsDirty] = useState(false)
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})
  
  // Type-specific state
  const [typeSpecificData, setTypeSpecificData] = useState<Record<string, unknown>>({})
  
  useEffect(() => {
    if (node) {
      setTitle(node.metadata.title)
      setLocation(node.metadata.location)
      setTimeOfDay(node.metadata.timeOfDay)
      setMoodTags(node.metadata.moodTags)
      // Load type-specific data from node metadata
      setTypeSpecificData(node.metadata.typeSpecific || {})
      setIsDirty(false)
      setValidationErrors({})
    }
  }, [nodeId, node?.metadata])
  
  if (!node) return null
  
  const currentTypeConfig = TYPE_SPECIFIC_FIELDS[node.type]
  const currentValidationRules = VALIDATION_RULES[node.type]
  
  // Validate all fields
  const validate = (): boolean => {
    const errors: Record<string, string> = {}
    
    // Check type-specific validations
    for (const rule of currentValidationRules) {
      const value = typeSpecificData[rule.field] || node.metadata[rule.field as keyof typeof node.metadata]
      const error = rule.validate(value)
      if (error) {
        errors[rule.field] = error
      }
    }
    
    // Check required fields
    for (const field of currentTypeConfig.fields) {
      if (field.required) {
        const value = typeSpecificData[field.key]
        if (!value || (typeof value === 'string' && value.trim() === '')) {
          errors[field.key] = `${field.label} is required`
        }
      }
    }
    
    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }
  
  const handleSave = () => {
    if (!validate()) {
      return
    }
    
    updateNodeMetadata(nodeId, {
      title,
      location,
      timeOfDay,
      moodTags,
      typeSpecific: typeSpecificData,
    })
    setIsDirty(false)
  }
  
  const handleMoodToggle = (mood: string) => {
    setMoodTags(prev =>
      prev.includes(mood)
        ? prev.filter(m => m !== mood)
        : [...prev, mood]
    )
    setIsDirty(true)
  }
  
  const handleAddCustomMood = () => {
    if (customMood && !moodTags.includes(customMood)) {
      setMoodTags([...moodTags, customMood])
      setCustomMood('')
      setIsDirty(true)
    }
  }
  
  const handleTypeChange = (newType: NodeType) => {
    updateNodeType(nodeId, newType)
    // Reset type-specific data when changing types
    setTypeSpecificData({})
    setIsDirty(true)
  }
  
  const handleTypeSpecificChange = (key: string, value: unknown) => {
    setTypeSpecificData(prev => ({ ...prev, [key]: value }))
    setIsDirty(true)
    // Clear validation error for this field
    if (validationErrors[key]) {
      setValidationErrors(prev => {
        const next = { ...prev }
        delete next[key]
        return next
      })
    }
  }
  
  const renderTypeSpecificField = (field: typeof currentTypeConfig.fields[0]) => {
    const value = typeSpecificData[field.key] as string || ''
    const error = validationErrors[field.key]
    
    const fieldWrapperClass = `type-field ${error ? 'has-error' : ''}`
    
    switch (field.type) {
      case 'select':
        return (
          <div key={field.key} className={fieldWrapperClass}>
            <label className="metadata-label">
              {field.label}
              {field.required && <span className="required">*</span>}
            </label>
            <select
              value={value}
              onChange={(e) => handleTypeSpecificChange(field.key, e.target.value)}
              className="metadata-select"
            >
              <option value="">Select {field.label.toLowerCase()}...</option>
              {field.options?.map(opt => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
            {error && <span className="field-error">{error}</span>}
          </div>
        )
      case 'textarea':
        return (
          <div key={field.key} className={fieldWrapperClass}>
            <label className="metadata-label">
              {field.label}
              {field.required && <span className="required">*</span>}
            </label>
            <textarea
              value={value}
              onChange={(e) => handleTypeSpecificChange(field.key, e.target.value)}
              placeholder={field.placeholder}
              className="metadata-textarea"
              rows={3}
            />
            {error && <span className="field-error">{error}</span>}
          </div>
        )
      case 'number':
        return (
          <div key={field.key} className={fieldWrapperClass}>
            <label className="metadata-label">
              {field.label}
              {field.required && <span className="required">*</span>}
            </label>
            <input
              type="number"
              value={value}
              onChange={(e) => handleTypeSpecificChange(field.key, e.target.value ? Number(e.target.value) : '')}
              placeholder={field.placeholder}
              className="metadata-input"
              min={1}
            />
            {error && <span className="field-error">{error}</span>}
          </div>
        )
      default:
        return (
          <div key={field.key} className={fieldWrapperClass}>
            <label className="metadata-label">
              {field.label}
              {field.required && <span className="required">*</span>}
            </label>
            <input
              type="text"
              value={value}
              onChange={(e) => handleTypeSpecificChange(field.key, e.target.value)}
              placeholder={field.placeholder}
              className="metadata-input"
            />
            {error && <span className="field-error">{error}</span>}
          </div>
        )
    }
  }
  
  const estimatedReadingTime = Math.ceil(node.content.wordCount / 200) // ~200 WPM
  
  // Type badge color
  const typeColors: Record<NodeType, string> = {
    chapter: '#4a9eff',
    scene: '#4caf50',
    beat: '#ff9800',
    dialogue: '#9c27b0',
    manga: '#e91e63',
  }
  
  return (
    <div className="scene-metadata" role="form" aria-label="Scene metadata">
      <div className="metadata-header">
        <h3 className="metadata-title">Scene Details</h3>
        {isDirty && <span className="dirty-badge">Unsaved</span>}
      </div>
      
      {/* Node Type Selector */}
      <div className="metadata-section">
        <label className="metadata-label">Node Type</label>
        <div className="type-selector" role="group" aria-label="Node type selection">
          {(Object.keys(TYPE_SPECIFIC_FIELDS) as NodeType[]).map(type => (
            <button
              key={type}
              onClick={() => handleTypeChange(type)}
              className={`type-button ${node.type === type ? 'active' : ''}`}
              style={{
                '--type-color': typeColors[type],
              } as React.CSSProperties}
              aria-pressed={node.type === type}
            >
              {TYPE_SPECIFIC_FIELDS[type].label.split(' ')[0]}
              <span className="type-name">{type}</span>
            </button>
          ))}
        </div>
      </div>
      
      {/* Common Fields */}
      <div className="metadata-section">
        <label htmlFor="scene-title" className="metadata-label">
          Title
          {node.type === 'chapter' && <span className="required">*</span>}
        </label>
        <input
          id="scene-title"
          type="text"
          value={title}
          onChange={(e) => { setTitle(e.target.value); setIsDirty(true) }}
          placeholder={`Enter ${node.type} title...`}
          className={`metadata-input ${validationErrors.title ? 'input-error' : ''}`}
        />
        {validationErrors.title && <span className="field-error">{validationErrors.title}</span>}
      </div>
      
      {/* Type-Specific Fields */}
      <div className="metadata-section type-specific-section">
        <h4 className="type-specific-title">{currentTypeConfig.label}</h4>
        <div className="type-specific-fields">
          {currentTypeConfig.fields.map(renderTypeSpecificField)}
        </div>
      </div>
      
      {/* Mood & Tone */}
      <div className="metadata-section">
        <label className="metadata-label">
          Mood & Tone
        </label>
        <div className="mood-presets" role="group" aria-label="Mood presets">
          {MOOD_PRESETS.map(mood => (
            <button
              key={mood.value}
              onClick={() => handleMoodToggle(mood.value)}
              className={`mood-preset ${moodTags.includes(mood.value) ? 'active' : ''}`}
              style={{
                '--mood-color': mood.color,
              } as React.CSSProperties}
              aria-pressed={moodTags.includes(mood.value)}
            >
              {mood.label}
            </button>
          ))}
        </div>
        
        <div className="custom-mood">
          <div className="autocomplete-wrapper">
            <input
              type="text"
              value={customMood}
              onChange={(e) => setCustomMood(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddCustomMood()}
              placeholder="Add custom mood..."
              className="metadata-input small"
              list="mood-suggestions"
            />
            <datalist id="mood-suggestions">
              {MOOD_PRESETS.filter(m => !moodTags.includes(m.value)).map(m => (
                <option key={m.value} value={m.label} />
              ))}
              <option value="Suspenseful" />
              <option value="Melancholic" />
              <option value="Euphoric" />
              <option value="Grim" />
              <option value="Whimsical" />
              <option value="Brooding" />
              <option value="Hopeful" />
              <option value="Despairing" />
              <option value="Vengeful" />
              <option value="Remorseful" />
            </datalist>
          </div>
          <button 
            onClick={handleAddCustomMood}
            className="button-small"
            disabled={!customMood}
          >
            Add
          </button>
        </div>
        
        {moodTags.length > 0 && (
          <div className="mood-tags">
            {moodTags.map(tag => (
              <span key={tag} className="mood-tag">
                {tag}
                <button
                  onClick={() => handleMoodToggle(tag)}
                  aria-label={`Remove ${tag}`}
                  className="tag-remove"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
      </div>
      
      {/* Characters Present */}
      {node.type !== 'chapter' && (
        <div className="metadata-section">
          <label className="metadata-label">
            Characters Present ({node.characters.length})
          </label>
          <div className="character-presence" role="group" aria-label="Character presence">
            {characters.length === 0 ? (
              <p className="empty-text">No characters defined yet</p>
            ) : (
              characters.map(char => {
                const isPresent = node.characters.includes(char.id)
                return (
                  <button
                    key={char.id}
                    onClick={() => toggleCharacterInNode(nodeId, char.id)}
                    className={`character-toggle ${isPresent ? 'present' : ''}`}
                    aria-pressed={isPresent}
                  >
                    <span className="character-indicator">
                      {isPresent ? '●' : '○'}
                    </span>
                    <span className="character-name">{char.name}</span>
                    {isPresent && (
                      <span className="character-status">
                        {node.characters.indexOf(char.id) === 0 ? ' (Entry)' : ''}
                        {node.characters.indexOf(char.id) === node.characters.length - 1 && node.characters.length > 1 ? ' (Exit)' : ''}
                      </span>
                    )}
                  </button>
                )
              })
            )}
          </div>
        </div>
      )}
      
      {/* Stats */}
      <div className="metadata-stats">
        <div className="stat-item">
          <span className="stat-label">Words</span>
          <span className="stat-value">{node.content.wordCount}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Est. Read Time</span>
          <span className="stat-value">{estimatedReadingTime} min</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Version</span>
          <span className="stat-value">v{node.content.version}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Modified</span>
          <span className="stat-value">
            {new Date(node.content.lastModified).toLocaleDateString()}
          </span>
        </div>
      </div>
      
      {/* Actions */}
      {isDirty && (
        <div className="metadata-actions">
          {Object.keys(validationErrors).length > 0 && (
            <span className="validation-summary">
              ⚠️ Please fix {Object.keys(validationErrors).length} error(s)
            </span>
          )}
          <button 
            onClick={handleSave} 
            className="button-primary"
            disabled={Object.keys(validationErrors).length > 0}
          >
            Save Changes
          </button>
        </div>
      )}
    </div>
  )
}
