import { useState, useCallback } from 'react'

/**
 * Custom hook for managing notifications
 * @returns {Object} - { notifications, showNotification, removeNotification }
 */
export const useNotifications = () => {
  const [notifications, setNotifications] = useState([])

  const showNotification = useCallback((message, type = 'info', duration = 5000) => {
    const id = Date.now() + Math.random()
    
    // Add notification
    setNotifications(prev => [...prev, { id, message, type }])
    
    // Auto-remove after duration
    if (duration > 0) {
      setTimeout(() => {
        removeNotification(id)
      }, duration)
    }
    
    return id
  }, [])

  const removeNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(notif => notif.id !== id))
  }, [])

  return {
    notifications,
    showNotification,
    removeNotification
  }
}

export default useNotifications
