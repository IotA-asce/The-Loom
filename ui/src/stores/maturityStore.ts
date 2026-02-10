import { create } from 'zustand'

// ==================== TYPES ====================

export type RatingLevel = 'G' | 'PG' | 'PG-13' | 'R' | 'NC-17'

export type ContentCategory = 'violence' | 'language' | 'sexualContent' | 'matureThemes'

export interface ContentScores {
  violence: number
  language: number
  sexualContent: number
  matureThemes: number
}

export interface ContentWarning {
  id: string
  label: string
  icon: string
  severity: 'low' | 'medium' | 'high'
  category: ContentCategory
  selected: boolean
}

export interface MaturityRating {
  code: RatingLevel
  name: string
  description: string
  minAge: number
  color: string
}

export const MATURITY_RATINGS: Record<RatingLevel, MaturityRating> = {
  'G': {
    code: 'G',
    name: 'General',
    description: 'Appropriate for all ages. No content that would offend parents for viewing by children.',
    minAge: 0,
    color: '#4caf50',
  },
  'PG': {
    code: 'PG',
    name: 'Parental Guidance',
    description: 'Some material may not be suitable for children. Parents urged to give "parental guidance".',
    minAge: 8,
    color: '#8bc34a',
  },
  'PG-13': {
    code: 'PG-13',
    name: 'Parents Strongly Cautioned',
    description: 'Some material may be inappropriate for children under 13. Parents strongly cautioned.',
    minAge: 13,
    color: '#ff9800',
  },
  'R': {
    code: 'R',
    name: 'Restricted',
    description: 'Under 17 requires accompanying parent or adult guardian. Contains adult material.',
    minAge: 17,
    color: '#f44336',
  },
  'NC-17': {
    code: 'NC-17',
    name: 'Adults Only',
    description: 'No one 17 and under admitted. Clearly adult content.',
    minAge: 18,
    color: '#b71c1c',
  },
}

export const DEFAULT_WARNINGS: ContentWarning[] = [
  { id: 'violence-mild', label: 'Mild Violence', icon: '🤜', severity: 'low', category: 'violence', selected: false },
  { id: 'violence-moderate', label: 'Moderate Violence', icon: '⚔️', severity: 'medium', category: 'violence', selected: false },
  { id: 'violence-intense', label: 'Intense Violence', icon: '💀', severity: 'high', category: 'violence', selected: false },
  { id: 'language-mild', label: 'Mild Language', icon: '🤬', severity: 'low', category: 'language', selected: false },
  { id: 'language-strong', label: 'Strong Language', icon: '🔞', severity: 'medium', category: 'language', selected: false },
  { id: 'sexual-suggestive', label: 'Suggestive Content', icon: '💋', severity: 'low', category: 'sexualContent', selected: false },
  { id: 'sexual-moderate', label: 'Moderate Sexual Content', icon: '🔥', severity: 'medium', category: 'sexualContent', selected: false },
  { id: 'sexual-explicit', label: 'Explicit Sexual Content', icon: '🚫', severity: 'high', category: 'sexualContent', selected: false },
  { id: 'themes-mature', label: 'Mature Themes', icon: '🎭', severity: 'medium', category: 'matureThemes', selected: false },
  { id: 'themes-dark', label: 'Dark/Disturbing Themes', icon: '🌑', severity: 'high', category: 'matureThemes', selected: false },
  { id: 'substance-use', label: 'Substance Use', icon: '🍷', severity: 'medium', category: 'matureThemes', selected: false },
  { id: 'fear', label: 'Scary/Intense Scenes', icon: '👻', severity: 'medium', category: 'matureThemes', selected: false },
]

// ==================== STATE ====================

export interface MaturityState {
  // Rating
  currentRating: RatingLevel
  contentScores: ContentScores
  justification: string
  
  // Target audience
  targetAudience: string | null
  
  // Warnings
  contentWarnings: ContentWarning[]
  
  // Panel state
  maturityPanelOpen: boolean
  
  // Actions
  toggleMaturityPanel: () => void
  setRating: (rating: RatingLevel) => void
  updateContentScore: (category: ContentCategory, score: number) => void
  setJustification: (justification: string) => void
  setTargetAudience: (audience: string) => void
  toggleWarning: (warningId: string) => void
  calculateRating: () => RatingLevel
  getSelectedWarnings: () => ContentWarning[]
}

// Calculate rating based on content scores
function calculateRatingFromScores(scores: ContentScores): RatingLevel {
  const maxScore = Math.max(scores.violence, scores.language, scores.sexualContent, scores.matureThemes)
  
  if (maxScore <= 2) return 'G'
  if (maxScore <= 4) return 'PG'
  if (maxScore <= 6) return 'PG-13'
  if (maxScore <= 8) return 'R'
  return 'NC-17'
}

// Generate justification based on scores
function generateJustification(scores: ContentScores): string {
  const highScores = Object.entries(scores)
    .filter(([, score]) => score >= 6)
    .map(([cat]) => cat)
  
  if (highScores.length === 0) {
    return 'This content is suitable for general audiences with minimal to no objectionable content.'
  }
  
  const categoryNames: Record<string, string> = {
    violence: 'violence',
    language: 'strong language',
    sexualContent: 'sexual content',
    matureThemes: 'mature themes',
  }
  
  const reasons = highScores.map(cat => categoryNames[cat]).join(', ')
  return `This rating is due to ${reasons}. Parental guidance is recommended for younger viewers.`
}

// ==================== STORE IMPLEMENTATION ====================

export const useMaturityStore = create<MaturityState>((set, get) => ({
  // ==================== INITIAL STATE ====================
  currentRating: 'PG-13',
  contentScores: {
    violence: 4,
    language: 3,
    sexualContent: 2,
    matureThemes: 5,
  },
  justification: 'This rating is due to mature themes and moderate violence. Parental guidance is recommended for younger viewers.',
  targetAudience: null,
  contentWarnings: DEFAULT_WARNINGS,
  maturityPanelOpen: false,
  
  // ==================== ACTIONS ====================
  toggleMaturityPanel: () => {
    set(state => ({ maturityPanelOpen: !state.maturityPanelOpen }))
  },
  
  setRating: (rating) => {
    set({ currentRating: rating })
  },
  
  updateContentScore: (category, score) => {
    set(state => {
      const newScores = { ...state.contentScores, [category]: Math.max(0, Math.min(10, score)) }
      const newRating = calculateRatingFromScores(newScores)
      return {
        contentScores: newScores,
        currentRating: newRating,
        justification: generateJustification(newScores),
      }
    })
  },
  
  setJustification: (justification) => {
    set({ justification })
  },
  
  setTargetAudience: (audience) => {
    set({ targetAudience: audience })
  },
  
  toggleWarning: (warningId) => {
    set(state => ({
      contentWarnings: state.contentWarnings.map(w =>
        w.id === warningId ? { ...w, selected: !w.selected } : w
      ),
    }))
  },
  
  calculateRating: () => {
    return calculateRatingFromScores(get().contentScores)
  },
  
  getSelectedWarnings: () => {
    return get().contentWarnings.filter(w => w.selected)
  },
}))
