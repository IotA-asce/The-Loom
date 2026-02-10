import { useEffect } from 'react'
import { useOfflineStore } from '../stores/offlineStore'
import './OfflineStatus.css'

export function OfflineStatus() {
  const { 
    isOnline, 
    setOnlineStatus, 
    isSyncing, 
    syncError,
    syncPendingActions,
    getPendingCount,
    getFailedCount,
  } = useOfflineStore()
  
  const pendingCount = getPendingCount()
  const failedCount = getFailedCount()
  
  // Listen for online/offline events
  useEffect(() => {
    const handleOnline = () => setOnlineStatus(true)
    const handleOffline = () => setOnlineStatus(false)
    
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [setOnlineStatus])
  
  // Auto-sync when online and pending
  useEffect(() => {
    if (isOnline && pendingCount > 0 && !isSyncing) {
      syncPendingActions()
    }
  }, [isOnline, pendingCount, isSyncing, syncPendingActions])
  
  if (isOnline && pendingCount === 0 && !syncError) {
    return (
      <div className="offline-status online">
        <span className="status-dot" />
        <span className="status-text">Synced</span>
      </div>
    )
  }
  
  if (!isOnline) {
    return (
      <div className="offline-status offline">
        <span className="status-icon">⚠️</span>
        <span className="status-text">Offline</span>
        {pendingCount > 0 && (
          <span className="pending-badge">{pendingCount} pending</span>
        )}
      </div>
    )
  }
  
  return (
    <div className={`offline-status ${isSyncing ? 'syncing' : ''} ${syncError ? 'error' : ''}`}>
      {isSyncing ? (
        <>
          <span className="sync-spinner" />
          <span className="status-text">Syncing...</span>
        </>
      ) : syncError ? (
        <>
          <span className="status-icon">❌</span>
          <span className="status-text">Sync failed</span>
          {failedCount > 0 && (
            <span className="failed-badge">{failedCount} failed</span>
          )}
        </>
      ) : (
        <>
          <span className="status-icon">🔄</span>
          <span className="status-text">{pendingCount} pending</span>
        </>
      )}
    </div>
  )
}

// Offline banner for when app goes offline
export function OfflineBanner() {
  const { isOnline, pendingActions } = useOfflineStore()
  
  if (isOnline) return null
  
  return (
    <div className="offline-banner">
      <span className="banner-icon">📡</span>
      <span className="banner-text">
        You're offline. Changes will be saved locally and synced when you reconnect.
      </span>
      {pendingActions.length > 0 && (
        <span className="pending-count">{pendingActions.length} changes queued</span>
      )}
    </div>
  )
}
