import { useState, useEffect } from 'react'
import { useAppStore } from '../store'
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

export function SceneMetadata({ nodeId }: SceneMetadataProps) {
  const { nodes, updateNodeMetadata, characters, toggleCharacterInNode } = useAppStore()
  const node = nodes.find(n => n.id === nodeId)
  
  const [title, setTitle] = useState('')
  const [location, setLocation] = useState('')
  const [timeOfDay, setTimeOfDay] = useState('')
  const [moodTags, setMoodTags] = useState<string[]>([])
  const [customMood, setCustomMood] = useState('')
  const [isDirty, setIsDirty] = useState(false)
  
  useEffect(() => {
    if (node) {
      setTitle(node.metadata.title)
      setLocation(node.metadata.location)
      setTimeOfDay(node.metadata.timeOfDay)
      setMoodTags(node.metadata.moodTags)
      setIsDirty(false)
    }
  }, [nodeId, node?.metadata])
  
  if (!node) return null
  
  const handleSave = () => {
    updateNodeMetadata(nodeId, {
      title,
      location,
      timeOfDay,
      moodTags,
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
  
  const estimatedReadingTime = Math.ceil(node.content.wordCount / 200) // ~200 WPM
  
  return (
    <div className="scene-metadata" role="form" aria-label="Scene metadata">
      <div className="metadata-header">
        <h3 className="metadata-title">Scene Details</h3>
        {isDirty && <span className="dirty-badge">Unsaved</span>}
      </div>
      
      <div className="metadata-section">
        <label htmlFor="scene-title" className="metadata-label">
          Scene Title
        </label>
        <input
          id="scene-title"
          type="text"
          value={title}
          onChange={(e) => { setTitle(e.target.value); setIsDirty(true) }}
          placeholder="Enter scene title..."
          className="metadata-input"
        />
      </div>
      
      <div className="metadata-row">
        <div className="metadata-section">
          <label htmlFor="scene-location" className="metadata-label">
            Location
          </label>
          <input
            id="scene-location"
            type="text"
            value={location}
            onChange={(e) => { setLocation(e.target.value); setIsDirty(true) }}
            placeholder="Where does this take place?"
            className="metadata-input"
          />
        </div>
        
        <div className="metadata-section">
          <label htmlFor="scene-time" className="metadata-label">
            Time of Day
          </label>
          <select
            id="scene-time"
            value={timeOfDay}
            onChange={(e) => { setTimeOfDay(e.target.value); setIsDirty(true) }}
            className="metadata-select"
          >
            <option value="">Select time...</option>
            {TIME_PRESETS.map(time => (
              <option key={time} value={time}>{time}</option>
            ))}
          </select>
        </div>
      </div>
      
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
      
      {isDirty && (
        <div className="metadata-actions">
          <button onClick={handleSave} className="button-primary">
            Save Changes
          </button>
        </div>
      )}
    </div>
  )
}
