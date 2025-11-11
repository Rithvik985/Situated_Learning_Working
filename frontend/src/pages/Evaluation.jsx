import React, { useState, useEffect } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { 
  faClipboardCheck, 
  faRobot, 
  faCogs,
  faChevronRight,
  faChevronLeft,
  faUpload,
  faFilePdf,
  faFileWord,
  faTrash,
  faSpinner,
  faCheckCircle,
  faExclamationTriangle,
  faEdit,
  faSave,
  faTimes,
  faDownload,
  faEye,
  faUsers,
  faGraduationCap,
  faFileText,
  faCloudUpload,
  faPlay,
  faCheck,
  faInfoCircle,
  faWarning
} from '@fortawesome/free-solid-svg-icons'
import { useDropzone } from 'react-dropzone'
import EvaluationSteps from '../components/EvaluationSteps'
import { getApiUrl, SERVERS, ENDPOINTS } from '../config/api'

const Evaluation = () => {
  // Step management
  const [currentStep, setCurrentStep] = useState(1)
  const [completedSteps, setCompletedSteps] = useState(new Set())
  
  // Step 1: Course Selection
  const [courses, setCourses] = useState([])
  const [selectedCourse, setSelectedCourse] = useState(null)
  const [loadingCourses, setLoadingCourses] = useState(false)
  const [courseFilters, setCourseFilters] = useState({ academic_years: [], semesters: [] })
  const [selectedAcademicYear, setSelectedAcademicYear] = useState('')
  const [selectedSemester, setSelectedSemester] = useState('')
  const [loadingFilters, setLoadingFilters] = useState(false)
  
  // Step 2: Assignment Selection  
  const [assignments, setAssignments] = useState([])
  const [selectedAssignment, setSelectedAssignment] = useState(null)
  const [loadingAssignments, setLoadingAssignments] = useState(false)
  
  // Step 3: Rubric Selection
  const [rubrics, setRubrics] = useState([])
  const [selectedRubric, setSelectedRubric] = useState(null)
  const [loadingRubrics, setLoadingRubrics] = useState(false)
  const [showRubricDetails, setShowRubricDetails] = useState(false)
  
  // Step 3: Rubric Generation/Editing disabled
  const [isGeneratingRubric, setIsGeneratingRubric] = useState(false)
  const [isEditingRubric, setIsEditingRubric] = useState(false)
  const [editingRubric, setEditingRubric] = useState(null)
  const [rubricEditReason, setRubricEditReason] = useState('')
  // const [showRubricNameModal, setShowRubricNameModal] = useState(false)
  // const [rubricName, setRubricName] = useState('')
  
  // Step 4: File Upload
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [uploadingFiles, setUploadingFiles] = useState(false)
  const [uploadProgress, setUploadProgress] = useState({})
  
  // Step 5: Processing & Evaluation
  const [evaluationResults, setEvaluationResults] = useState([])
  const [evaluating, setEvaluating] = useState(false)
  const [evaluationProgress, setEvaluationProgress] = useState({ current: 0, total: 0, message: '' })
  
  // Step 6: Review & Edit
  const [editingResults, setEditingResults] = useState({})
  const [facultyReasons, setFacultyReasons] = useState({})
  
  // General UI state
  const [notifications, setNotifications] = useState([])
  const [serviceStatus, setServiceStatus] = useState(null)

  const steps = [
    { number: 1, title: 'Course Selection', icon: faGraduationCap },
    { number: 2, title: 'Assignment Selection', icon: faFileText },
    { number: 3, title: 'Rubric Selection', icon: faClipboardCheck },
    { number: 4, title: 'Upload Submissions', icon: faCloudUpload },
    { number: 5, title: 'Process & Evaluate', icon: faRobot },
    { number: 6, title: 'Review & Edit', icon: faEdit },
    { number: 7, title: 'Export Reports', icon: faDownload }
  ]

  // Utility functions
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

  const markStepComplete = (stepNumber) => {
    setCompletedSteps(prev => new Set([...prev, stepNumber]))
  }

  const canProceedToStep = (stepNumber) => {
    return stepNumber === 1 || completedSteps.has(stepNumber - 1)
  }

  // API calls
  const fetchCourses = async () => {
    setLoadingCourses(true)
    try {
      const response = await fetch(getApiUrl(SERVERS.EVALUATION, ENDPOINTS.EVALUATION_COURSES))
      if (!response.ok) throw new Error('Failed to fetch courses')
      const data = await response.json()
      setCourses(data)
      if (data.length === 0) {
        showNotification('No courses with saved assignments found. Please create and save assignments first.', 'warning')
      }
    } catch (error) {
      showNotification(`Error fetching courses: ${error.message}`, 'error')
    } finally {
      setLoadingCourses(false)
    }
  }

  const fetchCourseFilters = async (courseTitle) => {
    setLoadingFilters(true)
    try {
      const response = await fetch(getApiUrl(SERVERS.EVALUATION, ENDPOINTS.EVALUATION_COURSE_FILTERS) + `/${encodeURIComponent(courseTitle)}/filters`)
      if (!response.ok) throw new Error('Failed to fetch course filters')
      const data = await response.json()
      setCourseFilters(data)
    } catch (error) {
      showNotification(`Error fetching course filters: ${error.message}`, 'error')
    } finally {
      setLoadingFilters(false)
    }
  }

  const fetchAssignments = async (courseTitle, academicYear = '', semester = '') => {
    setLoadingAssignments(true)
    try {
      let url = getApiUrl(SERVERS.EVALUATION, ENDPOINTS.EVALUATION_ASSIGNMENTS) + `/${encodeURIComponent(courseTitle)}/assignments`
      const params = new URLSearchParams()
      
      if (academicYear) params.append('academic_year', academicYear)
      if (semester) params.append('semester', semester)
      
      if (params.toString()) {
        url += `?${params.toString()}`
      }
      
      const response = await fetch(url)
      if (!response.ok) throw new Error('Failed to fetch assignments')
      const data = await response.json()
      setAssignments(data)
      if (data.length === 0) {
        showNotification('No saved assignments found for this course with the selected filters.', 'warning')
      }
    } catch (error) {
      showNotification(`Error fetching assignments: ${error.message}`, 'error')
    } finally {
      setLoadingAssignments(false)
    }
  }

  const fetchRubrics = async (assignmentId) => {
    setLoadingRubrics(true)
    try {
      const response = await fetch(getApiUrl(SERVERS.EVALUATION, ENDPOINTS.EVALUATION_RUBRICS) + `/${assignmentId}/rubrics`)
      if (!response.ok) throw new Error('Failed to fetch rubrics')
      const data = await response.json()
      setRubrics(data)
      // If none, backend will auto-create hardcoded rubric when fetching
    } catch (error) {
      showNotification(`Error fetching rubrics: ${error.message}`, 'error')
    } finally {
      setLoadingRubrics(false)
    }
  }

  const uploadSubmissions = async () => {
    if (uploadedFiles.length === 0) {
      showNotification('Please upload at least one submission file.', 'error')
      return
    }

    setUploadingFiles(true)
    const formData = new FormData()
    formData.append('assignment_id', selectedAssignment.id)
    
    uploadedFiles.forEach(fileObj => {
      formData.append('files', fileObj.file)
    })

    try {
      const response = await fetch(getApiUrl(SERVERS.EVALUATION, ENDPOINTS.SUBMIT_EVALUATION), {
        method: 'POST',
        body: formData
      })

      if (!response.ok) throw new Error('Failed to upload submissions')
      const data = await response.json()
      
      // Update file objects with server response
      const updatedFiles = data.map((serverFile) => ({
        id: serverFile.id,
        name: serverFile.file_name,
        file_path: serverFile.file_path,
        submission_id: serverFile.id,
        processing_status: serverFile.processing_status,
        extraction_method: serverFile.extraction_method || 'standard',
        ocr_confidence: serverFile.ocr_confidence || 1.0,
        extracted_text_preview: serverFile.extracted_text || '',
        type: serverFile.file_name.toLowerCase().endsWith('.pdf') ? 'pdf' : 'docx',
        size: 0 // Size not returned from server, but not critical for display
      }))
      
      setUploadedFiles(updatedFiles)
      markStepComplete(4)
      showNotification('Submissions uploaded and processed successfully!', 'success')
      
    } catch (error) {
      showNotification(`Upload failed: ${error.message}`, 'error')
    } finally {
      setUploadingFiles(false)
    }
  }

  const evaluateSubmissions = async () => {
    setEvaluating(true)
    setEvaluationProgress({ current: 0, total: uploadedFiles.length, message: 'Starting evaluation...' })
    
    try {
      // Extract submission IDs from uploaded files (only those that have been processed)
      const submissionIds = uploadedFiles
        .filter(file => file.id && file.processing_status === 'processed')
        .map(file => file.id)
      
      if (submissionIds.length === 0) {
        throw new Error('No processed submissions found to evaluate')
      }
      
      console.log('Evaluating submissions with IDs:', submissionIds)
      
      const response = await fetch(getApiUrl(SERVERS.EVALUATION, ENDPOINTS.EVALUATE_SUBMISSION), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          assignment_id: selectedAssignment.id,
          rubric_id: selectedRubric.id,
          submission_ids: submissionIds  // Only evaluate the specific submissions we uploaded
        })
      })

      if (!response.ok) throw new Error('Failed to evaluate submissions')
      const results = await response.json()
      
      setEvaluationResults(results)
      markStepComplete(5)
      showNotification(`Successfully evaluated ${results.length} submission(s) from current upload!`, 'success')
      
    } catch (error) {
      showNotification(`Evaluation failed: ${error.message}`, 'error')
    } finally {
      setEvaluating(false)
    }
  }

  const checkServiceStatus = async () => {
    try {
      const response = await fetch(getApiUrl(SERVERS.EVALUATION, ENDPOINTS.EVALUATION_PROGRESS))
      const status = await response.json()
      setServiceStatus(status)
    } catch (error) {
      console.error('Service status check failed:', error)
    }
  }

  // Rubric generation disabled; backend provides hardcoded rubric automatically

  const startEditingRubric = () => {
    setEditingRubric({ ...selectedRubric.criteria })
    setRubricEditReason('')
    setIsEditingRubric(true)
  }

  const cancelEditingRubric = () => {
    setEditingRubric(null)
    setRubricEditReason('')
    setIsEditingRubric(false)
  }

  const saveEditedRubric = async () => {
    if (!selectedRubric.id) {
      showNotification('Rubric ID not found. Please regenerate the rubric.', 'error')
      return
    }

    // Check if only name or doc_type changed (no structural changes to rubrics)
    const nameOnlyChange = (
      editingRubric.rubric_name !== selectedRubric.criteria.rubric_name ||
      editingRubric.doc_type !== selectedRubric.criteria.doc_type
    ) && JSON.stringify(editingRubric.rubrics) === JSON.stringify(selectedRubric.criteria.rubrics)

    // If not name-only change, require reason
    if (!nameOnlyChange && !rubricEditReason.trim()) {
      showNotification('Please provide a reason for the rubric content changes.', 'error')
      return
    }

    try {
      const response = await fetch(getApiUrl(SERVERS.EVALUATION, ENDPOINTS.EVALUATION_RUBRIC_EDIT) + `/${selectedRubric.id}/edit`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          criteria: editingRubric,
          reason_for_edit: rubricEditReason || (nameOnlyChange ? 'Name/type update only' : ''),
          name_only_change: nameOnlyChange
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to update rubric')
      }

      const result = await response.json()
      setSelectedRubric({ 
        ...selectedRubric,
        criteria: editingRubric,
        is_edited: nameOnlyChange ? false : result.is_edited
      })
      setEditingRubric(null)
      setRubricEditReason('')
      setIsEditingRubric(false)
      
      showNotification('Rubric updated successfully!', 'success')
    } catch (err) {
      showNotification(err.message, 'error')
    }
  }

  // Load courses on component mount
  useEffect(() => {
    fetchCourses()
    checkServiceStatus()
  }, [])

  // File upload handling with dropzone
  const onDrop = React.useCallback((acceptedFiles, rejectedFiles) => {
    if (rejectedFiles.length > 0) {
      showNotification('Some files were rejected. Only PDF and DOCX files are allowed.', 'error')
      return
    }

    if (uploadedFiles.length + acceptedFiles.length > 5) {
      showNotification('Maximum 5 submissions allowed.', 'error')
      return
    }

    const newFiles = acceptedFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      name: file.name,
      size: file.size,
      type: file.name.toLowerCase().endsWith('.pdf') ? 'pdf' : 'docx',
      status: 'ready',
      extraction_method: 'ready', // Set to 'ready' to show correct badge
      processing_status: 'pending'
    }))

    setUploadedFiles(prev => [...prev, ...newFiles])
    
    // Clear future steps (4, 5, 6, 7) when new files are uploaded
    setEvaluationResults([])
    setEditingResults({})
    setFacultyReasons({})
    setCompletedSteps(prev => {
      const newSet = new Set(prev)
      newSet.delete(4) // Also clear step 4 since we need to process again
      newSet.delete(5)
      newSet.delete(6)
      newSet.delete(7)
      return newSet
    })
    
    showNotification(`${newFiles.length} file(s) added. Ready to process.`, 'success')
  }, [uploadedFiles])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    maxFiles: 5,
    multiple: true
  })

  const removeFile = (fileId) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId))
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getClassificationBadge = (file) => {
    // Use extraction_method from backend response
    const method = file.extraction_method
    const confidence = file.ocr_confidence || file.confidence || 1.0
    
    // Debug logging
    console.log('File classification:', file.name, 'method:', method, 'confidence:', confidence)
    
    // If no extraction method, it means file hasn't been processed yet
    if (!method || method === 'ready') {
      return (
        <span className="badge" style={{ backgroundColor: '#6c757d', color: 'white' }}>
          Ready to Process
        </span>
      )
    }
    
    if (method === 'failed') {
      return (
        <span className="badge" style={{ backgroundColor: '#dc3545', color: 'white' }}>
          Processing Failed
        </span>
      )
    }
    
    if (method === 'ocr' || method === 'ocr_vision_llm') {
      return (
        <span className="badge" style={{ backgroundColor: '#ff9800', color: 'white' }}>
          Handwritten
        </span>
      )
    } else if (method === 'standard' || method === 'docx_standard') {
      return (
        <span className="badge" style={{ backgroundColor: '#4caf50', color: 'white' }}>
          Typed Text
        </span>
      )
    } else if (method === 'standard_fallback') {
      return (
        <span className="badge" style={{ backgroundColor: '#ff5722', color: 'white' }}>
          Low Quality ({(confidence * 100).toFixed(0)}%)
        </span>
      )
    }
    
    return (
      <span className="badge" style={{ backgroundColor: '#9e9e9e', color: 'white' }}>
        Processing...
      </span>
    )
  }

  return (
    <div className="container" style={{ padding: '2rem 0', minHeight: '100vh' }}>
      {/* Header */}
  <div className="text-center" style={{ marginBottom: '2rem' }}>
  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
    <div style={{ fontSize: '3rem', color: 'var(--primary)' }}>
      <FontAwesomeIcon icon={faClipboardCheck} />
    </div>
    <h1 style={{ fontSize: '2.5rem', margin: 0 }}>Student Submission Evaluation</h1>
  </div>

  <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', maxWidth: '600px', margin: '0 auto' }}>
    Comprehensive AI-powered evaluation with OCR processing, rubric-based scoring, and detailed feedback generation.
  </p>
</div>

      {/* Service Status Indicator */}
      {serviceStatus && (
        <div className="card" style={{ marginBottom: '2rem', padding: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <FontAwesomeIcon 
              icon={serviceStatus.overall_status === 'healthy' ? faCheckCircle : faExclamationTriangle} 
              style={{ color: serviceStatus.overall_status === 'healthy' ? '#4caf50' : '#ff9800' }}
            />
            <div>
              <strong>Service Status: </strong>
              <span style={{ color: serviceStatus.overall_status === 'healthy' ? '#4caf50' : '#ff9800' }}>
                {serviceStatus.overall_status === 'healthy' ? 'All Services Online' : 'Some Services Degraded'}
              </span>
              {serviceStatus.overall_status !== 'healthy' && (
                <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                  Check OCR and evaluation services connectivity
                </div>
              )}
            </div>
          </div>
        </div>
      )}

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
                         notification.type === 'success' ? '#28a745' : 
                         notification.type === 'warning' ? '#ff9800' : '#17a2b8',
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
                    notification.type === 'success' ? faCheckCircle : 
                    notification.type === 'warning' ? faWarning : faInfoCircle} 
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
                borderRadius: '4px'
              }}
            >
              <FontAwesomeIcon icon={faTimes} size="sm" />
            </button>
          </div>
        ))}
      </div>

      {/* Step Progress Indicator */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <h3 style={{ marginBottom: '1.5rem', color: 'var(--primary)' }}>Evaluation Progress</h3>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          {steps.map((step, index) => (
            <div 
              key={step.number}
              style={{ 
                display: 'flex', 
                flexDirection: 'column', 
                alignItems: 'center',
                opacity: canProceedToStep(step.number) ? 1 : 0.5,
                cursor: canProceedToStep(step.number) ? 'pointer' : 'not-allowed'
              }}
              onClick={() => canProceedToStep(step.number) && setCurrentStep(step.number)}
            >
              <div 
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: completedSteps.has(step.number) ? '#4caf50' : 
                            currentStep === step.number ? 'var(--primary)' : '#e0e0e0',
                  color: completedSteps.has(step.number) || currentStep === step.number ? 'white' : '#666',
                  marginBottom: '0.5rem',
                  transition: 'all 0.3s ease'
                }}
              >
                {completedSteps.has(step.number) ? (
                  <FontAwesomeIcon icon={faCheck} />
                ) : (
                  <FontAwesomeIcon icon={step.icon} size="sm" />
                )}
              </div>
              <span style={{ 
                fontSize: '0.8rem', 
                textAlign: 'center',
                color: currentStep === step.number ? 'var(--primary)' : 'var(--text-secondary)',
                fontWeight: currentStep === step.number ? 'bold' : 'normal'
              }}>
                {step.title}
              </span>
              {index < steps.length - 1 && (
                <FontAwesomeIcon 
                  icon={faChevronRight} 
                  style={{ 
                    position: 'absolute',
                    right: '-10px',
                    color: '#ccc',
                    fontSize: '0.8rem'
                  }}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Step Content */}
      {currentStep === 1 && (
        <div className="card">
          <h3 style={{ marginBottom: '1.5rem', color: 'var(--primary)' }}>
            <FontAwesomeIcon icon={faGraduationCap} style={{ marginRight: '0.5rem' }} />
            Step 1: Select Course
          </h3>
          
          {loadingCourses ? (
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              <FontAwesomeIcon icon={faSpinner} spin size="2x" style={{ color: 'var(--primary)' }} />
              <p style={{ marginTop: '1rem' }}>Loading courses...</p>
            </div>
          ) : courses.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              <FontAwesomeIcon icon={faExclamationTriangle} size="2x" style={{ color: '#ff9800', marginBottom: '1rem' }} />
              <h4>No Courses Available</h4>
              <p style={{ color: 'var(--text-secondary)' }}>
                No courses with saved assignments found. Please create and save assignments in the Generation page first.
              </p>
            </div>
          ) : (
            <div>
              <p style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>
                Select a course title, then choose academic year and semester to filter assignments.
              </p>
              
              {/* Course Selection */}
              <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', marginBottom: '2rem' }}>
                {courses.map(course => (
                  <div 
                    key={course.id}
                    className="card"
                    style={{ 
                      cursor: 'pointer',
                      border: selectedCourse?.title === course.title ? '2px solid var(--primary)' : '1px solid var(--border-color)',
                      backgroundColor: selectedCourse?.title === course.title ? 'var(--surface)' : 'var(--bg-lighter)',
                      transition: 'all 0.3s ease'
                    }}
                    onClick={() => {
                      setSelectedCourse(course)
                      setSelectedAcademicYear('')
                      setSelectedSemester('')
                      setAssignments([])
                      fetchCourseFilters(course.title)
                    }}
                  >
                    <h4 style={{ margin: '0 0 0.5rem 0', color: 'var(--primary)' }}>
                      {course.course_code}
                    </h4>
                    <p style={{ margin: '0 0 0.5rem 0', fontWeight: '500' }}>
                      {course.title}
                    </p>
                    <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                      <div style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '0.5rem',
                        color: 'var(--primary)'
                      }}>
                        <FontAwesomeIcon icon={faUsers} />
                        <span>{course.saved_assignment_count} saved assignment(s)</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Academic Year and Semester Selection */}
              {selectedCourse && (
                <div style={{ 
                  padding: '1.5rem', 
                  backgroundColor: 'var(--surface)', 
                  borderRadius: '8px', 
                  marginBottom: '2rem' 
                }}>
                  <h4 style={{ marginBottom: '1rem', color: 'var(--primary)' }}>
                    Selected Course: {selectedCourse.title}
                  </h4>
                  
                  {loadingFilters ? (
                    <div style={{ textAlign: 'center', padding: '1rem' }}>
                      <FontAwesomeIcon icon={faSpinner} spin style={{ color: 'var(--primary)' }} />
                      <span style={{ marginLeft: '0.5rem' }}>Loading filters...</span>
                    </div>
                  ) : (
                    <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
                      <div>
                        <label className="form-label">Academic Year *</label>
                        <select
                          className="form-input"
                          value={selectedAcademicYear}
                          onChange={(e) => setSelectedAcademicYear(e.target.value)}
                        >
                          <option value="">Select Academic Year</option>
                          {courseFilters.academic_years.map(year => (
                            <option key={year} value={year}>{year}</option>
                          ))}
                        </select>
                      </div>
                      
                      <div>
                        <label className="form-label">Semester *</label>
                        <select
                          className="form-input"
                          value={selectedSemester}
                          onChange={(e) => setSelectedSemester(e.target.value)}
                        >
                          <option value="">Select Semester</option>
                          {courseFilters.semesters.map(semester => (
                            <option key={semester} value={semester}>Semester {semester}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                  )}
                  
                  {selectedAcademicYear && selectedSemester && (
                    <div style={{ textAlign: 'center', marginTop: '1.5rem' }}>
                  <button 
                    className="btn btn-primary"
                        onClick={() => {
                          fetchAssignments(selectedCourse.title, selectedAcademicYear, selectedSemester)
                          markStepComplete(1)
                          setCurrentStep(2)
                        }}
                  >
                    Continue to Assignment Selection
                    <FontAwesomeIcon icon={faChevronRight} style={{ marginLeft: '0.5rem' }} />
                  </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Step 2: Assignment Selection */}
      {currentStep === 2 && selectedCourse && (
        <div className="card">
          <h3 style={{ marginBottom: '1.5rem', color: 'var(--primary)' }}>
            <FontAwesomeIcon icon={faFileText} style={{ marginRight: '0.5rem' }} />
            Step 2: Select Assignment
          </h3>
          
          <div style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: 'var(--surface)', borderRadius: '8px' }}>
            <div style={{ display: 'grid', gap: '0.5rem' }}>
              <div><strong>Course:</strong> {selectedCourse.title}</div>
              <div><strong>Academic Year:</strong> {selectedAcademicYear}</div>
              <div><strong>Semester:</strong> {selectedSemester}</div>
            </div>
          </div>
          
          {loadingAssignments ? (
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              <FontAwesomeIcon icon={faSpinner} spin size="2x" style={{ color: 'var(--primary)' }} />
              <p style={{ marginTop: '1rem' }}>Loading assignments...</p>
            </div>
          ) : assignments.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              <FontAwesomeIcon icon={faExclamationTriangle} size="2x" style={{ color: '#ff9800', marginBottom: '1rem' }} />
              <h4>No Assignments Available</h4>
              <p style={{ color: 'var(--text-secondary)' }}>
                No saved assignments found for this course. Please generate and save assignments first.
              </p>
            </div>
          ) : (
            <div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {assignments.map(assignment => (
                  <div 
                    key={assignment.id}
                    className="card"
                    style={{ 
                      cursor: 'pointer',
                      border: selectedAssignment?.id === assignment.id ? '2px solid var(--primary)' : '1px solid var(--border-color)',
                      backgroundColor: selectedAssignment?.id === assignment.id ? 'var(--surface)' : 'var(--bg-lighter)',
                      transition: 'all 0.3s ease'
                    }}
                    onClick={() => {
                      setSelectedAssignment(assignment)
                      fetchRubrics(assignment.id)
                      markStepComplete(2)
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                      <div style={{ flex: 1 }}>
                        <h4 style={{ margin: '0 0 0.5rem 0', color: 'var(--primary)' }}>
                          {assignment.assignment_name}
                        </h4>
                        <p style={{ margin: '0 0 0.5rem 0', fontWeight: '500' }}>
                          {assignment.title}
                        </p>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span className={`badge badge-${assignment.difficulty_level.toLowerCase()}`}>
                          {assignment.difficulty_level}
                        </span>
                        {assignment.has_rubric ? (
                          <span className="badge" style={{ backgroundColor: '#4caf50', color: 'white' }}>
                            <FontAwesomeIcon icon={faCheckCircle} style={{ marginRight: '0.25rem' }} />
                            Has Rubric
                          </span>
                        ) : (
                          <span className="badge" style={{ backgroundColor: '#ff9800', color: 'white' }}>
                            <FontAwesomeIcon icon={faExclamationTriangle} style={{ marginRight: '0.25rem' }} />
                            No Rubric
                          </span>
                        )}
                      </div>
                    </div>
                    
                    <p style={{ 
                      color: 'var(--text-secondary)', 
                      lineHeight: '1.5',
                      maxHeight: '100px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}>
                      {assignment.description}
                    </p>
                    
                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '1rem' }}>
                      {assignment.topics.slice(0, 3).map((topic, index) => (
                        <span key={index} className="tag" style={{ fontSize: '0.8rem' }}>
                          {topic}
                        </span>
                      ))}
                      {assignment.topics.length > 3 && (
                        <span className="tag" style={{ fontSize: '0.8rem', backgroundColor: '#e0e0e0' }}>
                          +{assignment.topics.length - 3} more
                        </span>
                      )}
                    </div>
                  </div>
                ))}
        </div>

              {selectedAssignment && (
                <div style={{ textAlign: 'center', marginTop: '2rem' }}>
                  <button 
                    className="btn btn-primary"
                    onClick={() => setCurrentStep(3)}
                  >
                    Continue to Rubric Selection
                    <FontAwesomeIcon icon={faChevronRight} style={{ marginLeft: '0.5rem' }} />
                  </button>
                </div>
              )}
            </div>
          )}
          
          <div style={{ textAlign: 'center', marginTop: '2rem' }}>
            <button 
              className="btn btn-secondary"
              onClick={() => setCurrentStep(1)}
            >
              <FontAwesomeIcon icon={faChevronLeft} style={{ marginRight: '0.5rem' }} />
              Back to Course Selection
          </button>
        </div>
      </div>
      )}

      {/* Step 3: Enhanced Rubric Management */}
      {currentStep === 3 && selectedAssignment && (
        <div className="card">
          <h3 style={{ marginBottom: '1.5rem', color: 'var(--primary)' }}>
            <FontAwesomeIcon icon={faClipboardCheck} style={{ marginRight: '0.5rem' }} />
            Step 3: Rubric Management
          </h3>
          
          <div style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: 'var(--surface)', borderRadius: '8px' }}>
            <strong>Selected Assignment:</strong> {selectedAssignment.assignment_name}
          </div>
          
          {loadingRubrics ? (
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              <FontAwesomeIcon icon={faSpinner} spin size="2x" style={{ color: 'var(--primary)' }} />
              <p style={{ marginTop: '1rem' }}>Loading rubrics...</p>
            </div>
          ) : rubrics.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              <FontAwesomeIcon icon={faSpinner} spin size="2x" style={{ color: 'var(--primary)', marginBottom: '1rem' }} />
              <h4>Preparing Rubric</h4>
              <p style={{ color: 'var(--text-secondary)' }}>
                Fetching the standard rubric for this assignment...
              </p>
            </div>
          ) : (
            <div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
                {rubrics.map(rubric => (
                  <div 
                    key={rubric.id}
                    className="card"
                    style={{ 
                      cursor: 'pointer',
                      border: selectedRubric?.id === rubric.id ? '2px solid var(--primary)' : '1px solid var(--border-color)',
                      backgroundColor: selectedRubric?.id === rubric.id ? 'var(--surface)' : 'var(--bg-lighter)',
                      transition: 'all 0.3s ease'
                    }}
                    onClick={() => {
                      setSelectedRubric(rubric)
                      setShowRubricDetails(true)
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                      <div style={{ flex: 1 }}>
                        <h4 style={{ margin: '0 0 0.5rem 0', color: 'var(--primary)' }}>
                          {rubric.rubric_name}
                        </h4>
                        <p style={{ margin: '0 0 0.5rem 0', color: 'var(--text-secondary)' }}>
                          {rubric.doc_type}
                        </p>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        {rubric.is_edited && (
                          <span className="badge" style={{ backgroundColor: '#ff9800', color: 'white' }}>
                            Edited
                          </span>
                        )}
                      </div>
                    </div>
                    
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                      <p>Categories: {rubric.criteria?.rubrics?.length || 0}</p>
                      <p>Created: {new Date(rubric.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Detailed Rubric Display (when rubric is selected or generated) */}
          {selectedRubric && showRubricDetails && (
            <div className="card" style={{ marginTop: '2rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h3 style={{ margin: 0 }}>
                  Rubric Details
                  {selectedRubric.is_edited && (
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
                          if (!editingRubric || !selectedRubric.criteria) return true
                          
                          // Check if criteria/rubrics content has changed
                          const criteriaChanged = JSON.stringify(editingRubric.rubrics) !== JSON.stringify(selectedRubric.criteria.rubrics)
                          
                          // Check if only name or doc_type changed (no structural changes to rubrics)
                          const nameOnlyChange = (
                            editingRubric.rubric_name !== selectedRubric.criteria.rubric_name ||
                            editingRubric.doc_type !== selectedRubric.criteria.doc_type
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
                    <button 
                      onClick={startEditingRubric}
                      className="btn btn-outline btn-sm"
                    >
                      <FontAwesomeIcon icon={faEdit} style={{ marginRight: '0.25rem' }} />
                      Edit Rubric
                    </button>
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
                    <h4 style={{ color: 'var(--primary)' }}>{selectedRubric.criteria?.rubric_name}</h4>
                    <p style={{ color: 'var(--text-secondary)' }}>{selectedRubric.criteria?.doc_type}</p>
                  </div>
                )}
              </div>

              {(isEditingRubric ? editingRubric : selectedRubric.criteria)?.rubrics?.map((category, index) => (
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
                    const nameOnlyChange = editingRubric && selectedRubric.criteria && (
                      editingRubric.rubric_name !== selectedRubric.criteria.rubric_name ||
                      editingRubric.doc_type !== selectedRubric.criteria.doc_type
                    ) && JSON.stringify(editingRubric.rubrics) === JSON.stringify(selectedRubric.criteria.rubrics)
                    
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

              {selectedRubric && !isEditingRubric && (
                <div style={{ textAlign: 'center', marginTop: '2rem' }}>
                  <button 
                    className="btn btn-primary"
                    onClick={() => {
                      markStepComplete(3)
                      setCurrentStep(4)
                    }}
                  >
                    Continue to Upload Submissions
                    <FontAwesomeIcon icon={faChevronRight} style={{ marginLeft: '0.5rem' }} />
                  </button>
                </div>
              )}
            </div>
          )}
          
          <div style={{ textAlign: 'center', marginTop: '2rem' }}>
            <button 
              className="btn btn-secondary"
              onClick={() => setCurrentStep(2)}
            >
              <FontAwesomeIcon icon={faChevronLeft} style={{ marginRight: '0.5rem' }} />
              Back to Assignment Selection
            </button>
          </div>
        </div>
      )}

      {/* Steps 4-7: Additional workflow steps */}
      {[4, 5, 6, 7].includes(currentStep) && (
        <EvaluationSteps
          currentStep={currentStep}
          setCurrentStep={setCurrentStep}
          selectedAssignment={selectedAssignment}
          selectedRubric={selectedRubric}
          rubrics={rubrics}
          loadingRubrics={loadingRubrics}
          uploadedFiles={uploadedFiles}
          uploadingFiles={uploadingFiles}
          evaluating={evaluating}
          evaluationResults={evaluationResults}
          setEvaluationResults={setEvaluationResults}
          editingResults={editingResults}
          facultyReasons={facultyReasons}
          markStepComplete={markStepComplete}
          completedSteps={completedSteps}
          setSelectedRubric={setSelectedRubric}
          uploadSubmissions={uploadSubmissions}
          evaluateSubmissions={evaluateSubmissions}
          setEditingResults={setEditingResults}
          setFacultyReasons={setFacultyReasons}
          showNotification={showNotification}
          formatFileSize={formatFileSize}
          getClassificationBadge={getClassificationBadge}
          removeFile={removeFile}
          getRootProps={getRootProps}
          getInputProps={getInputProps}
          isDragActive={isDragActive}
        />
      )}

      {/* Rubric generation modal removed intentionally */}
      
    </div>
  )
}

export default Evaluation
