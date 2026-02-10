import { useEdgeStore, type EdgeType, type LineStyle } from '../stores/edgeStore'

const EDGE_COLORS = [
  { name: 'Gray', value: '#888888' },
  { name: 'Blue', value: '#4a9eff' },
  { name: 'Green', value: '#4caf50' },
  { name: 'Orange', value: '#ff9800' },
  { name: 'Red', value: '#ef4444' },
  { name: 'Purple', value: '#9c27b0' },
  { name: 'Pink', value: '#ec4899' },
  { name: 'Cyan', value: '#06b6d4' },
]
import './EdgeRenderer.css'

export function EdgeConfigPanel() {
  const {
    defaultEdgeType,
    defaultLineStyle,
    defaultColor,
    setDefaultEdgeType,
    setDefaultLineStyle,
    setDefaultColor,
  } = useEdgeStore()
  
  const edgeTypes: { type: EdgeType; label: string; description: string }[] = [
    { type: 'causal', label: 'Causal', description: 'Cause → Effect' },
    { type: 'temporal', label: 'Temporal', description: 'Before → After' },
    { type: 'parallel', label: 'Parallel', description: 'Concurrent events' },
  ]
  
  const lineStyles: { style: LineStyle; label: string }[] = [
    { style: 'solid', label: 'Solid' },
    { style: 'dashed', label: 'Dashed' },
    { style: 'dotted', label: 'Dotted' },
  ]
  
  return (
    <div className="edge-config-panel">
      <h4>🔗 Edge Settings</h4>
      
      <div className="edge-config-section">
        <label>Edge Type</label>
        <div className="edge-type-selector">
          {edgeTypes.map(({ type, label }) => (
            <button
              key={type}
              className={`edge-type-btn ${defaultEdgeType === type ? 'active' : ''}`}
              data-type={type}
              onClick={() => setDefaultEdgeType(type)}
              title={`${label}: ${edgeTypes.find(t => t.type === type)?.description}`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      
      <div className="edge-config-section">
        <label>Line Style</label>
        <div className="edge-style-selector">
          {lineStyles.map(({ style, label }) => (
            <button
              key={style}
              className={`edge-style-btn ${defaultLineStyle === style ? 'active' : ''}`}
              onClick={() => setDefaultLineStyle(style)}
            >
              <span className={`edge-style-preview ${style}`} />
              {label}
            </button>
          ))}
        </div>
      </div>
      
      <div className="edge-config-section">
        <label>Default Color</label>
        <div className="edge-color-picker">
          {EDGE_COLORS.map(({ value }: { value: string }) => (
            <button
              key={value}
              className={`edge-color-btn ${defaultColor === value ? 'active' : ''}`}
              style={{ backgroundColor: value }}
              onClick={() => setDefaultColor(value)}
              aria-label={`Select color ${value}`}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
