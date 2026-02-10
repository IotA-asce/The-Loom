import { useEffect, useCallback } from 'react'
import { useAppStore } from '../store'
import './Toast.css'

interface Toast {
  id: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  duration?: number
}

// Toast container component
export function ToastContainer() {
  const { toasts, removeToast } = useAppStore()

  return (
    <div className="toast-container" role="region" aria-label="Notifications">
      {toasts.map((toast) => (
        <ToastItem
          key={toast.id}
          toast={toast}
          onClose={() => removeToast(toast.id)}
        />
      ))}
    </div>
  )
}

// Individual toast item
function ToastItem({ toast, onClose }: { toast: Toast; onClose: () => void }) {
  useEffect(() => {
    const timer = setTimeout(onClose, toast.duration || 5000)
    return () => clearTimeout(timer)
  }, [onClose, toast.duration])

  const icons = {
    info: 'ℹ️',
    success: '✅',
    warning: '⚠️',
    error: '❌',
  }

  return (
    <div
      className={`toast toast-${toast.type}`}
      role="alert"
      aria-live="polite"
    >
      <span className="toast-icon">{icons[toast.type]}</span>
      <span className="toast-message">{toast.message}</span>
      <button
        onClick={onClose}
        className="toast-close"
        aria-label="Dismiss notification"
      >
        ×
      </button>
    </div>
  )
}

// Hook for easy toast usage
export function useToast() {
  const { addToast } = useAppStore()

  const toast = useCallback(
    (message: string, type: Toast['type'] = 'info', duration?: number) => {
      addToast({ message, type, duration })
    },
    [addToast]
  )

  return {
    toast,
    info: (msg: string, duration?: number) => toast(msg, 'info', duration),
    success: (msg: string, duration?: number) => toast(msg, 'success', duration),
    warning: (msg: string, duration?: number) => toast(msg, 'warning', duration),
    error: (msg: string, duration?: number) => toast(msg, 'error', duration),
  }
}
