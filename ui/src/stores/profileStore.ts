import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// ==================== TYPES ====================

export interface ToneOverride {
  id: string
  category: 'narrative' | 'dialogue' | 'description' | 'pacing'
  setting: string
  value: number
  reason: string
  timestamp: string
}

export interface GenreTag {
  id: string
  name: string
  category: 'primary' | 'secondary' | 'theme'
}

export type ContentScores = {
  narrative: number
  dialogue: number
  description: number
  pacing: number
  atmosphere: number
  humor: number
  intensity: number
  romance: number
}

export interface ProfileVersion {
  id: string
  timestamp: string
  description: string
  changes: string[]
  tones: ContentScores
  genres: GenreTag[]
}

export interface AuditEntry {
  id: string
  action: 'tone_change' | 'genre_add' | 'genre_remove' | 'version_restore' | 'override_add'
  description: string
  oldValue?: string
  newValue?: string
  reason?: string
  author: string
  timestamp: string
}

export interface ProfileState {
  // Current profile settings
  tones: ContentScores
  
  // Overrides
  overrides: ToneOverride[]
  
  // Genres
  genres: GenreTag[]
  
  // Version history
  versions: ProfileVersion[]
  
  // Audit trail
  auditTrail: AuditEntry[]
  
  // Panel state
  profilePanelOpen: boolean
  activeTab: 'editor' | 'versions' | 'audit'
  
  // Comparison state
  comparingVersionId: string | null
  
  // Actions
  toggleProfilePanel: () => void
  setActiveTab: (tab: ProfileState['activeTab']) => void
  updateTone: (category: keyof ProfileState['tones'], value: number, reason?: string) => void
  addOverride: (override: Omit<ToneOverride, 'id' | 'timestamp'>) => void
  removeOverride: (overrideId: string) => void
  addGenre: (name: string, category: GenreTag['category']) => void
  removeGenre: (genreId: string) => void
  saveVersion: (description: string) => void
  restoreVersion: (versionId: string) => void
  compareVersions: (versionId: string) => void
  clearComparison: () => void
  getCurrentVersion: () => ProfileVersion
  getVersionDiff: (versionId: string) => { added: string[]; removed: string[]; changed: string[] }
}

// Available genres
const AVAILABLE_GENRES = [
  'Fantasy', 'Sci-Fi', 'Mystery', 'Thriller', 'Romance', 'Horror',
  'Adventure', 'Drama', 'Comedy', 'Action', 'Historical', 'Contemporary',
  'Dystopian', 'Supernatural', 'Noir', 'Epic', 'Slice of Life', 'Psychological'
]

// ==================== STORE IMPLEMENTATION ====================

export const useProfileStore = create<ProfileState>()(
  persist(
    (set, get) => ({
      // ==================== INITIAL STATE ====================
      tones: {
        narrative: 5,
        dialogue: 5,
        description: 5,
        pacing: 5,
        atmosphere: 5,
        humor: 3,
        intensity: 5,
        romance: 2,
      },
      
      overrides: [],
      
      genres: [
        { id: 'genre-1', name: 'Fantasy', category: 'primary' },
        { id: 'genre-2', name: 'Adventure', category: 'secondary' },
      ],
      
      versions: [],
      auditTrail: [],
      
      profilePanelOpen: false,
      activeTab: 'editor',
      comparingVersionId: null,
      
      // ==================== PANEL ACTIONS ====================
      toggleProfilePanel: () => {
        set(state => ({ profilePanelOpen: !state.profilePanelOpen }))
      },
      
      setActiveTab: (tab) => {
        set({ activeTab: tab })
      },
      
      // ==================== TONE ACTIONS ====================
      updateTone: (category, value, reason) => {
        const oldValue = get().tones[category]
        
        set(state => ({
          tones: { ...state.tones, [category]: value },
          auditTrail: [
            {
              id: `audit-${Date.now()}`,
              action: 'tone_change',
              description: `Changed ${category} tone`,
              oldValue: oldValue.toString(),
              newValue: value.toString(),
              reason,
              author: 'User',
              timestamp: new Date().toISOString(),
            },
            ...state.auditTrail,
          ],
        }))
      },
      
      addOverride: (override) => {
        const newOverride: ToneOverride = {
          ...override,
          id: `override-${Date.now()}`,
          timestamp: new Date().toISOString(),
        }
        
        set(state => ({
          overrides: [...state.overrides, newOverride],
          auditTrail: [
            {
              id: `audit-${Date.now()}`,
              action: 'override_add',
              description: `Added override: ${override.setting}`,
              reason: override.reason,
              author: 'User',
              timestamp: new Date().toISOString(),
            },
            ...state.auditTrail,
          ],
        }))
      },
      
      removeOverride: (overrideId) => {
        set(state => ({
          overrides: state.overrides.filter(o => o.id !== overrideId),
        }))
      },
      
      // ==================== GENRE ACTIONS ====================
      addGenre: (name, category) => {
        const newGenre: GenreTag = {
          id: `genre-${Date.now()}`,
          name,
          category,
        }
        
        set(state => ({
          genres: [...state.genres, newGenre],
          auditTrail: [
            {
              id: `audit-${Date.now()}`,
              action: 'genre_add',
              description: `Added genre: ${name}`,
              author: 'User',
              timestamp: new Date().toISOString(),
            },
            ...state.auditTrail,
          ],
        }))
      },
      
      removeGenre: (genreId) => {
        const genre = get().genres.find(g => g.id === genreId)
        
        set(state => ({
          genres: state.genres.filter(g => g.id !== genreId),
          auditTrail: [
            {
              id: `audit-${Date.now()}`,
              action: 'genre_remove',
              description: `Removed genre: ${genre?.name}`,
              author: 'User',
              timestamp: new Date().toISOString(),
            },
            ...state.auditTrail,
          ],
        }))
      },
      
      // ==================== VERSION ACTIONS ====================
      saveVersion: (description) => {
        const version: ProfileVersion = {
          id: `version-${Date.now()}`,
          timestamp: new Date().toISOString(),
          description,
          changes: get().auditTrail.slice(0, 5).map(a => a.description),
          tones: { ...get().tones },
          genres: [...get().genres],
        }
        
        set(state => ({
          versions: [version, ...state.versions].slice(0, 20), // Keep last 20
        }))
      },
      
      restoreVersion: (versionId) => {
        const version = get().versions.find(v => v.id === versionId)
        if (!version) return
        
        set(state => ({
          tones: version.tones,
          genres: version.genres,
          auditTrail: [
            {
              id: `audit-${Date.now()}`,
              action: 'version_restore',
              description: `Restored version: ${version.description}`,
              author: 'User',
              timestamp: new Date().toISOString(),
            },
            ...state.auditTrail,
          ],
        }))
      },
      
      compareVersions: (versionId) => {
        set({ comparingVersionId: versionId })
      },
      
      clearComparison: () => {
        set({ comparingVersionId: null })
      },
      
      getCurrentVersion: () => {
        return {
          id: 'current',
          timestamp: new Date().toISOString(),
          description: 'Current state',
          changes: [],
          tones: get().tones,
          genres: get().genres,
        }
      },
      
      getVersionDiff: (versionId) => {
        const version = get().versions.find(v => v.id === versionId)
        const current = get()
        
        if (!version) return { added: [], removed: [], changed: [] }
        
        const added: string[] = []
        const removed: string[] = []
        const changed: string[] = []
        
        // Compare tones
        Object.entries(version.tones).forEach(([key, value]) => {
          if (current.tones[key as keyof typeof current.tones] !== value) {
            changed.push(`${key}: ${value} → ${current.tones[key as keyof typeof current.tones]}`)
          }
        })
        
        // Compare genres
        const currentGenreNames = current.genres.map(g => g.name)
        const versionGenreNames = version.genres.map(g => g.name)
        
        version.genres.forEach(g => {
          if (!currentGenreNames.includes(g.name)) {
            removed.push(`Genre: ${g.name}`)
          }
        })
        
        current.genres.forEach(g => {
          if (!versionGenreNames.includes(g.name)) {
            added.push(`Genre: ${g.name}`)
          }
        })
        
        return { added, removed, changed }
      },
    }),
    {
      name: 'loom-profile',
      version: 1,
      partialize: (state) => {
        const { tones, overrides, genres, versions, auditTrail } = state
        return { tones, overrides, genres, versions, auditTrail }
      },
    }
  )
)

export { AVAILABLE_GENRES }
