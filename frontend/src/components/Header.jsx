import React, { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { 
  faGraduationCap, 
  faBars, 
  faTimes,
  faFileText,
  faChartLine,
  faUpload,
  faClipboardCheck,
  faHome
} from '@fortawesome/free-solid-svg-icons'
import './Header.css'

const Header = () => {
  const [isScrolled, setIsScrolled] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const location = useLocation()

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50)
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen)
  }

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false)
  }

  const isActive = (path) => {
    return location.pathname === path
  }

  return (
    <header className={`header ${isScrolled ? 'scrolled' : ''}`}>
      <div className="container">
        <div className="header-content">
          {/* Logo - Centered */}
          <Link to="/" className="logo" onClick={closeMobileMenu}>
            <FontAwesomeIcon icon={faGraduationCap} className="logo-icon" />
            <span className="logo-text">
              <span className="spanda-bracket">[</span>
              <span className="spanda-text">Spanda</span>
              <span className="spanda-dot">.</span>
              <span className="spanda-text">AI</span>
              <span className="spanda-bracket">]</span>
            </span>
            <span className="logo-subtitle">Situated Learning</span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="nav-desktop">
            <Link 
              to="/upload-past-assignment" 
              className={`nav-link ${isActive('/upload-past-assignment') ? 'active' : ''}`}
            >
              <FontAwesomeIcon icon={faUpload} />
              Upload Past Assignments
            </Link>
            <Link 
              to="/generate-assignment" 
              className={`nav-link ${isActive('/generate-assignment') ? 'active' : ''}`}
            >
              <FontAwesomeIcon icon={faFileText} />
              Generate Assignment
            </Link>
            <Link 
              to="/evaluation" 
              className={`nav-link ${isActive('/evaluation') ? 'active' : ''}`}
            >
              <FontAwesomeIcon icon={faClipboardCheck} />
              Evaluation
            </Link>
            <Link 
              to="/analytics" 
              className={`nav-link ${isActive('/analytics') ? 'active' : ''}`}
            >
              <FontAwesomeIcon icon={faChartLine} />
              Analytics
            </Link>
          </nav>

          {/* Mobile Menu Button */}
          <button 
            className="mobile-menu-btn"
            onClick={toggleMobileMenu}
            aria-label="Toggle mobile menu"
          >
            <FontAwesomeIcon 
              icon={isMobileMenuOpen ? faTimes : faBars} 
              className="mobile-menu-icon"
            />
          </button>
        </div>

        {/* Mobile Navigation */}
        <nav className={`nav-mobile ${isMobileMenuOpen ? 'open' : ''}`}>
          <Link 
            to="/upload-past-assignment" 
            className={`nav-link ${isActive('/upload-past-assignment') ? 'active' : ''}`}
            onClick={closeMobileMenu}
          >
            <FontAwesomeIcon icon={faUpload} />
            Upload Past Assignments
          </Link>
          <Link 
            to="/generate-assignment" 
            className={`nav-link ${isActive('/generate-assignment') ? 'active' : ''}`}
            onClick={closeMobileMenu}
          >
            <FontAwesomeIcon icon={faFileText} />
            Generate Assignment
          </Link>
          <Link 
            to="/evaluation" 
            className={`nav-link ${isActive('/evaluation') ? 'active' : ''}`}
            onClick={closeMobileMenu}
          >
            <FontAwesomeIcon icon={faClipboardCheck} />
            Evaluation
          </Link>
          <Link 
            to="/analytics" 
            className={`nav-link ${isActive('/analytics') ? 'active' : ''}`}
            onClick={closeMobileMenu}
          >
            <FontAwesomeIcon icon={faChartLine} />
            Analytics
          </Link>
        </nav>
      </div>
    </header>
  )
}

export default Header