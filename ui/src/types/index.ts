// Type definitions for The Loom UI

export interface ApiNode {
  node_id: string
  label: string
  branch_id: string
  scene_id: string
  x: number
  y: number
  importance: number
}

export interface ApiEdge {
  source_id: string
  target_id: string
  relation_type: string
}

export interface ApiBranch {
  branch_id: string
  parent_branch_id: string | null
  source_node_id: string
  label: string
  status: 'active' | 'archived' | 'merged'
  lineage: string[]
  created_at: string
}

export interface ApiTunerResolution {
  resolved_settings: {
    violence: number
    humor: number
    romance: number
  }
  warnings: string[]
  precedence_order: string[]
  preview: {
    tone_summary: string
    intensity_summary: string
  }
}

export interface ApiSyncState {
  scene_id: string
  text_version: string
  image_version: string
  text_status: string
  image_status: string
  badges: { label: string; icon: string }[]
  sync_visible: boolean
  sync_accurate: boolean
}

export interface ApiGraphMetrics {
  total_nodes: number
  visible_nodes: number
  visible_edges: number
  virtualization_ratio: number
  estimated_frame_ms: number
  mode: string
  performance_usable: boolean
}

export interface ApiPhase8Metrics {
  graph_performance_usable: boolean
  keyboard_mobile_usable: boolean
  dual_sync_visible_and_accurate: boolean
  virtualization_ratio: number
  estimated_frame_ms: number
  keyboard_coverage: number
  mismatch_rate: number
}
