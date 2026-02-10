import { useCallback } from 'react'
import { useOfflineStore } from '../stores/offlineStore'

/**
 * Hook for optimistic updates with offline support
 * 
 * Usage:
 * const { optimisticUpdate } = useOptimistic()
 * 
 * optimisticUpdate(
 *   'update_node',
 *   { id: nodeId, x: newX, y: newY },
 *   () => updateNodePosition(nodeId, newX, newY)
 * )
 */

export function useOptimistic() {
  const { 
    isOnline, 
    queueAction, 
    addOptimisticUpdate, 
    removeOptimisticUpdate 
  } = useOfflineStore()
  
  const optimisticUpdate = useCallback(async <T>(
    actionType: Parameters<typeof queueAction>[0]['type'],
    payload: Record<string, unknown>,
    optimisticId: string,
    optimisticData: Record<string, unknown>,
    serverAction: () => Promise<T>,
    rollback?: () => void
  ): Promise<T | null> => {
    // Apply optimistic update immediately
    addOptimisticUpdate(optimisticId, optimisticData)
    
    // If offline, queue for later
    if (!isOnline) {
      queueAction({
        type: actionType,
        payload,
      })
      return null
    }
    
    try {
      // Try to execute server action
      const result = await serverAction()
      // Success - remove optimistic update
      removeOptimisticUpdate(optimisticId)
      return result
    } catch (error) {
      // Failure - remove optimistic update and optionally rollback
      removeOptimisticUpdate(optimisticId)
      if (rollback) rollback()
      
      // Queue for retry
      queueAction({
        type: actionType,
        payload,
      })
      
      throw error
    }
  }, [isOnline, queueAction, addOptimisticUpdate, removeOptimisticUpdate])
  
  return { optimisticUpdate }
}

/**
 * Hook for queueing actions when offline
 */
export function useOfflineQueue() {
  const { isOnline, queueAction, syncPendingActions } = useOfflineStore()
  
  const queueIfOffline = useCallback(<T>(
    actionType: Parameters<typeof queueAction>[0]['type'],
    payload: Record<string, unknown>,
    onlineAction: () => Promise<T>
  ): Promise<T | null> => {
    if (!isOnline) {
      queueAction({ type: actionType, payload })
      return Promise.resolve(null)
    }
    
    return onlineAction()
  }, [isOnline, queueAction])
  
  return { queueIfOffline, syncPendingActions }
}
