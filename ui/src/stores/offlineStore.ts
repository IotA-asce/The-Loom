import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// ==================== TYPES ====================

export type PendingActionType = 
  | 'create_node' 
  | 'update_node' 
  | 'delete_node' 
  | 'create_branch'
  | 'add_comment'
  | 'update_metadata'

export interface PendingAction {
  id: string
  type: PendingActionType
  payload: Record<string, unknown>
  timestamp: string
  retryCount: number
  status: 'pending' | 'processing' | 'failed'
  error?: string
}

export interface OfflineState {
  // Online status
  isOnline: boolean
  lastOnlineAt: string | null
  
  // Pending actions queue
  pendingActions: PendingAction[]
  
  // Sync status
  isSyncing: boolean
  lastSyncAt: string | null
  syncError: string | null
  
  // Optimistic updates
  optimisticUpdates: Map<string, Record<string, unknown>>
  
  // Actions
  setOnlineStatus: (online: boolean) => void
  queueAction: (action: Omit<PendingAction, 'id' | 'timestamp' | 'retryCount' | 'status'>) => void
  removePendingAction: (actionId: string) => void
  markActionFailed: (actionId: string, error: string) => void
  retryAction: (actionId: string) => void
  syncPendingActions: () => Promise<void>
  clearPendingActions: () => void
  addOptimisticUpdate: (id: string, data: Record<string, unknown>) => void
  removeOptimisticUpdate: (id: string) => void
  getPendingCount: () => number
  getFailedCount: () => number
}

// ==================== STORE IMPLEMENTATION ====================

export const useOfflineStore = create<OfflineState>()(
  persist(
    (set, get) => ({
      // ==================== INITIAL STATE ====================
      isOnline: navigator.onLine,
      lastOnlineAt: navigator.onLine ? new Date().toISOString() : null,
      
      pendingActions: [],
      
      isSyncing: false,
      lastSyncAt: null,
      syncError: null,
      
      optimisticUpdates: new Map(),
      
      // ==================== ONLINE STATUS ====================
      setOnlineStatus: (online) => {
        const wasOffline = !get().isOnline && online
        set({ 
          isOnline: online,
          lastOnlineAt: online ? new Date().toISOString() : get().lastOnlineAt,
        })
        
        // Auto-sync when coming back online
        if (wasOffline && get().pendingActions.length > 0) {
          get().syncPendingActions()
        }
      },
      
      // ==================== ACTION QUEUE ====================
      queueAction: (action) => {
        const newAction: PendingAction = {
          ...action,
          id: `action-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          timestamp: new Date().toISOString(),
          retryCount: 0,
          status: 'pending',
        }
        
        set(state => ({
          pendingActions: [...state.pendingActions, newAction],
        }))
        
        // If online, try to sync immediately
        if (get().isOnline) {
          get().syncPendingActions()
        }
      },
      
      removePendingAction: (actionId) => {
        set(state => ({
          pendingActions: state.pendingActions.filter(a => a.id !== actionId),
        }))
      },
      
      markActionFailed: (actionId, error) => {
        set(state => ({
          pendingActions: state.pendingActions.map(a =>
            a.id === actionId ? { ...a, status: 'failed', error } : a
          ),
        }))
      },
      
      retryAction: (actionId) => {
        set(state => ({
          pendingActions: state.pendingActions.map(a =>
            a.id === actionId ? { ...a, status: 'pending', retryCount: a.retryCount + 1 } : a
          ),
        }))
        get().syncPendingActions()
      },
      
      // ==================== SYNC ====================
      syncPendingActions: async () => {
        const { pendingActions, isOnline } = get()
        
        if (!isOnline || pendingActions.length === 0 || get().isSyncing) {
          return
        }
        
        set({ isSyncing: true, syncError: null })
        
        const pending = pendingActions.filter(a => a.status === 'pending')
        
        for (const action of pending) {
          try {
            // Mark as processing
            set(state => ({
              pendingActions: state.pendingActions.map(a =>
                a.id === action.id ? { ...a, status: 'processing' } : a
              ),
            }))
            
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 300))
            
            // Success - remove from queue
            get().removePendingAction(action.id)
            
            // Remove optimistic update if exists
            const optimisticId = `${action.type}-${action.payload.id}`
            get().removeOptimisticUpdate(optimisticId)
            
          } catch (error) {
            const errorMsg = error instanceof Error ? error.message : 'Unknown error'
            get().markActionFailed(action.id, errorMsg)
          }
        }
        
        set({ 
          isSyncing: false, 
          lastSyncAt: new Date().toISOString(),
          syncError: pendingActions.some(a => a.status === 'failed') 
            ? 'Some actions failed to sync' 
            : null,
        })
      },
      
      clearPendingActions: () => {
        set({ pendingActions: [], syncError: null })
      },
      
      // ==================== OPTIMISTIC UPDATES ====================
      addOptimisticUpdate: (id, data) => {
        set(state => {
          const newMap = new Map(state.optimisticUpdates)
          newMap.set(id, data)
          return { optimisticUpdates: newMap }
        })
      },
      
      removeOptimisticUpdate: (id) => {
        set(state => {
          const newMap = new Map(state.optimisticUpdates)
          newMap.delete(id)
          return { optimisticUpdates: newMap }
        })
      },
      
      // ==================== HELPERS ====================
      getPendingCount: () => {
        return get().pendingActions.filter(a => a.status === 'pending').length
      },
      
      getFailedCount: () => {
        return get().pendingActions.filter(a => a.status === 'failed').length
      },
    }),
    {
      name: 'loom-offline',
      version: 1,
      partialize: (state) => ({
        pendingActions: state.pendingActions,
        lastOnlineAt: state.lastOnlineAt,
        lastSyncAt: state.lastSyncAt,
      }),
    }
  )
)
