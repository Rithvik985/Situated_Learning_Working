import React, { useEffect } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faCheckCircle,
  faExclamationTriangle,
  faInfoCircle,
  faTimesCircle,
  faTimes
} from '@fortawesome/free-solid-svg-icons'
import '../styles/notificationModal.css'

const NotificationModal = ({ notifications, onRemove }) => {
  const getIcon = (type) => {
    switch (type) {
      case 'success':
        return faCheckCircle
      case 'error':
        return faTimesCircle
      case 'warning':
        return faExclamationTriangle
      case 'info':
      default:
        return faInfoCircle
    }
  }

  const getClassName = (type) => {
    return `notification-modal notification-modal-${type}`
  }

  if (notifications.length === 0) {
    return null
  }

  return (
    <>
      {/* Backdrop */}
      <div className="notification-backdrop" />

      {/* Modal Container */}
      <div className="notification-modal-container">
        {notifications.map((notif) => (
          <div key={notif.id} className={getClassName(notif.type)}>
            {/* Icon */}
            <div className="modal-icon">
              <FontAwesomeIcon icon={getIcon(notif.type)} />
            </div>

            {/* Content */}
            <div className="modal-content">
              <p className="modal-message">{notif.message}</p>
            </div>

            {/* Close Button */}
            <button
              className="modal-close-btn"
              onClick={() => onRemove(notif.id)}
              aria-label="Close notification"
            >
              <FontAwesomeIcon icon={faTimes} />
            </button>
          </div>
        ))}
      </div>
    </>
  )
}

export default NotificationModal
