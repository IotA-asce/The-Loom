import { useState } from 'react'
import { useMaturityStore, type RatingLevel, type ContentCategory, MATURITY_RATINGS } from '../stores/maturityStore'
import './MaturityRating.css'

interface MaturityRatingProps {
  isOpen: boolean
  onClose: () => void
}

export function MaturityRating({ isOpen, onClose }: MaturityRatingProps) {
  const {
    currentRating,
    contentScores,
    targetAudience,
    contentWarnings,
    justification,
    setTargetAudience,
    toggleWarning,
  } = useMaturityStore()
  
  const [activeTab, setActiveTab] = useState<'overview' | 'categories' | 'warnings'>('overview')
  
  if (!isOpen) return null
  
  const rating = MATURITY_RATINGS[currentRating]
  
  const categories: { key: ContentCategory; label: string; icon: string }[] = [
    { key: 'violence', label: 'Violence', icon: '⚔️' },
    { key: 'language', label: 'Language', icon: '💬' },
    { key: 'sexualContent', label: 'Sexual Content', icon: '🔞' },
    { key: 'matureThemes', label: 'Mature Themes', icon: '🎭' },
  ]
  
  const audiences = [
    { value: 'children', label: 'Children (0-12)', icon: '🧒' },
    { value: 'teen', label: 'Teens (13-17)', icon: '👦' },
    { value: 'young-adult', label: 'Young Adult (18-25)', icon: '🧑' },
    { value: 'adult', label: 'Adult (26+)', icon: '👨' },
    { value: 'all-ages', label: 'All Ages', icon: '👨‍👩‍👧‍👦' },
  ]
  
  const getScoreColor = (score: number) => {
    if (score <= 2) return '#4caf50'
    if (score <= 4) return '#8bc34a'
    if (score <= 6) return '#ff9800'
    if (score <= 8) return '#ff5722'
    return '#f44336'
  }
  
  const getScoreLabel = (score: number) => {
    if (score <= 2) return 'Minimal'
    if (score <= 4) return 'Mild'
    if (score <= 6) return 'Moderate'
    if (score <= 8) return 'Intense'
    return 'Extreme'
  }
  
  return (
    <div className="maturity-overlay" onClick={onClose}>
      <div className="maturity-panel" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="maturity-header">
          <h2>🎬 Content Rating</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        {/* Main Rating Badge */}
        <div className="maturity-hero">
          <div
            className="rating-badge-large"
            style={{ backgroundColor: rating.color }}
          >
            <span className="badge-label">{rating.code}</span>
            <span className="badge-name">{rating.name}</span>
          </div>
          
          <div className="rating-summary">
            <p className="rating-description">{rating.description}</p>
            <div className="age-guidance">
              <span className="age-icon">👥</span>
              <span>Recommended for {rating.minAge}+</span>
            </div>
          </div>
        </div>
        
        {/* Tabs */}
        <div className="maturity-tabs">
          <button
            className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            📊 Overview
          </button>
          <button
            className={`tab-btn ${activeTab === 'categories' ? 'active' : ''}`}
            onClick={() => setActiveTab('categories')}
          >
            📈 Categories
          </button>
          <button
            className={`tab-btn ${activeTab === 'warnings' ? 'active' : ''}`}
            onClick={() => setActiveTab('warnings')}
          >
            ⚠️ Warnings
          </button>
        </div>
        
        {/* Content */}
        <div className="maturity-content">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="overview-tab">
              {/* Justification */}
              <div className="overview-section">
                <h3>📝 Rating Justification</h3>
                <p className="justification-text">{justification}</p>
              </div>
              
              {/* Target Audience */}
              <div className="overview-section">
                <h3>🎯 Target Audience</h3>
                <div className="audience-selector">
                  {audiences.map(audience => (
                    <button
                      key={audience.value}
                      className={`audience-btn ${targetAudience === audience.value ? 'active' : ''}`}
                      onClick={() => setTargetAudience(audience.value as any)}
                    >
                      <span className="audience-icon">{audience.icon}</span>
                      <span className="audience-label">{audience.label}</span>
                    </button>
                  ))}
                </div>
                
                {targetAudience && (
                  <div className="suitability-indicator">
                    {(() => {
                      const audienceMinAge: Record<string, number> = {
                        'children': 0,
                        'teen': 13,
                        'young-adult': 18,
                        'adult': 26,
                        'all-ages': 0,
                      }
                      const isSuitable = audienceMinAge[targetAudience] >= rating.minAge ||
                                        (targetAudience === 'all-ages' && rating.minAge === 0)
                      
                      return (
                        <>
                          <span className={`suitability-badge ${isSuitable ? 'suitable' : 'unsuitable'}`}>
                            {isSuitable ? '✅ Suitable' : '❌ Not Suitable'}
                          </span>
                          {!isSuitable && (
                            <p className="suitability-note">
                              This content may not be appropriate for your selected audience.
                            </p>
                          )}
                        </>
                      )
                    })()}
                  </div>
                )}
              </div>
              
              {/* Quick Scores */}
              <div className="overview-section">
                <h3>📊 Content Breakdown</h3>
                <div className="quick-scores">
                  {categories.map(cat => (
                    <div key={cat.key} className="quick-score">
                      <span className="quick-icon">{cat.icon}</span>
                      <div className="quick-bar">
                        <div
                          className="quick-fill"
                          style={{
                            width: `${contentScores[cat.key] * 10}%`,
                            backgroundColor: getScoreColor(contentScores[cat.key]),
                          }}
                        />
                      </div>
                      <span className="quick-value">{contentScores[cat.key]}/10</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
          
          {/* Categories Tab */}
          {activeTab === 'categories' && (
            <div className="categories-tab">
              {categories.map(cat => {
                const score = contentScores[cat.key]
                return (
                  <div key={cat.key} className="category-card">
                    <div className="category-header">
                      <span className="category-icon">{cat.icon}</span>
                      <div className="category-info">
                        <h4>{cat.label}</h4>
                        <span
                          className="category-level"
                          style={{ color: getScoreColor(score) }}
                        >
                          {getScoreLabel(score)}
                        </span>
                      </div>
                      <span className="category-score">{score}/10</span>
                    </div>
                    
                    <div className="category-bar">
                      <div
                        className="category-fill"
                        style={{
                          width: `${score * 10}%`,
                          backgroundColor: getScoreColor(score),
                        }}
                      />
                    </div>
                    
                    <div className="category-markers">
                      {[0, 2, 4, 6, 8, 10].map(marker => (
                        <span
                          key={marker}
                          className={`marker ${score >= marker ? 'active' : ''}`}
                        >
                          {marker}
                        </span>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
          
          {/* Warnings Tab */}
          {activeTab === 'warnings' && (
            <div className="warnings-tab">
              <div className="warnings-section">
                <h3>⚠️ Content Warnings</h3>
                <p className="warnings-description">
                  Select warnings to display to readers:
                </p>
                
                <div className="warnings-list">
                  {contentWarnings.map(warning => (
                    <label
                      key={warning.id}
                      className={`warning-item ${warning.selected ? 'selected' : ''}`}
                    >
                      <input
                        type="checkbox"
                        checked={warning.selected}
                        onChange={() => toggleWarning(warning.id)}
                      />
                      <span className="warning-checkbox" />
                      <div className="warning-info">
                        <span className="warning-icon">{warning.icon}</span>
                        <span className="warning-label">{warning.label}</span>
                      </div>
                      <span
                        className="warning-severity"
                        style={{
                          backgroundColor: warning.severity === 'high' ? '#ef4444' :
                                         warning.severity === 'medium' ? '#ff9800' : '#4caf50',
                        }}
                      >
                        {warning.severity}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
              
              {/* Active Warnings Summary */}
              <div className="warnings-section">
                <h3>🚨 Active Warnings</h3>
                {contentWarnings.some(w => w.selected) ? (
                  <div className="active-warnings">
                    {contentWarnings
                      .filter(w => w.selected)
                      .map(warning => (
                        <div
                          key={warning.id}
                          className="active-warning"
                          style={{
                            borderColor: warning.severity === 'high' ? '#ef4444' :
                                        warning.severity === 'medium' ? '#ff9800' : '#4caf50',
                          }}
                        >
                          <span className="active-icon">{warning.icon}</span>
                          <span className="active-label">{warning.label}</span>
                        </div>
                      ))}
                  </div>
                ) : (
                  <p className="no-warnings">No warnings selected</p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Compact rating badge for display elsewhere
export function RatingBadge({ rating, showLabel = true, size = 'medium' }: {
  rating: RatingLevel
  showLabel?: boolean
  size?: 'small' | 'medium' | 'large'
}) {
  const ratingInfo = MATURITY_RATINGS[rating]
  
  return (
    <div
      className={`rating-badge ${size}`}
      style={{ backgroundColor: ratingInfo.color }}
      title={`${ratingInfo.name}: ${ratingInfo.description}`}
    >
      <span className="badge-code">{ratingInfo.code}</span>
      {showLabel && <span className="badge-text">{ratingInfo.name}</span>}
    </div>
  )
}
