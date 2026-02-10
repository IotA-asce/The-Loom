import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// ==================== TYPES ====================

export interface Bookmark {
  id: string
  nodeId: string
  label: string
  color: string
  createdAt: string
  order: number
}

export interface BookmarkState {
  // Bookmarks
  bookmarks: Bookmark[]
  
  // Actions
  addBookmark: (nodeId: string, label: string, color?: string) => void
  removeBookmark: (bookmarkId: string) => void
  updateBookmark: (bookmarkId: string, updates: Partial<Omit<Bookmark, 'id'>>) => void
  reorderBookmarks: (bookmarkIds: string[]) => void
  getBookmarkForNode: (nodeId: string) => Bookmark | undefined
  isNodeBookmarked: (nodeId: string) => boolean
  clearAllBookmarks: () => void
}

// Bookmark colors
export const BOOKMARK_COLORS = [
  { name: 'Red', value: '#ef4444' },
  { name: 'Orange', value: '#f97316' },
  { name: 'Yellow', value: '#eab308' },
  { name: 'Green', value: '#22c55e' },
  { name: 'Blue', value: '#3b82f6' },
  { name: 'Purple', value: '#a855f7' },
  { name: 'Pink', value: '#ec4899' },
  { name: 'Gray', value: '#6b7280' },
]

// ==================== STORE IMPLEMENTATION ====================

export const useBookmarkStore = create<BookmarkState>()(
  persist(
    (set, get) => ({
      // ==================== INITIAL STATE ====================
      bookmarks: [],
      
      // ==================== BOOKMARK ACTIONS ====================
      addBookmark: (nodeId, label, color) => {
        const state = get()
        
        // Check if node already has a bookmark
        const existing = state.bookmarks.find(b => b.nodeId === nodeId)
        if (existing) {
          // Update existing bookmark
          set({
            bookmarks: state.bookmarks.map(b =>
              b.id === existing.id ? { ...b, label, ...(color && { color }) } : b
            ),
          })
          return
        }
        
        // Assign a color if not provided
        const assignedColor = color || BOOKMARK_COLORS[state.bookmarks.length % BOOKMARK_COLORS.length].value
        
        const newBookmark: Bookmark = {
          id: `bookmark-${Date.now()}`,
          nodeId,
          label,
          color: assignedColor,
          createdAt: new Date().toISOString(),
          order: state.bookmarks.length,
        }
        
        set({ bookmarks: [...state.bookmarks, newBookmark] })
      },
      
      removeBookmark: (bookmarkId) => {
        set(state => ({
          bookmarks: state.bookmarks.filter(b => b.id !== bookmarkId),
        }))
      },
      
      updateBookmark: (bookmarkId, updates) => {
        set(state => ({
          bookmarks: state.bookmarks.map(b =>
            b.id === bookmarkId ? { ...b, ...updates } : b
          ),
        }))
      },
      
      reorderBookmarks: (bookmarkIds) => {
        set(state => {
          const bookmarkMap = new Map(state.bookmarks.map(b => [b.id, b]))
          const reordered = bookmarkIds
            .map(id => bookmarkMap.get(id))
            .filter((b): b is Bookmark => b !== undefined)
            .map((b, index) => ({ ...b, order: index }))
          
          return { bookmarks: reordered }
        })
      },
      
      getBookmarkForNode: (nodeId) => {
        return get().bookmarks.find(b => b.nodeId === nodeId)
      },
      
      isNodeBookmarked: (nodeId) => {
        return get().bookmarks.some(b => b.nodeId === nodeId)
      },
      
      clearAllBookmarks: () => {
        set({ bookmarks: [] })
      },
    }),
    {
      name: 'loom-bookmarks',
      version: 1,
    }
  )
)
