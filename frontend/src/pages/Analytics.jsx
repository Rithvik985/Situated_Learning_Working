import React, { useState, useEffect } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { 
  faChartLine, 
  faFilter, 
  faDownload,
  faSpinner,
  faExclamationTriangle,
  faInfoCircle,
  faCheckCircle,
  faGraduationCap,
  faFileText,
  faUsers,
  faClipboardCheck,
  faEdit,
  faTags,
  faChartBar,
  faChartPie,
  faArrowTrendUp,
  faCalendarAlt,
  faRefresh,
  faTimes,
  faEye,
  faEyeSlash
} from '@fortawesome/free-solid-svg-icons'
import { API_CONFIG } from '../config/api'
import './Analytics.css'

const Analytics = () => {
  // State management
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [refreshing, setRefreshing] = useState(false)
  
  // Filter state
  const [filters, setFilters] = useState({
    courseFilter: '',
    academicYearFilter: '',
    timeRange: 30
  })
  const [availableFilters, setAvailableFilters] = useState({
    course_titles: [],
    academic_years: []
  })
  const [showFilters, setShowFilters] = useState(false)
  
  // Analytics data
  const [overviewData, setOverviewData] = useState(null)
  const [usageData, setUsageData] = useState(null)
  const [contentData, setContentData] = useState(null)
  const [learningData, setLearningData] = useState(null)
  
  // UI state
  const [activeSection, setActiveSection] = useState('overview')
  const [notifications, setNotifications] = useState([])

  // Load data on component mount
  useEffect(() => {
    loadAvailableFilters()
    loadAllAnalytics()
  }, [])

  // Reload data when filters change
  useEffect(() => {
    if (overviewData) { // Only reload if data has been loaded at least once
      loadAllAnalytics()
    }
  }, [filters])

  const showNotification = (message, type = 'info') => {
    const id = Date.now()
    setNotifications(prev => [...prev, { id, message, type }])
    setTimeout(() => {
      setNotifications(prev => prev.filter(notif => notif.id !== id))
    }, 5000)
  }

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(notif => notif.id !== id))
  }

  const loadAvailableFilters = async () => {
    try {
      const response = await fetch(`${API_CONFIG.ANALYTICS_URL}/api/analytics/courses`)
      if (!response.ok) throw new Error('Failed to load filter options')
      const data = await response.json()
      setAvailableFilters(data)
    } catch (err) {
      console.error('Error loading filters:', err)
      showNotification('Failed to load filter options', 'error')
    }
  }

  const loadAllAnalytics = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const params = new URLSearchParams()
      if (filters.courseFilter) params.append('course_filter', filters.courseFilter)
      if (filters.academicYearFilter) params.append('academic_year_filter', filters.academicYearFilter)
      
      const [overviewRes, usageRes, contentRes, learningRes] = await Promise.all([
        fetch(`${API_CONFIG.ANALYTICS_URL}/api/analytics/overview?${params}`),
        fetch(`${API_CONFIG.ANALYTICS_URL}/api/analytics/usage?days=${filters.timeRange}&${params}`),
        fetch(`${API_CONFIG.ANALYTICS_URL}/api/analytics/content?${params}`),
        fetch(`${API_CONFIG.ANALYTICS_URL}/api/analytics/learning?${params}`)
      ])

      if (!overviewRes.ok || !usageRes.ok || !contentRes.ok || !learningRes.ok) {
        throw new Error('Failed to load analytics data')
      }

      const [overview, usage, content, learning] = await Promise.all([
        overviewRes.json(),
        usageRes.json(),
        contentRes.json(),
        learningRes.json()
      ])

      setOverviewData(overview)
      setUsageData(usage)
      setContentData(content)
      setLearningData(learning)

    } catch (err) {
      console.error('Error loading analytics:', err)
      setError(err.message)
      showNotification('Failed to load analytics data', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    await loadAllAnalytics()
    setRefreshing(false)
    showNotification('Analytics data refreshed successfully!', 'success')
  }

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }))
  }

  const clearFilters = () => {
    setFilters({
      courseFilter: '',
      academicYearFilter: '',
      timeRange: 30
    })
  }

  const exportData = async () => {
    try {
      const params = new URLSearchParams()
      if (filters.courseFilter) params.append('course_filter', filters.courseFilter)
      if (filters.academicYearFilter) params.append('academic_year_filter', filters.academicYearFilter)
      
      const response = await fetch(`${API_CONFIG.ANALYTICS_URL}/api/analytics/export?${params}`)
      if (!response.ok) throw new Error('Failed to export data')
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      
      // Get filename from response headers or use default
      const contentDisposition = response.headers.get('Content-Disposition')
      let filename = `analytics_report_${new Date().toISOString().split('T')[0]}.pdf`
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/)
        if (filenameMatch) {
          filename = filenameMatch[1]
        }
      }
      
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      showNotification('Analytics report exported successfully!', 'success')
    } catch (err) {
      console.error('Error exporting data:', err)
      showNotification('Failed to export report', 'error')
    }
  }

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
    return num.toString()
  }

  const formatPercentage = (num) => {
    return `${num}%`
  }

  if (loading && !overviewData) {
    return (
      <div className="analytics-container">
        <div className="loading-container">
          <FontAwesomeIcon icon={faSpinner} spin size="3x" style={{ color: 'var(--primary)' }} />
          <p className="loading-text">Loading analytics dashboard...</p>
        </div>
      </div>
    )
  }

  if (error && !overviewData) {
    return (
      <div className="analytics-container">
        <div className="error-container">
          <FontAwesomeIcon icon={faExclamationTriangle} size="3x" style={{ color: '#ef4444' }} />
          <h2 className="error-title">Failed to Load Analytics</h2>
          <p className="error-message">{error}</p>
          <button className="btn btn-primary" onClick={loadAllAnalytics}>
            <FontAwesomeIcon icon={faRefresh} style={{ marginRight: '0.5rem' }} />
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="analytics-container">
      {/* Header */}
      <div className="analytics-header">
        <div className="header-content">
          <div className="header-text">
            <div style={{ fontSize: '3rem', color: 'var(--primary)', marginBottom: '1rem' }}>
              <FontAwesomeIcon icon={faChartLine} />
            </div>
            <h1>Analytics Dashboard</h1>
            <p>Comprehensive insights into your situated learning system usage, content quality, and learning outcomes.</p>
          </div>
          
          <div className="header-actions">
            <button 
              className="btn btn-outline"
              onClick={() => setShowFilters(!showFilters)}
            >
              <FontAwesomeIcon icon={faFilter} style={{ marginRight: '0.5rem' }} />
              {showFilters ? 'Hide Filters' : 'Show Filters'}
            </button>
            <button 
              className="btn btn-secondary"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              <FontAwesomeIcon icon={refreshing ? faSpinner : faRefresh} spin={refreshing} style={{ marginRight: '0.5rem' }} />
              Refresh
            </button>
            <button 
              className="btn btn-primary"
              onClick={exportData}
            >
              <FontAwesomeIcon icon={faDownload} style={{ marginRight: '0.5rem' }} />
              Export Data
            </button>
          </div>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="filters-panel">
            <div className="filters-content">
              <div className="filter-group">
                <label className="filter-label">Course</label>
                <select
                  className="filter-select"
                  value={filters.courseFilter}
                  onChange={(e) => handleFilterChange('courseFilter', e.target.value)}
                >
                  <option value="">All Courses</option>
                  {availableFilters.course_titles.map(title => (
                    <option key={title} value={title}>{title}</option>
                  ))}
                </select>
              </div>

              <div className="filter-group">
                <label className="filter-label">Academic Year</label>
                <select
                  className="filter-select"
                  value={filters.academicYearFilter}
                  onChange={(e) => handleFilterChange('academicYearFilter', e.target.value)}
                >
                  <option value="">All Years</option>
                  {availableFilters.academic_years.map(year => (
                    <option key={year} value={year}>{year}</option>
                  ))}
                </select>
              </div>

              <div className="filter-group">
                <label className="filter-label">Time Range</label>
                <select
                  className="filter-select"
                  value={filters.timeRange}
                  onChange={(e) => handleFilterChange('timeRange', parseInt(e.target.value))}
                >
                  <option value={7}>Last 7 days</option>
                  <option value={30}>Last 30 days</option>
                  <option value={90}>Last 3 months</option>
                  <option value={365}>Last year</option>
                </select>
              </div>

              <div className="filter-actions">
                <button className="btn btn-outline btn-sm" onClick={clearFilters}>
                  <FontAwesomeIcon icon={faTimes} style={{ marginRight: '0.25rem' }} />
                  Clear
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Notifications */}
      <div className="notifications-container">
        {notifications.map(notification => (
          <div
            key={notification.id}
            className={`notification notification-${notification.type}`}
          >
            <FontAwesomeIcon 
              icon={notification.type === 'error' ? faExclamationTriangle : 
                    notification.type === 'success' ? faCheckCircle : faInfoCircle} 
            />
            <span className="notification-message">{notification.message}</span>
            <button
              className="notification-close"
              onClick={() => removeNotification(notification.id)}
            >
              <FontAwesomeIcon icon={faTimes} size="sm" />
            </button>
          </div>
        ))}
      </div>

      {/* Navigation Tabs */}
      <div className="analytics-nav">
        {[
          { key: 'overview', label: 'Overview', icon: faChartBar },
          { key: 'usage', label: 'Usage Trends', icon: faArrowTrendUp },
          { key: 'content', label: 'Content Analytics', icon: faEdit },
          { key: 'learning', label: 'Learning Outcomes', icon: faGraduationCap }
        ].map(tab => (
          <button
            key={tab.key}
            className={`nav-tab ${activeSection === tab.key ? 'active' : ''}`}
            onClick={() => setActiveSection(tab.key)}
          >
            <FontAwesomeIcon icon={tab.icon} />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Analytics Content */}
      <div className="analytics-content">
        {activeSection === 'overview' && overviewData && (
          <div className="analytics-section">
            <h2 className="section-title">System Overview</h2>
            
            <div className="metrics-grid">
              <div className="metric-card">
                <div className="metric-icon">
                  <FontAwesomeIcon icon={faGraduationCap} />
                </div>
                <div className="metric-content">
                  <div className="metric-value">{formatNumber(overviewData.total_courses)}</div>
                  <div className="metric-label">Active Courses</div>
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-icon">
                  <FontAwesomeIcon icon={faFileText} />
                </div>
                <div className="metric-content">
                  <div className="metric-value">{formatNumber(overviewData.total_generated_assignments)}</div>
                  <div className="metric-label">Generated Assignments</div>
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-icon">
                  <FontAwesomeIcon icon={faUsers} />
                </div>
                <div className="metric-content">
                  <div className="metric-value">{formatNumber(overviewData.total_student_submissions)}</div>
                  <div className="metric-label">Student Submissions</div>
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-icon">
                  <FontAwesomeIcon icon={faClipboardCheck} />
                </div>
                <div className="metric-content">
                  <div className="metric-value">{formatNumber(overviewData.total_evaluations)}</div>
                  <div className="metric-label">Evaluations Completed</div>
                </div>
              </div>
            </div>

            <div className="quality-metrics">
              <div className="quality-card">
                <div className="quality-header">
                  <FontAwesomeIcon icon={faEdit} />
                  <h3>Assignment Modification Rate</h3>
                </div>
                <div className="quality-content">
                  <div className="quality-percentage">
                    {formatPercentage(overviewData.assignment_modification_rate)}
                  </div>
                  <div className="quality-description">
                    Percentage of AI-generated assignments that were modified by faculty
                  </div>
                  <div className="quality-bar">
                    <div 
                      className="quality-fill"
                      style={{ width: `${overviewData.assignment_modification_rate}%` }}
                    />
                  </div>
                </div>
              </div>

              <div className="quality-card">
                <div className="quality-header">
                  <FontAwesomeIcon icon={faTags} />
                  <h3>Rubric Edit Rate</h3>
                </div>
                <div className="quality-content">
                  <div className="quality-percentage">
                    {formatPercentage(overviewData.rubric_edit_rate)}
                  </div>
                  <div className="quality-description">
                    Percentage of generated rubrics that were edited by faculty
                  </div>
                  <div className="quality-bar">
                    <div 
                      className="quality-fill"
                      style={{ width: `${overviewData.rubric_edit_rate}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeSection === 'usage' && usageData && (
          <div className="analytics-section">
            <h2 className="section-title">Usage Trends</h2>
            
            {/* Daily Usage Chart */}
            <div className="chart-container">
              <h3 className="chart-title">Daily Assignment Generation</h3>
              <div className="simple-chart">
                {usageData.daily_usage.slice(-14).map((day, index) => (
                  <div key={index} className="chart-bar">
                    <div 
                      className="bar-fill"
                      style={{ 
                        height: `${Math.max(day.generated_assignments * 10, 5)}px`,
                        minHeight: '5px'
                      }}
                      title={`${day.date}: ${day.generated_assignments} assignments`}
                    />
                    <div className="bar-label">
                      {new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Course Activity */}
            <div className="table-container">
              <h3 className="table-title">Most Active Courses</h3>
              <div className="data-table">
                <div className="table-header">
                  <div className="table-cell">Course</div>
                  <div className="table-cell">Code</div>
                  <div className="table-cell">Year</div>
                  <div className="table-cell">Assignments</div>
                </div>
                {usageData.course_activity.slice(0, 10).map((course, index) => (
                  <div key={index} className="table-row">
                    <div className="table-cell">{course.course_title}</div>
                    <div className="table-cell">{course.course_code}</div>
                    <div className="table-cell">{course.academic_year}</div>
                    <div className="table-cell">
                      <span className="activity-badge">{course.assignment_count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeSection === 'content' && contentData && (
          <div className="analytics-section">
            <h2 className="section-title">Content Analytics</h2>
            
            {/* Assignment Modifications */}
            <div className="content-grid">
              <div className="content-card">
                <h3 className="card-title">Assignment Modifications by Course</h3>
                <div className="modifications-list">
                  {contentData.assignment_modifications.slice(0, 8).map((mod, index) => (
                    <div key={index} className="modification-item">
                      <div className="modification-header">
                        <span className="course-name">{mod.course_name}</span>
                        <span className="modification-rate">{formatPercentage(mod.modification_rate)}</span>
                      </div>
                      <div className="modification-details">
                        {mod.modified_assignments} of {mod.total_assignments} assignments modified
                      </div>
                      <div className="modification-bar">
                        <div 
                          className="modification-fill"
                          style={{ width: `${mod.modification_rate}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="content-card">
                <h3 className="card-title">Difficulty Distribution</h3>
                <div className="difficulty-chart">
                  {contentData.difficulty_distribution.map((diff, index) => (
                    <div key={index} className="difficulty-item">
                      <div className="difficulty-label">{diff.difficulty}</div>
                      <div className="difficulty-bar">
                        <div 
                          className="difficulty-fill"
                          style={{ width: `${(diff.count / Math.max(...contentData.difficulty_distribution.map(d => d.count))) * 100}%` }}
                        />
                      </div>
                      <div className="difficulty-count">{diff.count}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Rubric Edits Summary */}
            <div className="summary-card">
              <h3 className="card-title">Rubric Editing Summary</h3>
              {contentData.rubric_edits.map((edit, index) => (
                <div key={index} className="summary-content">
                  <div className="summary-stat">
                    <div className="stat-value">{edit.total_rubrics}</div>
                    <div className="stat-label">Total Rubrics</div>
                  </div>
                  <div className="summary-stat">
                    <div className="stat-value">{edit.edited_rubrics}</div>
                    <div className="stat-label">Edited Rubrics</div>
                  </div>
                  <div className="summary-stat">
                    <div className="stat-value">{formatPercentage(edit.edit_rate)}</div>
                    <div className="stat-label">Edit Rate</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeSection === 'learning' && learningData && (
          <div className="analytics-section">
            <h2 className="section-title">Learning Outcomes</h2>
            
            {/* Score Distribution */}
            <div className="learning-grid">
              <div className="learning-card">
                <h3 className="card-title">Score Distribution</h3>
                <div className="score-chart">
                  {learningData.score_distributions.map((score, index) => (
                    <div key={index} className="score-item">
                      <div className="score-range">{score.score_range}</div>
                      <div className="score-bar">
                        <div 
                          className="score-fill"
                          style={{ 
                            width: `${(score.count / Math.max(...learningData.score_distributions.map(s => s.count))) * 100}%`,
                            backgroundColor: score.score_range.includes('Excellent') ? '#4caf50' :
                                           score.score_range.includes('Good') ? '#8bc34a' :
                                           score.score_range.includes('Average') ? '#ff9800' :
                                           score.score_range.includes('Below') ? '#ff5722' : '#f44336'
                          }}
                        />
                      </div>
                      <div className="score-count">{score.count}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="learning-card">
                <h3 className="card-title">Faculty Review Activity</h3>
                {learningData.faculty_adjustments.map((adj, index) => (
                  <div key={index} className="faculty-stats">
                    <div className="faculty-stat">
                      <div className="stat-icon">
                        <FontAwesomeIcon icon={faClipboardCheck} />
                      </div>
                      <div className="stat-content">
                        <div className="stat-number">{adj.total_evaluations}</div>
                        <div className="stat-text">Total Evaluations</div>
                      </div>
                    </div>
                    
                    <div className="faculty-stat">
                      <div className="stat-icon">
                        <FontAwesomeIcon icon={faEye} />
                      </div>
                      <div className="stat-content">
                        <div className="stat-number">{formatPercentage(adj.review_rate)}</div>
                        <div className="stat-text">Review Rate</div>
                      </div>
                    </div>
                    
                    <div className="faculty-stat">
                      <div className="stat-icon">
                        <FontAwesomeIcon icon={faEdit} />
                      </div>
                      <div className="stat-content">
                        <div className="stat-number">{adj.average_adjustment}</div>
                        <div className="stat-text">Avg Adjustment</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Analytics
