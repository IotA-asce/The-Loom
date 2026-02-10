import { useState, useMemo } from 'react'
import { useAppStore } from '../store'
import './ToneHeatmap.css'

interface ToneData {
  nodeId: string
  title: string
  position: number
  tones: {
    tense: number
    peaceful: number
    mysterious: number
    joyful: number
    sad: number
    angry: number
    romantic: number
    fearful: number
  }
  intensity: number
  genre: string[]
}

export function ToneHeatmap() {
  const {
    toneHeatmapOpen,
    toggleToneHeatmap,
    nodes,
  } = useAppStore()

  const [selectedTone, setSelectedTone] = useState<string | null>(null)
  const [zoomLevel, setZoomLevel] = useState(1)
  const [showPeaks, setShowPeaks] = useState(true)

  // Mock tone data
  const toneData: ToneData[] = useMemo(() => {
    return nodes.map((node, index) => ({
      nodeId: node.id,
      title: node.label,
      position: index,
      tones: {
        tense: Math.random() * 0.8 + 0.1,
        peaceful: Math.random() * 0.6,
        mysterious: Math.random() * 0.7,
        joyful: Math.random() * 0.5,
        sad: Math.random() * 0.6,
        angry: Math.random() * 0.4,
        romantic: Math.random() * 0.3,
        fearful: Math.random() * 0.5,
      },
      intensity: Math.random(),
      genre: ['Fantasy', Math.random() > 0.5 ? 'Adventure' : 'Drama'].filter(Boolean),
    }))
  }, [nodes])

  // Find intensity peaks
  const peaks = useMemo(() => {
    if (!showPeaks) return []
    return toneData
      .map((d, i) => ({ ...d, index: i }))
      .filter((d, i, arr) => {
        if (i === 0 || i === arr.length - 1) return false
        const prev = arr[i - 1].intensity
        const next = arr[i + 1].intensity
        return d.intensity > prev && d.intensity > next && d.intensity > 0.7
      })
  }, [toneData, showPeaks])

  if (!toneHeatmapOpen) return null

  const toneColors: Record<string, string> = {
    tense: '#ff5722',
    peaceful: '#4caf50',
    mysterious: '#9c27b0',
    joyful: '#ffeb3b',
    sad: '#2196f3',
    angry: '#f44336',
    romantic: '#e91e63',
    fearful: '#795548',
  }

  const maxIntensity = Math.max(...toneData.map(d => d.intensity))

  return (
    <div className="tone-heatmap" role="region" aria-labelledby="heatmap-title">
      <div className="panel-header">
        <h2 id="heatmap-title" className="panel-title">🎭 Tone Analysis</h2>
        <button
          onClick={toggleToneHeatmap}
          className="close-button"
          aria-label="Close tone heatmap"
        >
          ×
        </button>
      </div>

      <div className="heatmap-content">
        {/* Controls */}
        <div className="heatmap-controls">
          <div className="control-group">
            <label>Filter by Tone:</label>
            <select
              value={selectedTone || ''}
              onChange={(e) => setSelectedTone(e.target.value || null)}
            >
              <option value="">All Tones</option>
              {Object.keys(toneColors).map(tone => (
                <option key={tone} value={tone}>
                  {tone.charAt(0).toUpperCase() + tone.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <label>
              <input
                type="checkbox"
                checked={showPeaks}
                onChange={(e) => setShowPeaks(e.target.checked)}
              />
              Show Peaks
            </label>
          </div>

          <div className="zoom-controls">
            <button onClick={() => setZoomLevel(z => Math.max(0.5, z - 0.25))}>-</button>
            <span>{Math.round(zoomLevel * 100)}%</span>
            <button onClick={() => setZoomLevel(z => Math.min(2, z + 0.25))}>+</button>
          </div>
        </div>

        {/* Legend */}
        <div className="heatmap-legend">
          <span>Low</span>
          <div className="gradient-bar" />
          <span>High</span>
        </div>

        {/* Heatmap */}
        <div 
          className="heatmap-visualization"
          style={{ transform: `scaleX(${zoomLevel})` }}
        >
          {/* Y-axis labels */}
          <div className="y-axis">
            {Object.keys(toneColors).map(tone => (
              <div key={tone} className="y-label">
                <span 
                  className="tone-dot"
                  style={{ backgroundColor: toneColors[tone] }}
                />
                {tone}
              </div>
            ))}
          </div>

          {/* Heatmap grid */}
          <div className="heatmap-grid">
            {toneData.map((data) => (
              <div key={data.nodeId} className="heatmap-column">
                {/* Tone bars */}
                {Object.entries(data.tones).map(([tone, value]) => {
                  if (selectedTone && selectedTone !== tone) return null
                  return (
                    <div
                      key={tone}
                      className="tone-cell"
                      style={{
                        backgroundColor: toneColors[tone],
                        opacity: value,
                      }}
                      title={`${data.title}: ${tone} (${(value * 100).toFixed(0)}%)`}
                    />
                  )
                })}

                {/* Intensity indicator */}
                <div 
                  className="intensity-bar"
                  style={{
                    height: `${(data.intensity / maxIntensity) * 100}%`,
                  }}
                />

                {/* Peak marker */}
                {peaks.find(p => p.nodeId === data.nodeId) && (
                  <div className="peak-marker" title="Intensity Peak">
                    ⛰️
                  </div>
                )}

                {/* Column label */}
                <div className="column-label">
                  {data.title.slice(0, 10)}
                  {data.title.length > 10 && '...'}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Genre Distribution */}
        <div className="genre-section">
          <h3>Genre Distribution</h3>
          <div className="genre-tags">
            {Array.from(new Set(toneData.flatMap(d => d.genre))).map(genre => (
              <span key={genre} className="genre-tag">
                {genre}
              </span>
            ))}
          </div>
        </div>

        {/* Peak List */}
        {peaks.length > 0 && (
          <div className="peaks-section">
            <h3>Intensity Peaks</h3>
            <div className="peaks-list">
              {peaks.map(peak => (
                <div key={peak.nodeId} className="peak-item">
                  <span className="peak-icon">⛰️</span>
                  <div className="peak-info">
                    <span className="peak-title">{peak.title}</span>
                    <span className="peak-intensity">
                      Intensity: {(peak.intensity * 100).toFixed(0)}%
                    </span>
                  </div>
                  <button 
                    className="peak-navigate"
                    onClick={() => {
                      // Navigate to node
                    }}
                  >
                    →
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Selected Node Detail */}
        {toneData.length > 0 && (
          <div className="tone-detail">
            <h3>Scene Details</h3>
            <div className="detail-grid">
              {toneData.slice(0, 1).map(data => (
                <div key={data.nodeId} className="detail-card">
                  <h4>{data.title}</h4>
                  <div className="tone-breakdown">
                    {Object.entries(data.tones)
                      .sort((a, b) => b[1] - a[1])
                      .slice(0, 3)
                      .map(([tone, value]) => (
                        <div key={tone} className="tone-item">
                          <span 
                            className="tone-color"
                            style={{ backgroundColor: toneColors[tone] }}
                          />
                          <span className="tone-name">{tone}</span>
                          <span className="tone-value">
                            {(value * 100).toFixed(0)}%
                          </span>
                        </div>
                      ))
                    }
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
