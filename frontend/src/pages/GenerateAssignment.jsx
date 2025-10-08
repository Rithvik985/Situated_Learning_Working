import React, { useState, useEffect } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { 
  faFileText, 
  faRocket, 
  faCogs, 
  faPlus, 
  faTimes, 
  faEdit, 
  faSave, 
  faDownload,
  faSpinner,
  faCheck,
  faTag,
  faEye,
  faEyeSlash,
  faExclamationTriangle,
  faInfoCircle,
  faCheckCircle
} from '@fortawesome/free-solid-svg-icons'
import { getApiUrl, SERVERS, ENDPOINTS } from '../config/api'

const GenerateAssignment = () => {
  // Form state
  const [courseName, setCourseName] = useState('')
  const [courseId, setCourseId] = useState('')
  const [academicYear, setAcademicYear] = useState('')
  const [semester, setSemester] = useState(1)
  const [topics, setTopics] = useState([])
  const [newTopic, setNewTopic] = useState('')
  const [selectedDomains, setSelectedDomains] = useState([])
  const [customDomain, setCustomDomain] = useState('')
  const [showCustomDomainInput, setShowCustomDomainInput] = useState(false)
  const [customInstructions, setCustomInstructions] = useState('')
  
  // UI state
  const [availableDomains, setAvailableDomains] = useState([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedAssignments, setGeneratedAssignments] = useState([])
  const [selectedAssignments, setSelectedAssignments] = useState([])
  const [editingAssignments, setEditingAssignments] = useState({})
  const [editReasons, setEditReasons] = useState({})
  const [rubric, setRubric] = useState(null)
  const [isGeneratingRubric, setIsGeneratingRubric] = useState(false)
  const [showRubric, setShowRubric] = useState(false)
  const [isEditingRubric, setIsEditingRubric] = useState(false)
  const [editingRubric, setEditingRubric] = useState(null)
  const [rubricEditReason, setRubricEditReason] = useState('')
  const [assignmentName, setAssignmentName] = useState('')
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [showRubricNameModal, setShowRubricNameModal] = useState(false)
  const [rubricName, setRubricName] = useState('')
  const [generationProgress, setGenerationProgress] = useState({ completed: 0, total: 6, message: '' })
  const [expandedAssignments, setExpandedAssignments] = useState(new Set())
  const [notifications, setNotifications] = useState([])
  const [error, setError] = useState('')
  const [samlData, setSamlData] = useState({});
  const [userData, setUserData] = useState({});
    useEffect(() => {
  const fetchSamlData = async () => {
    try {
      // IMPORTANT: use exact backend path (qpra not qbg)
      const url = `/sla/get-saml-data`;
      console.log("[SAML] Fetching SAML data from:", url);

      const response = await fetch(url, {
        method: "GET",
        credentials: "include", // include HttpOnly cookie
        headers: {
          "Accept": "application/json",
        },
      });

      if (!response.ok) {
        console.warn("[SAML] fetch returned non-ok:", response.status);
        // If unauthorized, redirect to login (start SAML flow)
        if (response.status === 401) {
          console.log("[SAML] Session missing/expired — redirecting to login");
          window.location.href = `/`;
          return;
        }
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      setUserData(data);
      // Defensive extraction
      const courseData = {};
      const apiData = data?.api_data;

      if (Array.isArray(apiData)) {
        apiData.forEach((source, srcIndex) => {
          const ds = source?.["data-source"] || source?.data_source || `source_${srcIndex}`;
          const courses = Array.isArray(source?.courses) ? source.courses : Array.isArray(source?.data) ? source.data : [];

          courses.forEach((course) => {
            if (!course || typeof course !== "object") return;

            if (ds === "taxila") {
              // Taxila: key = fullname, value = shortname
              if (course.fullname && course.shortname) {
                courseData[course.fullname] = course.shortname;
              }
            } else if (ds === "canvas") {
              // Canvas: key = name, value = course_code
              if (course.name && course.course_code) {
                courseData[course.name] = course.course_code;
              }
            } else {
              // generic fallback — try common fields
              const title = course.fullname || course.name || course.title;
              const code = course.shortname || course.course_code || course.code || course.id;
              if (title && code) courseData[title] = code;
            }
          });
        });
      } else {
        console.warn("[SAML] api_data missing or not an array:", apiData);
      }

      setSamlData(courseData);
      setError(null);
    } catch (err) {
      console.error("Error fetching SAML data:", err);
      setError(err.message || "Unknown error");
      setSamlData({}); // ensure consistent state shape
    }
  };

  fetchSamlData();
}, []);

  // Generate academic years from 2009-10 to 2025-26
  const generateAcademicYears = () => {
    const years = []
    for (let year = 2009; year <= 2025; year++) {
      const nextYear = year + 1
      years.push(`${year}-${nextYear.toString().slice(-2)}`)
    }
    return years
  }

  const academicYears = generateAcademicYears()

  // Load domains on component mount
  useEffect(() => {
    fetchDomains()
  }, [])

  const fetchDomains = async () => {
    try {
      const response = await fetch(getApiUrl(SERVERS.GENERATION, ENDPOINTS.GET_DOMAINS))
      const data = await response.json()
      setAvailableDomains(data.domains || [])
    } catch (err) {
      console.error('Error fetching domains:', err)
      // Fallback domains
      setAvailableDomains([
        'Semiconductor Industry',
        'Electronics Manufacturing',
        'Research & Development',
        'Software Development',
        'Internet of Things (IoT)',
        'Manufacturing',
        'Healthcare Robotics'
      ])
    }
  }

  const addTopic = () => {
    if (newTopic.trim() && topics.length < 4 && !topics.includes(newTopic.trim())) {
      setTopics([...topics, newTopic.trim()])
      setNewTopic('')
    }
  }

  const removeTopic = (topicToRemove) => {
    setTopics(topics.filter(topic => topic !== topicToRemove))
  }

  const toggleDomain = (domain) => {
    setSelectedDomains(prev => 
      prev.includes(domain) 
        ? prev.filter(d => d !== domain)
        : [...prev, domain]
    )
  }

  const addCustomDomain = () => {
    if (customDomain.trim() && !selectedDomains.includes(customDomain.trim())) {
      setSelectedDomains(prev => [...prev, customDomain.trim()])
      setCustomDomain('')
      setShowCustomDomainInput(false)
    }
  }

  const removeDomain = (domainToRemove) => {
    setSelectedDomains(prev => prev.filter(domain => domain !== domainToRemove))
  }

  const toggleAssignmentExpansion = (assignmentId) => {
    setExpandedAssignments(prev => {
      const newSet = new Set(prev)
      if (newSet.has(assignmentId)) {
        newSet.delete(assignmentId)
      } else {
        newSet.add(assignmentId)
      }
      return newSet
    })
  }

  const getPreviewText = (text, maxLines = 5) => {
    const lines = text.split('\n')
    if (lines.length <= maxLines) return text
    return lines.slice(0, maxLines).join('\n') + '\n...'
  }

  const getTextStats = (text) => {
    const lines = text.split('\n')
    const words = text.split(/\s+/).filter(word => word.length > 0).length
    return { lines: lines.length, words }
  }

  const showNotification = (message, type = 'info') => {
    const id = Date.now()
    setNotifications(prev => [...prev, { id, message, type }])
    
    // Auto remove after 5 seconds
    setTimeout(() => {
      setNotifications(prev => prev.filter(notif => notif.id !== id))
    }, 5000)
  }

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(notif => notif.id !== id))
  }

  const startEditingRubric = () => {
    setEditingRubric({ ...rubric })
    setRubricEditReason('')
    setIsEditingRubric(true)
  }

  const cancelEditingRubric = () => {
    setEditingRubric(null)
    setRubricEditReason('')
    setIsEditingRubric(false)
  }

  const saveEditedRubric = async () => {
    if (!rubric.rubric_id) {
      showNotification('Rubric ID not found. Please regenerate the rubric.', 'error')
      return
    }

    // Check if only name or doc_type changed (no structural changes to rubrics)
    const nameOnlyChange = (
      editingRubric.rubric_name !== rubric.rubric_name ||
      editingRubric.doc_type !== rubric.doc_type
    ) && JSON.stringify(editingRubric.rubrics) === JSON.stringify(rubric.rubrics)

    // If not name-only change, require reason
    if (!nameOnlyChange && !rubricEditReason.trim()) {
      showNotification('Please provide a reason for the rubric content changes.', 'error')
      return
    }

    try {
      console.log('Saving rubric with ID:', rubric.rubric_id)
      const response = await fetch(getApiUrl(SERVERS.GENERATION, ENDPOINTS.RUBRIC_EDIT) + `/${rubric.rubric_id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          criteria: {
            rubric_name: editingRubric.rubric_name,
            doc_type: editingRubric.doc_type,
            rubrics: editingRubric.rubrics
          },
          reason_for_edit: rubricEditReason || (nameOnlyChange ? 'Name/type update only' : ''),
          name_only_change: nameOnlyChange
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to update rubric')
      }

      const result = await response.json()
      setRubric({ 
        ...editingRubric, 
        is_edited: nameOnlyChange ? false : result.is_edited, // Don't mark as edited for name-only changes
        rubric_id: rubric.rubric_id
      })
      setEditingRubric(null)
      setRubricEditReason('')
      setIsEditingRubric(false)
      
      showNotification('Rubric updated successfully!', 'success')
    } catch (err) {
      showNotification(err.message, 'error')
    }
  }

  const downloadRubric = async () => {
    if (!rubric) {
      showNotification('No rubric available to download.', 'error')
      return
    }

    if (!rubric.rubric_id) {
      showNotification('Rubric ID not found. Please regenerate the rubric.', 'error')
      return
    }

    try {
      console.log('Downloading rubric with ID:', rubric.rubric_id)
      const response = await fetch(getApiUrl(SERVERS.GENERATION, ENDPOINTS.RUBRIC_DOWNLOAD) + `/${rubric.rubric_id}/download`)
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to download rubric')
      }
      
      // Create blob and download
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${(rubric.rubric_name || 'Rubric').replace(/[^a-zA-Z0-9\s-_]/g, '')}_Rubric.docx`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      showNotification('Rubric downloaded successfully!', 'success')
    } catch (err) {
      showNotification(err.message, 'error')
    }
  }

  const handleGenerateAssignments = async () => {
    if (!courseName.trim() || !courseId.trim() || !academicYear.trim() || topics.length === 0 || selectedDomains.length === 0) {
      showNotification('Please fill in course name, course ID, academic year, at least one topic, and at least one domain.', 'error')
      return
    }

    setIsGenerating(true)
    
    // Clear all previous state
    setGeneratedAssignments([])
    setSelectedAssignments([])
    setRubric(null)
    setShowRubric(false)
    setEditingAssignments({})
    setEditReasons({})
    setExpandedAssignments(new Set())
    setEditingRubric(null)
    setRubricEditReason('')
    setIsEditingRubric(false)
    setGenerationProgress({ completed: 0, total: 6, message: '' })
    setAssignmentName('')
    setShowSaveModal(false)
    
    // Show notification that previous state is cleared
    showNotification('Clearing previous assignments and starting fresh generation...', 'info')

    try {
      const response = await fetch(getApiUrl(SERVERS.GENERATION, ENDPOINTS.GENERATE_PROGRESSIVE), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          course_name: courseName,
          course_id: courseId || null,
          academic_year: academicYear,
          semester: semester,
          topics,
          domains: selectedDomains,
          custom_instructions: customInstructions || null
        })
      })

      if (!response.ok) {
        throw new Error('Failed to start generation')
      }

      // Handle Server-Sent Events
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              if (data.type === 'progress') {
                // Update progress
                setGenerationProgress({ completed: data.completed, total: data.total, message: data.message })
                console.log(`Progress: ${data.completed}/${data.total} - ${data.message}`)
              } else if (data.type === 'assignment') {
                // Add new assignment to the list
                const newAssignment = { ...data.assignment, isSelected: false, isEditing: false }
                setGeneratedAssignments(prev => [...prev, newAssignment])
                console.log(`Generated assignment: ${data.assignment.title}`)
              } else if (data.type === 'complete') {
                showNotification(`Generated ${data.completed} assignments successfully!`, 'success')
              } else if (data.type === 'error') {
                showNotification(data.message, 'error')
                break
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e)
            }
          }
        }
      }
    } catch (err) {
      showNotification(err.message, 'error')
    } finally {
      setIsGenerating(false)
    }
  }

  const toggleAssignmentSelection = (assignmentId) => {
    setGeneratedAssignments(prev => 
      prev.map(assignment => 
        assignment.id === assignmentId 
          ? { ...assignment, isSelected: !assignment.isSelected }
          : { ...assignment, isSelected: false } // Deselect all others
      )
    )
    
    setSelectedAssignments(prev => 
      prev.includes(assignmentId)
        ? [] // If deselecting, clear selection
        : [assignmentId] // If selecting, only select this one
    )
  }

  const startEditingAssignment = (assignment) => {
    setEditingAssignments(prev => ({
      ...prev,
      [assignment.id]: { ...assignment }
    }))
    setEditReasons(prev => ({
      ...prev,
      [assignment.id]: ''
    }))
    setGeneratedAssignments(prev => 
      prev.map(a => 
        a.id === assignment.id 
          ? { ...a, isEditing: true }
          : a
      )
    )
  }

  const cancelEditingAssignment = (assignmentId) => {
    setGeneratedAssignments(prev => 
      prev.map(a => 
        a.id === assignmentId 
          ? { ...a, isEditing: false }
          : a
      )
    )
    setEditingAssignments(prev => {
      const newState = { ...prev }
      delete newState[assignmentId]
      return newState
    })
    setEditReasons(prev => {
      const newState = { ...prev }
      delete newState[assignmentId]
      return newState
    })
  }

  const saveEditedAssignment = async (assignmentId) => {
    const editReason = editReasons[assignmentId]
    const editingAssignment = editingAssignments[assignmentId]
    
    if (!editReason?.trim()) {
      showNotification('Please provide a reason for the changes.', 'error')
      return
    }

    try {
      const response = await fetch(getApiUrl(SERVERS.GENERATION, ENDPOINTS.EDIT_ASSIGNMENT) + `/${assignmentId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: editingAssignment.title,
          description: editingAssignment.description,
          reason_for_change: editReason
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to save changes')
      }

      const result = await response.json()
      
      setGeneratedAssignments(prev => 
        prev.map(a => 
          a.id === assignmentId 
            ? { 
                ...a, 
                ...editingAssignment,
                isEditing: false,
                tags: result.tags,
                version: result.version
              }
            : a
        )
      )
      
      setEditingAssignments(prev => {
        const newState = { ...prev }
        delete newState[assignmentId]
        return newState
      })
      setEditReasons(prev => {
        const newState = { ...prev }
        delete newState[assignmentId]
        return newState
      })
      
      showNotification('Assignment updated successfully!', 'success')
    } catch (err) {
      showNotification(err.message, 'error')
    }
  }

  const generateRubric = async () => {
    if (selectedAssignments.length === 0) {
      showNotification('Please select an assignment to generate a rubric.', 'error')
      return
    }

    // Get the selected assignment for auto-naming
    const selectedAssignment = generatedAssignments.find(a => a.id === selectedAssignments[0])
    const autoRubricName = selectedAssignment ? `${selectedAssignment.title}_Rubric` : 'Assignment_Rubric'
    
    setRubricName(autoRubricName)
    setShowRubricNameModal(true)
  }

  const confirmGenerateRubric = async () => {
    if (!rubricName.trim()) {
      showNotification('Please provide a name for the rubric.', 'error')
      return
    }

    setShowRubricNameModal(false)
    setIsGeneratingRubric(true)

    try {
      const response = await fetch(getApiUrl(SERVERS.GENERATION, ENDPOINTS.RUBRIC_GENERATE), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          assignment_ids: selectedAssignments,
          rubric_name: rubricName.trim()
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to generate rubric')
      }

      const result = await response.json()
      setRubric({
        ...result.rubric,
        rubric_id: result.rubric_id,
        is_edited: false
      })
      setShowRubric(true)
      showNotification('Rubric generated successfully!', 'success')
    } catch (err) {
      showNotification(err.message, 'error')
    } finally {
      setIsGeneratingRubric(false)
    }
  }

  const saveAssignment = async () => {
    if (!assignmentName.trim()) {
      showNotification('Please provide a name for the assignment.', 'error')
      return
    }

    try {
      const response = await fetch(getApiUrl(SERVERS.GENERATION, ENDPOINTS.SAVE_ASSIGNMENT), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          assignment_name: assignmentName,
          selected_assignment_ids: selectedAssignments,
          rubric_id: rubric?.rubric_id || null
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to save assignment')
      }

      const result = await response.json()
      showNotification(result.message, 'success')
      setShowSaveModal(false)
      setAssignmentName('')
    } catch (err) {
      showNotification(err.message, 'error')
    }
  }

  const downloadSingleAssignment = async (assignmentId, title) => {
    try {
      const response = await fetch(getApiUrl(SERVERS.GENERATION, ENDPOINTS.DOWNLOAD_ASSIGNMENT) + `/${assignmentId}/download`)
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to download assignment')
      }
      
      // Create blob and download
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${title.replace(/[^a-zA-Z0-9\s-_]/g, '')}_Assignment.docx`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      showNotification('Assignment downloaded successfully!', 'success')
    } catch (err) {
      showNotification(err.message, 'error')
    }
  }

  const downloadSelectedAssignments = async () => {
    if (selectedAssignments.length === 0) {
      showNotification('Please select at least one assignment to download.', 'error')
      return
    }

    try {
      const response = await fetch(getApiUrl(SERVERS.GENERATION, ENDPOINTS.DOWNLOAD_MULTIPLE), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          assignment_ids: selectedAssignments,
          assignment_name: assignmentName || 'Generated Assignments'
        })
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to download assignments')
      }
      
      // Create blob and download
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${(assignmentName || 'Generated_Assignments').replace(/[^a-zA-Z0-9\s-_]/g, '')}_Package.docx`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      showNotification(`Downloaded ${selectedAssignments.length} assignment(s) successfully!`, 'success')
    } catch (err) {
      showNotification(err.message, 'error')
    }
  }

  const canGenerate = courseName.trim() && courseId.trim() && academicYear.trim() && topics.length > 0 && selectedDomains.length > 0

  return (
    <div className="container" style={{ padding: '2rem 0', minHeight: '100vh' }}>
      {/* Header */}

<div className="text-center" style={{ marginBottom: '2rem' }}>
  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem'}}>
    <div style={{ fontSize: '3rem', color: 'var(--primary)' }}>
      <FontAwesomeIcon icon={faFileText} />
    </div>
    <h1 style={{ fontSize: '2.5rem', margin: 0 }}>Generate Assignment</h1>
  </div>

  <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', maxWidth: '600px', margin: '0 auto' }}>
    Create situational, industry-relevant assignments using AI-powered generation across different difficulty levels.
  </p>
</div>

  

      {/* Notifications */}
      <div style={{
        position: 'fixed',
        top: '20px',
        right: '20px',
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem'
      }}>
        {notifications.map(notification => (
          <div
            key={notification.id}
            style={{
              background: notification.type === 'error' ? '#dc3545' : 
                         notification.type === 'success' ? '#28a745' : '#17a2b8',
              color: 'white',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              minWidth: '300px',
              animation: 'slideInRight 0.3s ease-out'
            }}
          >
            <FontAwesomeIcon 
              icon={notification.type === 'error' ? faExclamationTriangle : 
                    notification.type === 'success' ? faCheckCircle : faInfoCircle} 
            />
            <span style={{ flex: 1 }}>{notification.message}</span>
            <button
              onClick={() => removeNotification(notification.id)}
              style={{
                background: 'none',
                border: 'none',
                color: 'white',
                cursor: 'pointer',
                padding: '0.25rem',
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
              onMouseOver={(e) => e.target.style.backgroundColor = 'rgba(255,255,255,0.2)'}
              onMouseOut={(e) => e.target.style.backgroundColor = 'transparent'}
            >
              <FontAwesomeIcon icon={faTimes} size="sm" />
            </button>
          </div>
        ))}
      </div>


      {/* Generation Form */}
      <div className="card" style={{ marginBottom: '2rem' }}>
          <h3 style={{ marginBottom: '1.5rem', color: 'var(--primary)' }}>
            <FontAwesomeIcon icon={faCogs} style={{ marginRight: '0.5rem' }} />
          Assignment Generation
        </h3>

        <div className="form-grid" style={{ display: 'grid', gap: '1.5rem', gridTemplateColumns: 'repeat(2, 1fr)' }}>
          {/* Course Information */}
      <div>
      <label className="form-label" htmlFor="course-select">
        Course Name *
      </label>

<select
  id="course-select"
  className="form-input"
  value={courseName}
  onChange={(e) => {
    const title = e.target.value;
    setCourseName(title);
    setCourseId(samlData[title] ?? "");
  }}
  style={{ fontSize: "1rem" }}
>
  <option value="" disabled>
    Select a Course
  </option>

  {Object.entries(samlData).map(([title, code]) => (
    <option key={code ?? title} value={title}> {/* <-- value is title */}
      {title}
    </option>
  ))}
</select>
</div>
<div>
<label className="form-label"> Course ID * <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 'normal', marginLeft: '0.5rem' }}> (e.g., CS101, EE201) </span> </label>

{/* Course ID (read-only because it's derived from samlData) */}
<input
  type="text"
  className="form-input"
  value={courseId}
  readOnly
  placeholder="Course ID (auto-filled)"
  style={{ fontSize: "1rem" }}
/>
</div>

          <div>
            <label className="form-label">
              Academic Year *
              <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 'normal', marginLeft: '0.5rem' }}>
                (e.g., 2023-24, 2024-25)
              </span>
            </label>
            <select
              className="form-input"
              value={academicYear}
              onChange={(e) => setAcademicYear(e.target.value)}
              style={{ fontSize: '1rem' }}
            >
              <option value="">Select Academic Year</option>
              {academicYears.map(year => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="form-label">
              Semester *
              <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 'normal', marginLeft: '0.5rem' }}>
                (1 or 2)
              </span>
            </label>
            <select
              className="form-input"
              value={semester}
              onChange={(e) => setSemester(parseInt(e.target.value))}
              style={{ fontSize: '1rem' }}
            >
              <option value={1}>Semester 1</option>
              <option value={2}>Semester 2</option>
            </select>
          </div>
        </div>

        {/* Topics */}
        <div style={{ marginTop: '1.5rem' }}>
          <label className="form-label">
            Topics * 
            <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 'normal', marginLeft: '0.5rem' }}>
              (Add up to 4 topics)
            </span>
          </label>
          
          {/* Selected Topics Display */}
          {topics.length > 0 && (
            <div style={{ 
              display: 'flex', 
              gap: '0.5rem', 
              marginBottom: '1rem', 
              flexWrap: 'wrap',
              padding: '0.75rem',
              backgroundColor: 'var(--surface)',
              borderRadius: '8px',
              border: '1px solid var(--border-color)'
            }}>
              {topics.map((topic, index) => (
                <span key={index} className="tag" style={{ 
                  backgroundColor: 'var(--primary)', 
                  color: 'var(--text-on-primary)',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '20px',
                  fontSize: '0.9rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  {topic}
                  <button 
                    onClick={() => removeTopic(topic)} 
                    style={{ 
                      background: 'none', 
                      border: 'none', 
                      color: 'inherit',
                      cursor: 'pointer',
                      padding: '0',
                      display: 'flex',
                      alignItems: 'center'
                    }}
                  >
                    <FontAwesomeIcon icon={faTimes} size="sm" />
                  </button>
                </span>
              ))}
            </div>
          )}
          
          {/* Add Topic Input */}
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
            <div style={{ flex: 1 }}>
              <input
                type="text"
                className="form-input"
                value={newTopic}
                onChange={(e) => setNewTopic(e.target.value)}
                placeholder={topics.length >= 4 ? "Maximum 4 topics reached" : "Enter topic name"}
                onKeyPress={(e) => e.key === 'Enter' && addTopic()}
                disabled={topics.length >= 4}
                style={{ 
                  opacity: topics.length >= 4 ? 0.6 : 1,
                  cursor: topics.length >= 4 ? 'not-allowed' : 'text'
                }}
              />
              {topics.length >= 4 ? (
                <div style={{ 
                  fontSize: '0.8rem', 
                  color: 'var(--text-muted)', 
                  marginTop: '0.25rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem'
                }}>
                  <FontAwesomeIcon icon={faTimes} size="sm" />
                  Maximum topics limit reached
                </div>
              ) : (
                <div style={{ 
                  fontSize: '0.8rem', 
                  color: 'var(--text-muted)', 
                  marginTop: '0.25rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem'
                }}>
                  <FontAwesomeIcon icon={faPlus} size="sm" />
                  Press Enter or click Add to include this topic
                </div>
              )}
            </div>
            <button 
              onClick={addTopic} 
              className="btn btn-secondary"
              disabled={topics.length >= 4 || !newTopic.trim()}
              style={{ 
                minWidth: '44px',
                height: '44px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <FontAwesomeIcon icon={faPlus} />
            </button>
          </div>
        </div>

        {/* Domains */}
        <div style={{ marginTop: '1.5rem' }}>
          <label className="form-label">
            Domains * 
            <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 'normal', marginLeft: '0.5rem' }}>
              (Select from list or add custom)
            </span>
          </label>
          
          {/* Selected Domains Display */}
          {selectedDomains.length > 0 && (
            <div style={{ 
              display: 'flex', 
              gap: '0.5rem', 
              marginBottom: '1rem', 
              flexWrap: 'wrap',
              padding: '0.75rem',
              backgroundColor: 'var(--surface)',
              borderRadius: '8px',
              border: '1px solid var(--border-color)'
            }}>
              {selectedDomains.map((domain, index) => (
                <span key={index} className="tag" style={{ 
                  backgroundColor: 'var(--primary)', 
                  color: 'var(--text-on-primary)',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '20px',
                  fontSize: '0.9rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  {domain}
                  <button 
                    onClick={() => removeDomain(domain)} 
                    style={{ 
                      background: 'none', 
                      border: 'none', 
                      color: 'inherit',
                      cursor: 'pointer',
                      padding: '0',
                      display: 'flex',
                      alignItems: 'center'
                    }}
                  >
                    <FontAwesomeIcon icon={faTimes} size="sm" />
                  </button>
                </span>
              ))}
            </div>
          )}
          
          {/* Domain Selection Grid */}
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', 
            gap: '0.75rem',
            padding: '1rem',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            backgroundColor: 'var(--bg-lighter)',
            marginBottom: '1rem'
          }}>
            {availableDomains.map((domain) => (
              <label key={domain} style={{ 
                display: 'flex', 
                alignItems: 'center', 
                cursor: 'pointer',
                padding: '0.5rem',
                borderRadius: '6px',
                transition: 'background-color 0.2s ease',
                backgroundColor: selectedDomains.includes(domain) ? 'var(--primary)' : 'transparent',
                color: selectedDomains.includes(domain) ? 'var(--text-on-primary)' : 'var(--text-primary)'
              }}>
                <input
                  type="checkbox"
                  checked={selectedDomains.includes(domain)}
                  onChange={() => toggleDomain(domain)}
                  style={{ 
                    marginRight: '0.75rem',
                    transform: 'scale(1.2)',
                    accentColor: 'var(--primary)'
                  }}
                />
                <span style={{ fontSize: '0.9rem', fontWeight: '500' }}>{domain}</span>
              </label>
            ))}
          </div>
          
          {/* Custom Domain Input */}
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
            <div style={{ flex: 1 }}>
              <input
                type="text"
                className="form-input"
                value={customDomain}
                onChange={(e) => setCustomDomain(e.target.value)}
                placeholder="Enter custom domain name"
                onKeyPress={(e) => e.key === 'Enter' && addCustomDomain()}
                onFocus={() => setShowCustomDomainInput(true)}
                style={{ 
                  backgroundColor: showCustomDomainInput ? 'var(--bg-lighter)' : 'var(--bg-light)',
                  border: showCustomDomainInput ? '2px solid var(--primary)' : '1px solid var(--border-color)'
                }}
              />
              {showCustomDomainInput && (
                <div style={{ 
                  fontSize: '0.8rem', 
                  color: 'var(--text-muted)', 
                  marginTop: '0.25rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem'
                }}>
                  <FontAwesomeIcon icon={faPlus} size="sm" />
                  Press Enter or click Add to include this domain
                </div>
              )}
            </div>
            <button 
              onClick={addCustomDomain} 
              className="btn btn-secondary"
              disabled={!customDomain.trim() || selectedDomains.includes(customDomain.trim())}
              style={{ 
                minWidth: '44px',
                height: '44px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <FontAwesomeIcon icon={faPlus} />
            </button>
          </div>
        </div>

        {/* Custom Instructions */}
        <div style={{ marginTop: '1.5rem' }}>
          <label className="form-label">
            Custom Instructions 
            <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 'normal', marginLeft: '0.5rem' }}>
              (Optional)
            </span>
          </label>
          <textarea
            className="form-textarea"
            value={customInstructions}
            onChange={(e) => setCustomInstructions(e.target.value)}
            placeholder="Enter any specific requirements, constraints, or additional instructions for the assignment generation..."
            rows="4"
            style={{
              resize: 'vertical',
              minHeight: '100px',
              fontFamily: 'inherit',
              lineHeight: '1.5'
            }}
          />
          <div style={{ 
            fontSize: '0.8rem', 
            color: 'var(--text-muted)', 
            marginTop: '0.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.25rem'
          }}>
            <FontAwesomeIcon icon={faCogs} size="sm" />
            These instructions will be used to customize assignment generation
          </div>
        </div>

        {/* Generate Button */}
        <div style={{ textAlign: 'center', marginTop: '2rem' }}>
          <button 
            onClick={handleGenerateAssignments}
            className="btn btn-primary"
            disabled={!canGenerate || isGenerating}
            style={{ minWidth: '200px', padding: '0.75rem 1.5rem' }}
          >
            {isGenerating ? (
              <>
                <FontAwesomeIcon icon={faSpinner} spin style={{ marginRight: '0.5rem' }} />
                Generating...
              </>
            ) : (
              <>
                <FontAwesomeIcon icon={faRocket} style={{ marginRight: '0.5rem' }} />
                Generate Assignments
              </>
            )}
          </button>
          
          {/* Progress Indicator */}
          {isGenerating && (
            <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: 'var(--surface)', borderRadius: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '0.5rem' }}>
                <FontAwesomeIcon icon={faSpinner} spin style={{ marginRight: '0.5rem', color: 'var(--primary)' }} />
                <span style={{ color: 'var(--text-primary)' }}>{generationProgress.message}</span>
              </div>
              <div style={{ width: '100%', backgroundColor: 'var(--bg-dark)', borderRadius: '4px', height: '8px', overflow: 'hidden' }}>
                <div 
                  style={{ 
                    width: `${(generationProgress.completed / generationProgress.total) * 100}%`, 
                    height: '100%', 
                    backgroundColor: 'var(--primary)', 
                    transition: 'width 0.3s ease',
                    borderRadius: '4px'
                  }}
                />
              </div>
              <div style={{ textAlign: 'center', marginTop: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                {generationProgress.completed} of {generationProgress.total} assignments generated
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Generated Assignments */}
      {generatedAssignments.length > 0 && (
        <div className="card" style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h3 style={{ margin: 0 }}>
              Generated Assignments ({generatedAssignments.length})
          </h3>
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
              <span style={{ color: 'var(--text-secondary)' }}>
                {selectedAssignments.length > 0 ? '1 assignment selected' : 'No assignment selected'}
              </span>
              <button 
                onClick={generateRubric}
                className="btn btn-secondary"
                disabled={selectedAssignments.length === 0 || isGeneratingRubric}
              >
                {isGeneratingRubric ? (
                  <>
                    <FontAwesomeIcon icon={faSpinner} spin style={{ marginRight: '0.5rem' }} />
                    Generating...
                  </>
                ) : (
                  <>
                    <FontAwesomeIcon icon={faFileText} style={{ marginRight: '0.5rem' }} />
                    Generate Rubric
                  </>
                )}
              </button>
              {selectedAssignments.length > 0 && (
                <button 
                  onClick={() => setShowSaveModal(true)}
                  className="btn btn-primary"
                >
                  <FontAwesomeIcon icon={faSave} style={{ marginRight: '0.5rem' }} />
                  Save Assignment
                </button>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {generatedAssignments.map((assignment) => (
              <div 
                key={assignment.id} 
                className="card"
                style={{ 
                  border: assignment.isSelected ? '2px solid var(--primary)' : '1px solid var(--border-color)',
                  backgroundColor: assignment.isSelected ? 'var(--surface)' : 'var(--bg-lighter)',
                  color: 'var(--text-primary)',
                  transition: 'all 0.3s ease',
                  display: 'flex',
                  flexDirection: 'column'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <input
                      type="checkbox"
                      checked={assignment.isSelected}
                      onChange={() => toggleAssignmentSelection(assignment.id)}
                      style={{ transform: 'scale(1.2)' }}
                    />
                    <h4 style={{ margin: 0, color: 'var(--primary)' }}>
                      {assignment.isEditing ? (
                        <input
                          type="text"
                          value={editingAssignments[assignment.id]?.title ?? ''}
                          onChange={(e) => setEditingAssignments(prev => ({
                            ...prev,
                            [assignment.id]: { ...prev[assignment.id], title: e.target.value }
                          }))}
                          className="form-input"
                          style={{ fontSize: '1.1rem', fontWeight: 'bold' }}
                        />
                      ) : (
                        assignment.title
                      )}
                    </h4>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <span className={`badge badge-${assignment.difficulty_level?.toLowerCase()}`}>
                      {assignment.difficulty_level}
                    </span>
                    {assignment.tags?.map((tag, index) => (
                      <span key={index} className="tag">
                        <FontAwesomeIcon icon={faTag} style={{ marginRight: '0.25rem' }} />
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Content Area - Flexible */}
                <div style={{ flex: 1, marginBottom: '1rem' }}>
                  {assignment.isEditing ? (
                    <div>
                      <textarea
                        value={editingAssignments[assignment.id]?.description ?? ''}
                        onChange={(e) => setEditingAssignments(prev => ({
                          ...prev,
                          [assignment.id]: { ...prev[assignment.id], description: e.target.value }
                        }))}
                        className="form-textarea"
                        rows="6"
                        style={{ marginBottom: '1rem' }}
                      />
                      <div>
                        <label className="form-label">Reason for Changes *</label>
                        <textarea
                          value={editReasons[assignment.id] || ''}
                          onChange={(e) => setEditReasons(prev => ({
                            ...prev,
                            [assignment.id]: e.target.value
                          }))}
                          className="form-textarea"
                          placeholder="Please explain why you made these changes..."
                          rows="2"
                        />
                      </div>
                    </div>
                  ) : (
                    <div>
                      <div style={{ 
                        color: 'var(--text-secondary)', 
                        lineHeight: '1.6', 
                        whiteSpace: 'pre-wrap',
                        position: 'relative',
                        transition: 'all 0.3s ease',
                        maxHeight: !expandedAssignments.has(assignment.id) && assignment.description.split('\n').length > 5 
                          ? '200px' 
                          : 'none',
                        overflow: 'hidden'
                      }}>
                        {expandedAssignments.has(assignment.id) 
                          ? assignment.description 
                          : (
                            <div style={{ position: 'relative' }}>
                              {getPreviewText(assignment.description)}
                              {assignment.description.split('\n').length > 5 && (
                                <div style={{
                                  position: 'absolute',
                                  bottom: 0,
                                  left: 0,
                                  right: 0,
                                  height: '2rem',
                                  background: 'linear-gradient(transparent, var(--bg-lighter))',
                                  pointerEvents: 'none'
                                }} />
                              )}
                            </div>
                          )
                        }
                      </div>
                      
                      {/* Show expand/collapse button if text is long enough */}
                      {assignment.description.split('\n').length > 5 && (
                        <div style={{ 
                          marginTop: '0.75rem',
                          textAlign: 'center'
                        }}>
                          <button
                            onClick={() => toggleAssignmentExpansion(assignment.id)}
                            style={{
                              background: 'none',
                              border: '1px solid var(--primary)',
                              color: 'var(--primary)',
                              padding: '0.5rem 1rem',
                              borderRadius: '20px',
                              cursor: 'pointer',
                              fontSize: '0.9rem',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.5rem',
                              margin: '0 auto',
                              transition: 'all 0.2s ease'
                            }}
                            onMouseOver={(e) => {
                              e.target.style.backgroundColor = 'var(--primary)'
                              e.target.style.color = 'var(--text-on-primary)'
                            }}
                            onMouseOut={(e) => {
                              e.target.style.backgroundColor = 'transparent'
                              e.target.style.color = 'var(--primary)'
                            }}
                          >
                            {expandedAssignments.has(assignment.id) ? (
                              <>
                                <FontAwesomeIcon icon={faEyeSlash} size="sm" />
                                Show Less
                              </>
                            ) : (
                              <>
                                <FontAwesomeIcon icon={faEye} size="sm" />
                                Show More
                              </>
                            )}
                          </button>
                          
                          {/* Text stats */}
                          <div style={{ 
                            marginTop: '0.5rem',
                            fontSize: '0.8rem',
                            color: 'var(--text-muted)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '1rem'
                          }}>
                            <span>
                              {getTextStats(assignment.description).lines} lines
                            </span>
                            <span>•</span>
                            <span>
                              {getTextStats(assignment.description).words} words
                            </span>
                            {!expandedAssignments.has(assignment.id) && (
                              <>
                                <span>•</span>
                                <span style={{ color: 'var(--primary)' }}>
                                  +{assignment.description.split('\n').length - 5} more lines
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Action Buttons - Always at Bottom */}
                <div style={{ 
                  display: 'flex', 
                  gap: '0.5rem', 
                  marginTop: 'auto',
                  paddingTop: '1rem',
                  borderTop: '1px solid var(--border-color)'
                }}>
                  {assignment.isEditing ? (
                    <>
                      <button 
                        onClick={() => saveEditedAssignment(assignment.id)}
                        className="btn btn-success btn-sm"
                        disabled={!editReasons[assignment.id]?.trim()}
                        style={{ minWidth: '120px' }}
                      >
                        <FontAwesomeIcon icon={faSave} style={{ marginRight: '0.25rem' }} />
                        Save Changes
                      </button>
                      <button 
                        onClick={() => cancelEditingAssignment(assignment.id)}
                        className="btn btn-secondary btn-sm"
                        style={{ minWidth: '80px' }}
                      >
                        <FontAwesomeIcon icon={faTimes} style={{ marginRight: '0.25rem' }} />
                        Cancel
                      </button>
                    </>
                  ) : (
                    <>
                      <button 
                        onClick={() => startEditingAssignment(assignment)}
                        className="btn btn-outline btn-sm"
                        style={{ minWidth: '80px' }}
                      >
                        <FontAwesomeIcon icon={faEdit} style={{ marginRight: '0.25rem' }} />
                        Edit
                      </button>
                      <button 
                        onClick={() => downloadSingleAssignment(assignment.id, assignment.title)}
                        className="btn btn-secondary btn-sm"
                        style={{ minWidth: '100px' }}
                      >
                        <FontAwesomeIcon icon={faDownload} style={{ marginRight: '0.25rem' }} />
                        Download
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Generated Rubric */}
      {showRubric && rubric && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h3 style={{ margin: 0 }}>
              Generated Rubric
              {rubric.is_edited && (
                <span style={{ 
                  marginLeft: '0.5rem', 
                  fontSize: '0.8rem', 
                  color: 'var(--primary)',
                  fontWeight: 'normal'
                }}>
                  (Edited)
                </span>
              )}
            </h3>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {isEditingRubric ? (
                <>
                  <button 
                    onClick={saveEditedRubric}
                    className="btn btn-success btn-sm"
                    disabled={(() => {
                      if (!editingRubric || !rubric) return true
                      
                      // Check if criteria/rubrics content has changed
                      const criteriaChanged = JSON.stringify(editingRubric.rubrics) !== JSON.stringify(rubric.rubrics)
                      
                      // Check if only name or doc_type changed (no structural changes to rubrics)
                      const nameOnlyChange = (
                        editingRubric.rubric_name !== rubric.rubric_name ||
                        editingRubric.doc_type !== rubric.doc_type
                      ) && !criteriaChanged
                      
                      // If criteria changed, always require reason
                      if (criteriaChanged && !rubricEditReason.trim()) {
                        return true
                      }
                      
                      // If it's a name-only change, button is enabled
                      // If it's not a name-only change, require reason
                      return !nameOnlyChange && !rubricEditReason.trim()
                    })()}
                  >
                    <FontAwesomeIcon icon={faSave} style={{ marginRight: '0.25rem' }} />
                    Save Changes
                  </button>
                  <button 
                    onClick={cancelEditingRubric}
                    className="btn btn-secondary btn-sm"
                  >
                    <FontAwesomeIcon icon={faTimes} style={{ marginRight: '0.25rem' }} />
                    Cancel
                  </button>
                </>
              ) : (
                <>
                  <button 
                    onClick={startEditingRubric}
                    className="btn btn-outline btn-sm"
                  >
                    <FontAwesomeIcon icon={faEdit} style={{ marginRight: '0.25rem' }} />
                    Edit Rubric
                  </button>
                  <button 
                    onClick={() => setShowRubric(false)}
                    className="btn btn-outline btn-sm"
                  >
                    <FontAwesomeIcon icon={faEyeSlash} style={{ marginRight: '0.25rem' }} />
                    Hide
                  </button>
                  <button 
                    onClick={downloadRubric}
                    className="btn btn-secondary btn-sm"
                  >
                    <FontAwesomeIcon icon={faDownload} style={{ marginRight: '0.25rem' }} />
                    Download Rubric
                  </button>
                </>
              )}
            </div>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            {isEditingRubric ? (
              <div>
                <label className="form-label">Rubric Name</label>
                <input
                  type="text"
                  value={editingRubric?.rubric_name || ''}
                  onChange={(e) => setEditingRubric(prev => ({ ...prev, rubric_name: e.target.value }))}
                  className="form-input"
                  style={{ marginBottom: '1rem' }}
                />
                <label className="form-label">Document Type</label>
                <input
                  type="text"
                  value={editingRubric?.doc_type || ''}
                  onChange={(e) => setEditingRubric(prev => ({ ...prev, doc_type: e.target.value }))}
                  className="form-input"
                  style={{ marginBottom: '1rem' }}
                />
              </div>
            ) : (
              <div>
                <h4 style={{ color: 'var(--primary)' }}>{rubric.rubric_name}</h4>
                <p style={{ color: 'var(--text-secondary)' }}>{rubric.doc_type}</p>
              </div>
            )}
          </div>

          {(isEditingRubric ? editingRubric : rubric).rubrics?.map((category, index) => (
            <div key={index} className="card" style={{ marginBottom: '1rem' }}>
              {isEditingRubric ? (
                <div>
                  <label className="form-label">Category Name</label>
                  <input
                    type="text"
                    value={category.category}
                    onChange={(e) => {
                      const newRubric = { ...editingRubric }
                      newRubric.rubrics[index].category = e.target.value
                      setEditingRubric(newRubric)
                    }}
                    className="form-input"
                    style={{ marginBottom: '0.75rem' }}
                  />
                  <label className="form-label">Questions</label>
                  {category.questions?.map((question, qIndex) => (
                    <input
                      key={qIndex}
                      type="text"
                      value={question}
                      onChange={(e) => {
                        const newRubric = { ...editingRubric }
                        newRubric.rubrics[index].questions[qIndex] = e.target.value
                        setEditingRubric(newRubric)
                      }}
                      className="form-input"
                      style={{ marginBottom: '0.5rem' }}
                      placeholder={`Question ${qIndex + 1}`}
                    />
                  ))}
                </div>
              ) : (
                <div>
                  <h5 style={{ color: 'var(--primary)', marginBottom: '0.75rem' }}>
                    {category.category}
                  </h5>
                  <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
                    {category.questions?.map((question, qIndex) => (
                      <li key={qIndex} style={{ marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
                        {question}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}

          {isEditingRubric && (
            <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: 'var(--bg-lighter)', borderRadius: 'var(--radius)' }}>
              {(() => {
                const nameOnlyChange = editingRubric && rubric && (
                  editingRubric.rubric_name !== rubric.rubric_name ||
                  editingRubric.doc_type !== rubric.doc_type
                ) && JSON.stringify(editingRubric.rubrics) === JSON.stringify(rubric.rubrics)
                
                return (
                  <>
                    <label className="form-label">
                      Reason for Changes {nameOnlyChange ? '(Optional for name/type changes)' : '*'}
                    </label>
                    <textarea
                      value={rubricEditReason}
                      onChange={(e) => setRubricEditReason(e.target.value)}
                      className="form-textarea"
                      placeholder={nameOnlyChange ? "Optional: Explain the name/type change..." : "Please explain why you are making these changes to the rubric..."}
                      rows="3"
                    />
                  </>
                )
              })()}
            </div>
          )}
        </div>
      )}

      {/* Rubric Name Modal */}
      {showRubricNameModal && (
        <div className="modal-overlay" onClick={() => setShowRubricNameModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Name Your Rubric</h3>
              <button onClick={() => setShowRubricNameModal(false)} className="btn btn-outline btn-sm">
                <FontAwesomeIcon icon={faTimes} />
              </button>
            </div>
            <div className="modal-body">
              <label className="form-label">Rubric Name *</label>
              <input
                type="text"
                className="form-input"
                value={rubricName}
                onChange={(e) => setRubricName(e.target.value)}
                placeholder="Enter a name for this rubric"
                autoFocus
              />
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.5rem' }}>
                This rubric will be used to evaluate the selected assignment.
              </p>
            </div>
            <div className="modal-footer">
              <button 
                onClick={confirmGenerateRubric}
                className="btn btn-primary"
                disabled={!rubricName.trim()}
              >
                <FontAwesomeIcon icon={faFileText} style={{ marginRight: '0.5rem' }} />
                Generate Rubric
              </button>
              <button 
                onClick={() => setShowRubricNameModal(false)}
                className="btn btn-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Save Assignment Modal */}
      {showSaveModal && (
        <div className="modal-overlay" onClick={() => setShowSaveModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Save Assignment</h3>
              <button onClick={() => setShowSaveModal(false)} className="btn btn-outline btn-sm">
                <FontAwesomeIcon icon={faTimes} />
              </button>
            </div>
            <div className="modal-body">
              <label className="form-label">Assignment Name *</label>
              <input
                type="text"
                className="form-input"
                value={assignmentName}
                onChange={(e) => setAssignmentName(e.target.value)}
                placeholder="Enter a name for this assignment"
                autoFocus
              />
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.5rem' }}>
                This will save the selected assignment with the provided name.
              </p>
            </div>
            <div className="modal-footer">
              <button 
                onClick={saveAssignment}
                className="btn btn-primary"
                disabled={!assignmentName.trim()}
              >
                <FontAwesomeIcon icon={faSave} style={{ marginRight: '0.5rem' }} />
                Save Assignment
              </button>
              <button 
                onClick={() => setShowSaveModal(false)}
                className="btn btn-secondary"
              >
                Cancel
          </button>
        </div>
      </div>
        </div>
      )}
    </div>
  )
}

export default GenerateAssignment
