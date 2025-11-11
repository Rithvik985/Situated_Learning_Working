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
  faHome,
  faSignOutAlt
} from '@fortawesome/free-solid-svg-icons'
import './Header.css'
import axios from 'axios'

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

const handleLogout = async () => {
  try {
    const response = await axios.get(
      `/sla/logout`,  // ✅ corrected endpoint
      { withCredentials: true }
    );

    if (response.data?.success) {
      window.location.href = response.data.redirect_url;
    } else {
      console.warn('Logout API returned unexpected response:', response.data);
    }
  } catch (error) {
    console.error('Logout failed:', error);
  }
};


  return (
    <header className={`header ${isScrolled ? 'scrolled' : ''}`}>
      <div className="container">
        <div className="header-content-bar">
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
              to="/faculty/dashboard" 
              className={`nav-link ${isActive('/faculty-dashboard') ? 'active' : ''}`}
            >
              <FontAwesomeIcon icon={faChartLine} />
              Faculty Dashboard
            </Link>
            <Link 
              to="/faculty/evaluation" 
              className={`nav-link ${isActive('/faculty-evaluation') ? 'active' : ''}`}
            >
              <FontAwesomeIcon icon={faClipboardCheck} />
              Faculty Evaluation
            </Link>
            <Link 
              to="/student/evaluation" 
              className={`nav-link ${isActive('/student-evaluation') ? 'active' : ''}`}
            >
              <FontAwesomeIcon icon={faFileText} />
              Student Evaluation
            </Link>
            <Link 
              to="/student-workflow" 
              className={`nav-link ${isActive('/student-workflow') ? 'active' : ''}`}
            >
              <FontAwesomeIcon icon={faHome} />
              Student Workflow
            </Link>
            <Link 
              to="/dashboard" 
              className={`nav-link ${isActive('/dashboard') ? 'active' : ''}`}
            >
              <FontAwesomeIcon icon={faChartLine} />
              Analytics
            </Link>
          </nav>

          {/* Logout Button - Desktop */}
          <button 
            className="logout-btn"
            onClick={handleLogout}
            aria-label="Logout"
          >
            <FontAwesomeIcon icon={faSignOutAlt} />
            Logout
          </button>

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
            to="/faculty-dashboard" 
            className={`nav-link ${isActive('/faculty-dashboard') ? 'active' : ''}`}
            onClick={closeMobileMenu}
          >
            <FontAwesomeIcon icon={faChartLine} />
            Faculty Dashboard
          </Link>
          <Link 
            to="/faculty-evaluation" 
            className={`nav-link ${isActive('/faculty-evaluation') ? 'active' : ''}`}
            onClick={closeMobileMenu}
          >
            <FontAwesomeIcon icon={faClipboardCheck} />
            Faculty Evaluation
          </Link>
          <Link 
            to="/student-evaluation" 
            className={`nav-link ${isActive('/student-evaluation') ? 'active' : ''}`}
            onClick={closeMobileMenu}
          >
            <FontAwesomeIcon icon={faFileText} />
            Student Evaluation
          </Link>
          <Link 
            to="/student-workflow" 
            className={`nav-link ${isActive('/student-workflow') ? 'active' : ''}`}
            onClick={closeMobileMenu}
          >
            <FontAwesomeIcon icon={faHome} />
            Student Workflow
          </Link>
          <Link 
            to="/analytics" 
            className={`nav-link ${isActive('/analytics') ? 'active' : ''}`}
            onClick={closeMobileMenu}
          >
            <FontAwesomeIcon icon={faChartLine} />
            Analytics
          </Link>
          
          {/* Logout Button - Mobile */}
          <button 
            className="logout-btn mobile"
            onClick={() => {
              handleLogout()
              closeMobileMenu()
            }}
            aria-label="Logout"
          >
            <FontAwesomeIcon icon={faSignOutAlt} />
            Logout
          </button>
        </nav>
      </div>
    </header>
  )
}

export default Header