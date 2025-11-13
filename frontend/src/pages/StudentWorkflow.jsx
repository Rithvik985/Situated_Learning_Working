import React, { useEffect, useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import ReactMarkdown from 'react-markdown'; 

import { useNavigate } from 'react-router-dom'
import Select from 'react-select'
import { faListCheck, faMagicWandSparkles, faChevronRight, faCheckCircle, faExclamationTriangle, faRotate, faSave, faChartLine, faPlus, faTimes, faTag, faHourglassHalf, faBookmark } from '@fortawesome/free-solid-svg-icons'
import { getApiUrl, SERVERS, ENDPOINTS } from '../config/api'

const StudentWorkflow = () => {
  const [options, setOptions] = useState({ domains: [], service_categories: [], departments: [] })
  const [domain, setDomain] = useState('')
  const [service, setService] = useState('')
  const [department, setDepartment] = useState('')
  const [topics, setTopics] = useState([])
  const [newTopic, setNewTopic] = useState('')
  const [handouts, setHandouts] = useState('')
  const [studentId, setStudentId] = useState('')
  const navigate = useNavigate()
  const [courseName, setCourseName] = useState('')
  const [courseId, setCourseId] = useState('')
  const [loading, setLoading] = useState(false)
  const [questions, setQuestions] = useState([])
  const [questionSet, setQuestionSet] = useState(null)
  const [selectedQuestion, setSelectedQuestion] = useState('')
  const [approvalStatus, setApprovalStatus] = useState('')
  const [statusRefreshing, setStatusRefreshing] = useState(false)
  const [notif, setNotif] = useState(null)
  const [savedAssignments, setSavedAssignments] = useState([])
  const [approvedNotSavedAssignments, setApprovedNotSavedAssignments] = useState([])
  const [samlData, setSamlData] = useState({})
  const [userData, setUserData] = useState({})

  // Fetch SAML data on component mount
  useEffect(() => {
    const fetchSamlData = async () => {
      try {
        const url = `/sla/get-saml-data`;
        console.log("[SAML] Fetching SAML data from:", url);

        const response = await fetch(url, {
          method: "GET",
          credentials: "include",
          headers: {
            "Accept": "application/json",
          },
        });

        if (!response.ok) {
          console.warn("[SAML] fetch returned non-ok:", response.status);
          if (response.status === 401) {
            console.log("[SAML] Session missing/expired — redirecting to login");
            window.location.href = `/`;
            return;
          }
          throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        setUserData(data);
        
        // Extract course data from SAML response
        const courseData = {};
        const apiData = data?.api_data;

        if (Array.isArray(apiData)) {
          apiData.forEach((source, srcIndex) => {
            const ds = source?.["data-source"] || source?.data_source || `source_${srcIndex}`;
            const courses = Array.isArray(source?.courses) ? source.courses : Array.isArray(source?.data) ? source.data : [];

            courses.forEach((course) => {
              if (!course || typeof course !== "object") return;

              if (ds === "taxila") {
                if (course.fullname && course.shortname) {
                  courseData[course.fullname] = course.shortname;
                }
              } else if (ds === "canvas") {
                if (course.name && course.course_code) {
                  courseData[course.name] = course.course_code;
                }
              } else {
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
      } catch (err) {
        console.error("Error fetching SAML data:", err);
        setSamlData({});
      }
    };

    fetchSamlData();
  }, []);

  // Function to fetch saved assignments
  const fetchSavedAssignments = async () => {
    try {
      const res = await fetch(`${getApiUrl(SERVERS.STUDENT, ENDPOINTS.LIST_ASSIGNMENTS)}?student_id=${encodeURIComponent(studentId)}`)
      if (!res.ok) throw new Error('Failed to fetch saved assignments')
      const data = await res.json()
      setSavedAssignments(data)
    } catch (e) {
      console.error('Error fetching saved assignments:', e)
      notify('Failed to load saved assignments', 'error')
    }
  }

  // Function to fetch approved but not saved assignments
  const fetchApprovedNotSavedAssignments = async () => {
    try {
      const res = await fetch(`${getApiUrl(SERVERS.STUDENT, ENDPOINTS.APPROVED_NOT_SAVED)}?student_id=${encodeURIComponent(studentId)}`)
      if (!res.ok) {
        // If endpoint doesn't exist yet, return empty array
        if (res.status === 404) {
          setApprovedNotSavedAssignments([])
          return
        }
        throw new Error('Failed to fetch approved assignments')
      }
      const data = await res.json()
      setApprovedNotSavedAssignments(data)
    } catch (e) {
      console.error('Error fetching approved assignments:', e)
      setApprovedNotSavedAssignments([])
    }
  }

  // Load assignments when student ID changes
  useEffect(() => {
    if (studentId) {
      fetchSavedAssignments()
      fetchApprovedNotSavedAssignments()
    } else {
      setSavedAssignments([])
      setApprovedNotSavedAssignments([])
    }
  }, [studentId])

  // Function to check question status
  const checkQuestionStatus = async (questionSetId, showNotifications = false) => {
    try {
      setStatusRefreshing(true)
      const res = await fetch(`${getApiUrl(SERVERS.STUDENT, ENDPOINTS.STATUS)}/${questionSetId}/status`)
      
      if (res.ok) {
        const data = await res.json()
        const previousStatus = approvalStatus
        
        // Update state with new data
        setQuestionSet(data)
        setQuestions(data.generated_questions || [])
        setSelectedQuestion(data.selected_question || '')
        setApprovalStatus(data.approval_status)
        
        // Refresh assignments if status changed to approved
        if ((data.approval_status === 'approved' && previousStatus !== 'approved') || 
            (data.approval_status !== 'approved' && previousStatus === 'approved')) {
          fetchApprovedNotSavedAssignments()
        }
        
        // Show approval notification
        if (data.approval_status === 'approved' && previousStatus !== 'approved') {
          notify(
            <div style={{ padding: '0.5rem 0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <FontAwesomeIcon icon={faCheckCircle} style={{ color: '#28a745', fontSize: '1.5em' }} />
                <span style={{ fontWeight: 'bold', fontSize: '1.1em' }}>Assignment Approved!</span>
              </div>
              {data.faculty_remarks && (
                <div style={{ 
                  fontSize: '0.9em', 
                  padding: '0.5rem', 
                  backgroundColor: 'rgba(40, 167, 69, 0.1)', 
                  borderRadius: '4px',
                  marginTop: '0.5rem'
                }}>
                  <strong>Faculty remarks:</strong> {data.faculty_remarks}
                </div>
              )}
            </div>,
            'success',
            10000
          )
        }
        // Show rejection notification
        else if (data.approval_status === 'rejected' && previousStatus !== 'rejected') {
          notify(
            <div style={{ padding: '0.5rem 0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <FontAwesomeIcon icon={faExclamationTriangle} style={{ color: '#dc3545', fontSize: '1.5em' }} />
                <span style={{ fontWeight: 'bold', fontSize: '1.1em' }}>Assignment Rejected</span>
              </div>
              {data.faculty_remarks && (
                <div style={{ 
                  fontSize: '0.9em', 
                  padding: '0.5rem', 
                  backgroundColor: 'rgba(220, 53, 69, 0.1)', 
                  borderRadius: '4px',
                  marginTop: '0.5rem'
                }}>
                  <strong>Faculty remarks:</strong> {data.faculty_remarks}
                </div>
              )}
            </div>,
            'error',
            10000
          )
        }
        else if (showNotifications) {
          notify(`Current status: ${data.approval_status}`, 'info', 3000)
        }
      } else {
        const errorText = await res.text()
        console.error('Status check failed:', res.status, errorText)
        if (showNotifications) {
          notify('Failed to check status', 'error', 3000)
        }
      }
    } catch (e) {
      console.error('Error checking status:', e)
      if (showNotifications) {
        notify('Error checking status', 'error', 3000)
      }
    } finally {
      setStatusRefreshing(false)
    }
  }

  // Load initial options
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(getApiUrl(SERVERS.STUDENT, ENDPOINTS.CONTEXT_OPTIONS))
        const data = await res.json()
        setOptions(data)
      } catch (e) {
        setOptions({ domains: ['Manufacturing', 'IT', 'Healthcare'], service_categories: ['DevOps','ERP','Cloud'], departments: ['R&D','Operations','IT'] })
      }
    })()
  }, [])

  const notify = (msg, type='info', duration = 3000) => {
    setNotif({ msg, type })
    // Clear notification after duration
    setTimeout(() => setNotif(null), duration)
  }

  // Topic management functions
  const addTopic = () => {
    if (newTopic.trim() && topics.length < 4 && !topics.includes(newTopic.trim())) {
      setTopics([...topics, newTopic.trim()])
      setNewTopic('')
    }
  }

  const removeTopic = (topicToRemove) => {
    setTopics(topics.filter(topic => topic !== topicToRemove))
  }

const saveAssignment = async (questionSetId, assignmentName = null) => {
  if (!questionSetId) {
    notify('Cannot save: Assignment ID is required', 'error')
    return
  }

  try {
    notify('Saving assignment...', 'info')
    const res = await fetch(getApiUrl(SERVERS.STUDENT, ENDPOINTS.SAVE_ASSIGNMENT), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question_set_id: questionSetId,
        student_id: studentId,
        assignment_name: assignmentName || `${domain} Assignment`,
        course_name: courseName,
        course_id: courseId
      })
    })

    if (!res.ok) {
      const error = await res.text()
      throw new Error(error)
    }

    const data = await res.json()
    
    // CRITICAL: Refresh both lists after saving
    await fetchSavedAssignments() // Refresh saved assignments list
    await fetchApprovedNotSavedAssignments() // Refresh approved but not saved list
    
    notify(
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FontAwesomeIcon icon={faSave} style={{ color: '#28a745', fontSize: '1.2em' }} />
          <span style={{ fontWeight: 'bold' }}>Assignment Saved Successfully!</span>
        </div>
        <div style={{ fontSize: '0.9em' }}>
          Your assignment has been saved and moved to the Saved Assignments section.
        </div>
      </div>,
      'success',
      5000
    )
  } catch (e) {
    notify('Failed to save assignment: ' + e.message, 'error')
  }
}

  const generate = async () => {
    // Validation for required fields
    if (!studentId) {
      notify('Student ID/Email is required', 'error')
      return
    }
    if (!courseName.trim()) {
      notify('Course Name is required', 'error')
      return
    }
    if (topics.length === 0) {
      notify('At least one topic is required', 'error')
      return
    }
    if (!domain) {
      notify('Domain is required', 'error')
      return
    }

    setLoading(true)
    setQuestions([])
    try {
      const res = await fetch(getApiUrl(SERVERS.STUDENT, ENDPOINTS.GENERATE_QUESTIONS), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: studentId,
          course_id: courseId || null,
          course_name: courseName || null,
          domain,
          service_category: service || null,
          department: department || null,
          topics: topics, // Now sending as array
          handouts: handouts ? handouts.split(',').map(h=>h.trim()).filter(Boolean) : []
        })
      })
      if (!res.ok) throw new Error('Failed to generate questions')
      const data = await res.json()
      setQuestionSet(data)
      setQuestions(data.generated_questions || [])
      setApprovalStatus(data.approval_status)
      notify('Generated questions successfully!','success')
    } catch (e) {
      notify(e.message,'error')
    } finally {
      setLoading(false)
    }
  }

  const submitSelection = async () => {
    if (!questionSet?.id || !selectedQuestion) { notify('Pick a question first','error'); return }
    try {
      const res = await fetch(`${getApiUrl(SERVERS.STUDENT, ENDPOINTS.SELECT_QUESTION)}/${questionSet.id}/select`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ selected_question: selectedQuestion })
      })
      if (!res.ok) throw new Error('Failed to submit selection')
      const data = await res.json()
      setApprovalStatus(data.approval_status)
      setQuestionSet(data)
      notify('Submitted for faculty approval','success')
    } catch (e) {
      notify(e.message,'error')
    }
  }

  const canGenerate = studentId && courseName.trim() && topics.length > 0 && domain

  return (
    <div className="container" style={{ padding: '2rem 0', minHeight: '100vh' }}>
      <div className="text-center" style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem'}}>
          <div style={{ fontSize: '3rem', color: 'var(--primary)' }}>
            <FontAwesomeIcon icon={faListCheck} />
          </div>
          <h1 style={{ fontSize: '2.2rem', margin: 0 }}>Student Workflow</h1>
        </div>
        <p style={{ color: 'var(--text-secondary)' }}>Select context, generate questions, pick one, send for approval.</p>
      </div>

      {notif && (
        <div 
          className="card" 
          style={{ 
            marginBottom: '1rem', 
            borderLeft: `4px solid ${notif.type==='error'?'#dc3545': notif.type==='success'?'#28a745':'#17a2b8'}`,
            backgroundColor: notif.type==='error'?'rgba(220, 53, 69, 0.05)': notif.type==='success'?'rgba(40, 167, 69, 0.05)':'rgba(23, 162, 184, 0.05)',
            transition: 'all 0.3s ease'
          }}
        >
          {notif.msg}
        </div>
      )}

      {/* Student ID Section - Separate at the top */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem', color: 'var(--primary)' }}>
          <FontAwesomeIcon icon={faTag} style={{ marginRight: '0.5rem' }} /> Student Identification
        </h3>
        <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit,minmax(300px,1fr))' }}>
          <div>
            <label className="form-label">Student ID / Email *</label>
            <input 
              className="form-input" 
              placeholder="Enter your student ID or email" 
              value={studentId} 
              onChange={e=>setStudentId(e.target.value)} 
            />
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              Enter your ID to view and manage your assignments
            </div>
          </div>
        </div>
      </div>

      {/* Approved but Not Saved Assignments Section */}
      {studentId && approvedNotSavedAssignments.length > 0 && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ marginBottom: '1rem', color: 'var(--warning)' }}>
            <FontAwesomeIcon icon={faHourglassHalf} style={{ marginRight: '0.5rem' }} />
            Approved Assignments - Ready to Save
          </h3>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
            These assignments have been approved by faculty but haven't been saved yet.
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {approvedNotSavedAssignments.map((assignment) => (
              <div key={assignment.id} className="card" style={{ 
                padding: '1.5rem',
                borderLeft: '4px solid var(--warning)',
                backgroundColor: 'var(--surface)'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
                  <div style={{ flex: 1 }}>
                    <h4 style={{ margin: 0, color: 'var(--primary)' }}>{assignment.assignment_name || `${assignment.domain} Assignment`}</h4>
                    <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                      {assignment.domain && <span>Domain: {assignment.domain}</span>}
                      {assignment.course_name && (
                        <span style={{ marginLeft: '1rem' }}>Course: {assignment.course_name}</span>
                      )}
                      <span style={{ marginLeft: '1rem' }}>Status: <span className="badge" style={{ backgroundColor: '#28a745', color: 'white' }}>Approved</span></span>
                    </div>
                    {assignment.selected_question && (
                      <div style={{ 
                        marginTop: '1rem',
                        padding: '1rem',
                        background: 'var(--bg-lighter)',
                        borderRadius: '4px',
                        whiteSpace: 'pre-wrap',
                        fontSize: '0.9rem',
                        lineHeight: '1.5'
                      }}>
                        <ReactMarkdown>{assignment.selected_question}</ReactMarkdown>
                      </div>
                    )}
                    {assignment.faculty_remarks && (
                      <div style={{ 
                        marginTop: '0.5rem',
                        padding: '0.75rem',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        borderRadius: '4px',
                        fontSize: '0.85rem'
                      }}>
                        <strong>Faculty Remarks:</strong> {assignment.faculty_remarks}
                      </div>
                    )}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', minWidth: '120px' }}>
                    <button 
                      className="btn btn-success"
                      onClick={() => saveAssignment(assignment.id, assignment.assignment_name)}
                      style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem' }}
                    >
                      <FontAwesomeIcon icon={faSave} /> Save
                    </button>
                    <button 
                      className="btn btn-secondary"
                      onClick={() => checkQuestionStatus(assignment.id, true)}
                      style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem' }}
                    >
                      <FontAwesomeIcon icon={faRotate} /> Refresh
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Saved Assignments Section */}
      {studentId && savedAssignments.length > 0 && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ marginBottom: '1rem', color: 'var(--success)' }}>
            <FontAwesomeIcon icon={faBookmark} style={{ marginRight: '0.5rem' }} />
            Saved Assignments
          </h3>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
            These assignments have been saved and are ready for submission.
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {savedAssignments.map((assignment) => (
              <div key={assignment.id} className="card" style={{ padding: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
                  <div style={{ flex: 1 }}>
                    <h4 style={{ margin: 0, color: 'var(--primary)' }}>{assignment.assignment_name}</h4>
                    <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                      {assignment.domain && <span>Domain: {assignment.domain}</span>}
                      {assignment.course_name && (
                        <span style={{ marginLeft: '1rem' }}>Course: {assignment.course_name}</span>
                      )}
                      {assignment.course_id && (
                        <span style={{ marginLeft: '1rem' }}>Course ID: {assignment.course_id}</span>
                      )}
                    </div>
                    <div style={{ 
                      marginTop: '1rem',
                      padding: '1rem',
                      background: 'var(--surface)',
                      borderRadius: '4px',
                      whiteSpace: 'pre-wrap',
                      fontSize: '0.9rem',
                      lineHeight: '1.5'
                    }}>
                      <ReactMarkdown>{assignment.description}</ReactMarkdown>
                    </div>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', minWidth: '120px', textAlign: 'right' }}>
                    Saved on {new Date(assignment.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Context & Generation Section */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem', color: 'var(--primary)' }}>
          <FontAwesomeIcon icon={faMagicWandSparkles} style={{ marginRight: '0.5rem' }} /> Context & Generation
        </h3>
        
        {/* Required Fields Section */}
        <div style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: 'var(--surface)', borderRadius: '8px' }}>
          <h4 style={{ marginBottom: '1rem', color: 'var(--primary)' }}>Required Information</h4>
          <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit,minmax(250px,1fr))' }}>
            {/* Course Selection */}
            <div>
              <label className="form-label">Course Name *</label>
              <select
                className="form-input"
                value={courseName}
                onChange={(e) => {
                  const title = e.target.value;
                  setCourseName(title);
                  setCourseId(samlData[title] ?? "");
                }}
                style={{ fontSize: "1rem" }}
              >
                <option value="" disabled>Select a Course</option>
                {Object.entries(samlData).map(([title, code]) => (
                  <option key={code ?? title} value={title}>
                    {title}
                  </option>
                ))}
              </select>
            </div>

            {/* Course ID (auto-filled) */}
            <div>
              <label className="form-label">Course ID</label>
              <input
                type="text"
                className="form-input"
                value={courseId}
                readOnly
                placeholder="Course ID (auto-filled)"
                style={{ fontSize: "1rem", backgroundColor: 'var(--bg-light)' }}
              />
            </div>

            {/* Domain Selection */}
            <div>
              <label className="form-label">Domain *</label>
              <select className="form-input" value={domain} onChange={e=>setDomain(e.target.value)}>
                <option value="">Select Domain *</option>
                {options.domains.map(d=> <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
          </div>

          {/* Topics Section */}
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
                backgroundColor: 'var(--bg-lighter)',
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
        </div>

        {/* Optional Fields Section */}
        <div style={{ padding: '1rem', backgroundColor: 'var(--bg-lighter)', borderRadius: '8px' }}>
          <h4 style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>Optional Information</h4>
          <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))' }}>
            <select className="form-input" value={service} onChange={e=>setService(e.target.value)}>
              <option value="">Service/Product</option>
              {options.service_categories.map(s=> <option key={s} value={s}>{s}</option>)}
            </select>
            <select className="form-input" value={department} onChange={e=>setDepartment(e.target.value)}>
              <option value="">Department</option>
              {options.departments.map(d=> <option key={d} value={d}>{d}</option>)}
            </select>
            <input className="form-input" placeholder="Handouts (URLs, comma separated)" value={handouts} onChange={e=>setHandouts(e.target.value)} />
          </div>
        </div>

        <div style={{ textAlign: 'center', marginTop: '1.5rem' }}>
          <button 
            className="btn btn-primary" 
            onClick={generate} 
            disabled={!canGenerate || loading}
            style={{ minWidth: '200px', padding: '0.75rem 1.5rem' }}
          >
            {loading ? 'Generating...' : 'Generate Questions'}
          </button>
        </div>
      </div>

      {questions.length > 0 && (
        <div className="card">
          <h3 style={{ marginBottom: '1rem' }}>Generated Questions</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {questions.map((q, idx) => (
              <label key={idx} className="card" style={{ 
                display: 'flex', 
                alignItems: 'flex-start', 
                gap: '1rem', 
                cursor: 'pointer',
                padding: '1.5rem',
                borderLeft: selectedQuestion === q ? '4px solid var(--primary)' : undefined,
                transition: 'all 0.3s ease'
              }}>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                  <div style={{ 
                    minWidth: '30px',
                    height: '30px',
                    borderRadius: '50%',
                    background: selectedQuestion === q ? 'var(--primary)' : 'var(--surface-hover)',
                    color: selectedQuestion === q ? 'white' : 'var(--text-secondary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 'bold'
                  }}>
                    {idx + 1}
                  </div>
                  <input 
                    type="radio" 
                    name="q" 
                    checked={selectedQuestion===q} 
                    onChange={()=>setSelectedQuestion(q)} 
                    style={{ marginTop: '0.5rem' }} 
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ 
                    whiteSpace: 'pre-wrap',
                    lineHeight: '1.6',
                    color: selectedQuestion === q ? 'var(--text-primary)' : 'var(--text-secondary)'
                  }}>

        <ReactMarkdown>{q}</ReactMarkdown>
                  </div>
                  <div style={{ 
                    marginTop: '1rem', 
                    fontSize: '0.9rem', 
                    color: 'var(--text-secondary)'
                  }}>
                    Assignment {idx + 1} of {questions.length}
                  </div>
                </div>
              </label>
            ))}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                {approvalStatus === 'approved' ? (
                  <span className="badge" style={{ backgroundColor: '#28a745', color: 'white' }}>
                    <FontAwesomeIcon icon={faCheckCircle} style={{ marginRight: '0.25rem' }} /> Approved
                  </span>
                ) : approvalStatus ? (
                  <span className="badge" style={{ backgroundColor: '#ff9800', color: 'white' }}>{approvalStatus}</span>
                ) : null}
              </div>
              {questionSet?.id && (
                <>
                  <button 
                    className="btn btn-sm" 
                    onClick={() => checkQuestionStatus(questionSet.id, true)}
                    disabled={statusRefreshing}
                    style={{ 
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.25rem 0.75rem',
                      backgroundColor: 'var(--surface)',
                      border: '1px solid var(--border-color)',
                      color: 'var(--text-secondary)',
                      fontSize: '0.9rem'
                    }}
                  >
                  <FontAwesomeIcon 
                    icon={faRotate} 
                    className={statusRefreshing ? 'fa-spin' : ''} 
                  />
                  Check Status
                </button>
                {questionSet.faculty_remarks && (approvalStatus === 'approved' || approvalStatus === 'rejected') && (
                  <div 
                    style={{ 
                      position: 'absolute',
                      left: '0',
                      right: '0',
                      marginTop: '3rem',
                      padding: '0.75rem',
                      borderRadius: '4px',
                      backgroundColor: approvalStatus === 'approved' ? 'rgba(40, 167, 69, 0.1)' : 'rgba(255, 152, 0, 0.1)',
                      border: `1px solid ${approvalStatus === 'approved' ? '#28a745' : '#ff9800'}`,
                      fontSize: '0.9rem'
                    }}
                  >
                    <strong>Faculty Remarks:</strong> {questionSet.faculty_remarks}
                  </div>
                )}
                </>
              )}
            </div>
            <div style={{ display: 'flex', gap: '1rem' }}>
              {approvalStatus === 'approved' && (
                <button
                  className="btn btn-success"
                  onClick={() => saveAssignment(questionSet.id)}
                  style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                >
                  <FontAwesomeIcon icon={faSave} /> Save Assignment
                </button>
              )}
              <button 
                className="btn btn-secondary" 
                onClick={submitSelection} 
                disabled={!selectedQuestion || approvalStatus === 'approved'}
              >
                Send for Approval <FontAwesomeIcon icon={faChevronRight} style={{ marginLeft: '0.5rem' }} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default StudentWorkflow