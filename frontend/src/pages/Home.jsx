import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { 
  faGraduationCap, 
  faFileText, 
  faChartLine, 
  faRocket,
  faArrowRight,
  faBrain,
  faCogs,
  faLightbulb,
  faPlayCircle,
  faCheckCircle,
  faGlobe,
  faShieldAlt,
  faClock,
  faBalanceScale,
  faUpload,
  faClipboardCheck,
  faSearch,
  faEye,
  faChartBar,
  faRobot,
  faFilePdf,
  faImage,
  faCog,
  faUsers,
  faBookOpen,
  faIndustry,
  faPencilAlt,
  faAward,
  faSignInAlt,
  faBars,
  faTimes
} from '@fortawesome/free-solid-svg-icons'
import './Home.css'
import axios from 'axios'
const Home = () => {
  const navigate = useNavigate()
  const [currentFeature, setCurrentFeature] = useState(0)
  const [isScrolled, setIsScrolled] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const handleGetStarted = () => {
    navigate('/upload-past-assignment')
  }

  const handleTryDemo = () => {
    navigate('/generate-assignment')
  }


    const handleLogin = async () => {
    try {
      // Call the backend through the vite proxy. Vite proxy should forward /qprs -> your FastAPI (port 8019)
      const response = await axios.get(`/sla/login`, {
        responseType: 'json',
      });
    
      if (response.status === 200) {
        const encodedResponse = response.data; 
  
        if (!encodedResponse) {
          console.error("The encoded_request is missing or undefined!");
          return;
        }
  
        const form = document.createElement('form');
        form.method = 'POST';
        // IdP SSO endpoint — keep this as your IdP Redirect endpoint
        form.action = 'https://idp.bits-pilani.ac.in/idp/profile/SAML2/Redirect/SSO';
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'SAMLRequest';
        hiddenInput.value = encodedResponse;
        form.appendChild(hiddenInput);
        document.body.appendChild(form);
        form.submit();
      } else {
        console.error("Login failed with status:", response.status);
      }
    } catch (error) {
      console.error("Error during login:", error);
    }
  };
  

  const scrollToSection = (sectionId) => {
    const element = document.getElementById(sectionId)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' })
      setIsMobileMenuOpen(false) // Close mobile menu after navigation
    }
  }

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen)
  }

  // Enhanced scroll effects
  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.pageYOffset
      setIsScrolled(scrollTop > 100)
      
      // Animate elements on scroll
      const elements = document.querySelectorAll('.animate-on-scroll')
      elements.forEach((element) => {
        const elementTop = element.offsetTop
        const elementHeight = element.offsetHeight
        const windowHeight = window.innerHeight
        
        if (scrollTop + windowHeight > elementTop + elementHeight / 3) {
          element.classList.add('in-view')
        }
      })
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const features = [
    {
      icon: faUpload,
      title: "Upload Past Assignments",
      description: "Build reference corpus by uploading PDF/DOCX past assignments with automatic text extraction and topic tagging"
    },
    {
      icon: faFileText,
      title: "AI-Powered Assignment Generation",
      description: "Generate up to 10 situational, industry-relevant assignments per request with intelligent few-shot learning"
    },
    {
      icon: faClipboardCheck,
      title: "Comprehensive Evaluation",
      description: "Evaluate student submissions with OCR, plagiarism detection, and rubric-aligned AI scoring"
    },
    {
      icon: faChartBar,
      title: "Quality Rubrics",
      description: "Generate detailed rubrics aligned to outcomes and taxonomy levels with full editing capabilities"
    }
  ]

  const benefits = [
    {
      icon: faClock,
      title: "Time Efficiency",
      description: "Reduce assignment creation and evaluation time by 80% with intelligent automation",
      color: "#3B82F6"
    },
    {
      icon: faIndustry,
      title: "Industry Relevance",
      description: "Generate assignments with real-world scenarios and industry applications",
      color: "#10B981"
    },
    {
      icon: faBrain,
      title: "AI-Powered Insights",
      description: "Get detailed analysis of assignment quality and student performance with improvement suggestions",
      color: "#F59E0B"
    },
    {
      icon: faAward,
      title: "Quality Assurance",
      description: "Comprehensive evaluation workflows ensure consistent and fair assessment",
      color: "#8B5CF6"
    },
    {
      icon: faBookOpen,
      title: "Learning Analytics",
      description: "Track student progress and identify learning gaps with detailed reporting",
      color: "#EF4444"
    }
  ]

  const workflowSteps = [
    {
      number: "01",
      title: "Upload Past Assignments",
      description: "Upload PDF/DOCX files to build a reference corpus with automatic text extraction and topic tagging",
      icon: faUpload
    },
    {
      number: "02",
      title: "Generate Assignments",
      description: "Create situational assignments using AI with course-specific topics and industry relevance",
      icon: faFileText
    },
    {
      number: "03",
      title: "Generate Rubrics",
      description: "Create detailed rubrics aligned to learning outcomes with customizable criteria and weightings",
      icon: faChartBar
    },
    {
      number: "04",
      title: "Evaluate Submissions",
      description: "Upload student submissions for AI-powered evaluation with OCR and plagiarism detection",
      icon: faClipboardCheck
    }
  ]

  const capabilities = [
    {
      icon: faFilePdf,
      title: "Multi-Format Support",
      description: "Upload PDF and DOCX assignments and submissions with automatic processing"
    },
    {
      icon: faRobot,
      title: "AI Assignment Generation",
      description: "Generate contextual assignments using few-shot learning from your reference corpus"
    },
    {
      icon: faSearch,
      title: "Smart Topic Mining",
      description: "Extract topics and subtopics from handouts and reference materials automatically"
    },
    {
      icon: faEye,
      title: "OCR Processing",
      description: "Extract text from handwritten submissions with advanced layout detection"
    },
    {
      icon: faShieldAlt,
      title: "Plagiarism Detection",
      description: "Detect copied content and AI-generated submissions with confidence scores"
    },
    {
      icon: faChartLine,
      title: "Performance Analytics",
      description: "Track assignment quality, student performance, and learning outcomes"
    }
  ]

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentFeature((prev) => (prev + 1) % features.length)
    }, 4000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="landing-container">
      {/* Header Navigation */}
      <nav className={`main-header ${isScrolled ? 'scrolled' : ''}`}>
        <div className="header-content">
          {/* Logo */}
          <div className="logo">
             <FontAwesomeIcon icon={faGraduationCap} className="logo-icon" />
            <span className="logo-text">
              <span className="spanda-bracket">[</span>
              <span className="spanda-text">Spanda</span>
              <span className="spanda-dot">.</span>
              <span className="spanda-text">AI</span>
              <span className="spanda-bracket">]</span>
            </span>
            <span className="logo-subtitle">Situated Learning</span>
          </div>

          {/* Desktop Navigation */}
          <div className="nav-links desktop-nav">
            <button className="nav-link-home" onClick={() => scrollToSection('features')}>
              Features
            </button>
            <button className="nav-link-home" onClick={() => scrollToSection('capabilities')}>
              Capabilities
            </button>
            <button className="nav-link-home" onClick={() => scrollToSection('workflow')}>
              Workflow
            </button>
            <button className="nav-link-home" onClick={() => scrollToSection('benefits')}>
              Benefits
            </button>
          </div>

          {/* Login Button and Mobile Menu Toggle */}
          <div className="header-actions">
            <button className="login-button" onClick={handleLogin}>
              <FontAwesomeIcon icon={faSignInAlt} />
              Login
            </button>
            <button 
              className="mobile-menu-toggle"
              onClick={toggleMobileMenu}
            >
              <FontAwesomeIcon icon={isMobileMenuOpen ? faTimes : faBars} />
            </button>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        <div className={`mobile-nav ${isMobileMenuOpen ? 'open' : ''}`}>
          <button className="nav-link-home mobile" onClick={() => scrollToSection('features')}>
            Features
          </button>
          <button className="nav-link-home mobile" onClick={() => scrollToSection('capabilities')}>
            Capabilities
          </button>
          <button className="nav-link-home mobile" onClick={() => scrollToSection('workflow')}>
            Workflow
          </button>
          <button className="nav-link-home mobile" onClick={() => scrollToSection('benefits')}>
            Benefits
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <header className="hero">
        <div className="hero-content">
          <div className="hero-text">
            <div className="badge">
              <FontAwesomeIcon icon={faRocket} />
              <span>Powered by AI-Driven Situated Learning</span>
            </div>
            <h1>AI-Powered Situated Learning System</h1>
            <p>
              Transform your educational workflow with intelligent assignment generation and evaluation. 
              From uploading past assignments to creating industry-relevant assessments and comprehensive 
              student evaluation, our system provides end-to-end situated learning solutions.
            </p>
            
            <div className="hero-stats">
              <div className="stat-item">
                <div className="stat-number">80%</div>
                <div className="stat-label">Time Saved</div>
              </div>
              <div className="stat-item">
                <div className="stat-number">AI</div>
                <div className="stat-label">Powered Generation</div>
              </div>
              <div className="stat-item">
                <div className="stat-number">10+</div>
                <div className="stat-label">Assignments per Request</div>
              </div>
            </div>
            
            <div className="hero-actions">
              <button className="cta-button primary" onClick={handleLogin}>
                <FontAwesomeIcon icon={faPlayCircle} />
                Get Started
                <FontAwesomeIcon icon={faArrowRight} className="arrow-icon" />
              </button>
              <button className="cta-button secondary" >
                <FontAwesomeIcon icon={faFileText} />
                Generate Assignment
              </button>
            </div>
          </div>
          
          <div className="hero-visual">
            <div className="feature-showcase">
              <div className="animated-feature-card">
                <div className="feature-icon-large">
                  <FontAwesomeIcon icon={features[currentFeature].icon} />
                </div>
                <h3>{features[currentFeature].title}</h3>
                <p>{features[currentFeature].description}</p>
              </div>
              <div className="feature-indicators">
                {features.map((_, index) => (
                  <div 
                    key={index} 
                    className={`indicator ${index === currentFeature ? 'active' : ''}`}
                    onClick={() => setCurrentFeature(index)}
                  />
                ))}
              </div>
            </div>
            
            <div className="hero-stats-cards">
              <div className="stats-card">
                <div className="stats-icon">📄</div>
                <div className="stats-content">
                  <div className="stats-number">PDF/DOCX</div>
                  <div className="stats-label">File Support</div>
                </div>
              </div>
              <div className="stats-card">
                <div className="stats-icon">🎯</div>
                <div className="stats-content">
                  <div className="stats-number">Situated</div>
                  <div className="stats-label">Learning</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Features Section */}
      <section id="features" className="features-section">
        <div className="container">
          <div className="section-header animate-on-scroll">
            <h2>Core Features</h2>
            <p>Complete workflow from content upload to assignment evaluation with AI-powered intelligence</p>
          </div>
          
          <div className="features-grid">
            {features.map((feature, index) => (
              <div key={index} className="feature-box animate-on-scroll">
                <div className="icon-container">
                  <FontAwesomeIcon icon={feature.icon} className="icon" />
                </div>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Capabilities Section */}
      <section id="capabilities" className="capabilities-section">
        <div className="container">
          <div className="section-header animate-on-scroll">
            <h2>Advanced Capabilities</h2>
            <p>Powerful tools and technologies for comprehensive situated learning management</p>
          </div>
          
          <div className="capabilities-grid">
            {capabilities.map((capability, index) => (
              <div key={index} className="capability-box animate-on-scroll">
                <div className="icon-container">
                  <FontAwesomeIcon icon={capability.icon} className="icon" />
                </div>
                <h3>{capability.title}</h3>
                <p>{capability.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section id="benefits" className="benefits-section">
        <div className="container">
          <div className="section-header animate-on-scroll">
            <h2>Why Choose Our System?</h2>
            <p>Transform your educational workflow with intelligent situated learning solutions</p>
          </div>
          
          <div className="benefits-grid">
            {benefits.map((benefit, index) => (
              <div key={index} className="benefit-card animate-on-scroll">
                <div className="benefit-icon" style={{ color: benefit.color }}>
                  <FontAwesomeIcon icon={benefit.icon} />
                </div>
                <h3>{benefit.title}</h3>
                <p>{benefit.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Workflow Section */}
      <section id="workflow" className="workflow-section">
        <div className="container">
          <div className="section-header animate-on-scroll">
            <h2>Simple 4-Step Workflow</h2>
            <p>From content upload to evaluation in minutes with AI-powered automation</p>
          </div>
          
          <div className="workflow-steps">
            {workflowSteps.map((step, index) => (
              <div key={index} className="step animate-on-scroll">
                <div className="step-number">
                  {step.number}
                </div>
                <div className="step-content">
                  <div className="step-icon">
                    <FontAwesomeIcon icon={step.icon} />
                  </div>
                  <h4>{step.title}</h4>
                  <p>{step.description}</p>
                </div>
                {index < workflowSteps.length - 1 && (
                  <div className="step-connector" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA Section */}
      <section className="final-cta-section">
        <div className="container">
          <div className="cta-content">
            <div className="cta-text">
              <h2>Ready to Transform Your Educational Workflow?</h2>
              <p>Join leading educational institutions using our AI-powered situated learning system</p>
            </div>
            <div className="cta-actions">
              <button className="cta-button primary large" onClick={handleGetStarted}>
                <FontAwesomeIcon icon={faRocket} />
                Start Upload
                <FontAwesomeIcon icon={faArrowRight} className="arrow-icon" />
              </button>
              <button className="cta-button secondary large" onClick={handleTryDemo}>
                <FontAwesomeIcon icon={faPlayCircle} />
                Generate Assignment
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

export default Home