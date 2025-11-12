import React from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { 
  faCheckCircle, 
  faExclamationTriangle, 
  faInfoCircle, 
  faTimesCircle,
  faTimes
} from '@fortawesome/free-solid-svg-icons'
import '../styles/notifications.css'

const NotificationContainer = ({ notifications, onRemove }) => {
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
    return `notification notification-${type}`
  }

  return (
    <div className="notification-container">
      {notifications.map((notif) => (
        <div key={notif.id} className={getClassName(notif.type)}>
          <div className="notification-content">
            <FontAwesomeIcon icon={getIcon(notif.type)} className="notification-icon" />
            <span className="notification-message">{notif.message}</span>
          </div>
          <button
            className="notification-close"
            onClick={() => onRemove(notif.id)}
            aria-label="Close notification"
          >
            <FontAwesomeIcon icon={faTimes} />
          </button>
        </div>
      ))}
    </div>
  )
}

export default NotificationContainer
