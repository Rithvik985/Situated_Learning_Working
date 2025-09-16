import React from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faFacebook,
  faTwitter,
  faLinkedin,
  faInstagram
} from '@fortawesome/free-brands-svg-icons'
import {
  faAddressCard,
  faTasks,
  faPhone,
  faLock
} from '@fortawesome/free-solid-svg-icons'
import './Footer.css'

const Footer = () => {
  return (
    <footer className="footer">
      <div className="footer-content">
        <div className="branding">
          <h2>
            <span className="highlight">[</span>
            <span className="text-white">Spanda</span>
            <span className="highlight">.</span>
            <span className="text-white">AI</span>
            <span className="highlight">]</span>
          </h2>
          <p>Empowering education through AI-driven situated learning solutions.</p>
          <hr className="divider" />
        </div>

        <div className="footer-links">
          <h3>Quick Links</h3>
          <ul>
            <li>
              <FontAwesomeIcon icon={faAddressCard} className="link-icon" />
              <a href="https://www.spanda.ai/about"> About Us</a>
            </li>
            <li>
              <FontAwesomeIcon icon={faTasks} className="link-icon" />
              <a href="https://www.spanda.ai/"> Services</a>
            </li>
            <li>
              <FontAwesomeIcon icon={faPhone} className="link-icon" />
              <a href="https://www.spanda.ai/contact"> Contact</a>
            </li>
            <li>
              <FontAwesomeIcon icon={faLock} className="link-icon" />
              <a href="https://www.spanda.ai/"> Privacy Policy</a>
            </li>
          </ul>
          <hr className="divider" />
        </div>
        
        <div className="social-media">
          <h3>Connect with Us</h3>
          <div className="social-icons">
            <a href="https://www.facebook.com" target="_blank" rel="noopener noreferrer">
              <FontAwesomeIcon icon={faFacebook} />
            </a>
            <a href="https://www.twitter.com" target="_blank" rel="noopener noreferrer">
              <FontAwesomeIcon icon={faTwitter} />
            </a>
            <a href="https://www.linkedin.com/company/spandaAI" target="_blank" rel="noopener noreferrer">
              <FontAwesomeIcon icon={faLinkedin} />
            </a>
            <a href="https://www.instagram.com" target="_blank" rel="noopener noreferrer">
              <FontAwesomeIcon icon={faInstagram} />
            </a>
          </div>
        </div>
      </div>
      
      <div className="footer-bottom">
        <p>&copy; {new Date().getFullYear()} Spanda.AI. All Rights Reserved.</p>
      </div>
    </footer>
  )
}

export default Footer
