import React, { useEffect, useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { useNavigate } from 'react-router-dom'
import Select from 'react-select'
import { faListCheck, faMagicWandSparkles, faChevronRight, faCheckCircle, faExclamationTriangle, faRotate, faSave, faChartLine } from '@fortawesome/free-solid-svg-icons'
import { getApiUrl, SERVERS, ENDPOINTS } from '../config/api'

const StudentWorkflow = () => {
  const [options, setOptions] = useState({ domains: [], service_categories: [], departments: [] })
  const [domain, setDomain] = useState('')
  const [service, setService] = useState('')
  const [department, setDepartment] = useState('')
  const [topics, setTopics] = useState('')
  const [handouts, setHandouts] = useState('')
  const [studentId, setStudentId] = useState('student@example.com')
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
  const [courses, setCourses] = useState([])


  // Function to fetch saved assignments
  const fetchSavedAssignments = async () => {
    try {
      const res = await fetch(`${getApiUrl(SERVERS.STUDENT)}/assignments?student_id=${encodeURIComponent(studentId)}`)
      if (!res.ok) throw new Error('Failed to fetch saved assignments')
      const data = await res.json()
      setSavedAssignments(data)
    } catch (e) {
      console.error('Error fetching saved assignments:', e)
      notify('Failed to load saved assignments', 'error')
    }
  }

  // Load saved assignments when student ID changes
  useEffect(() => {
    if (studentId) {
      fetchSavedAssignments()
    }
  }, [studentId])

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const res = await fetch(getApiUrl(SERVERS.STUDENT, ENDPOINTS.STUDENT_COURSES))
        if (!res.ok) throw new Error("Failed to fetch courses")
        const data = await res.json()
        setCourses(data)
      } catch (e) {
        console.error("Error loading courses:", e)
      }
    }
    fetchCourses()
  }, [])


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
  }, []) // Re-run when question set ID changes

  const notify = (msg, type='info', duration = 3000) => {
    setNotif({ msg, type })
    // Clear notification after duration
    setTimeout(() => setNotif(null), duration)
  }

  const saveAssignment = async () => {
    if (!questionSet?.id || !selectedQuestion || approvalStatus !== 'approved') {
      notify('Cannot save: Assignment must be approved first', 'error')
      return
    }

    try {
      notify('Saving assignment...', 'info')
      const res = await fetch(getApiUrl(SERVERS.STUDENT, ENDPOINTS.SAVE_ASSIGNMENT), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question_set_id: questionSet.id,
          student_id: studentId,
          assignment_name: `${domain} Assignment`,
          course_name: courseName
        })
      })

      if (!res.ok) {
        const error = await res.text()
        throw new Error(error)
      }

      const data = await res.json()
      await fetchSavedAssignments() // Refresh the list of saved assignments
      notify(
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FontAwesomeIcon icon={faSave} style={{ color: '#28a745', fontSize: '1.2em' }} />
            <span style={{ fontWeight: 'bold' }}>Assignment Saved Successfully!</span>
          </div>
          <div style={{ fontSize: '0.9em' }}>
            Your assignment has been saved. You can view it in the list below.
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
    if (!studentId || !domain) { notify('Student and domain required','error'); return }
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
          topics: topics ? topics.split(',').map(t=>t.trim()).filter(Boolean) : [],
          handouts: handouts ? handouts.split(',').map(h=>h.trim()).filter(Boolean) : []
        })
      })
      if (!res.ok) throw new Error('Failed to generate questions')
      const data = await res.json()
      setQuestionSet(data)
      setQuestions(data.generated_questions || [])
      setApprovalStatus(data.approval_status)
      notify('Generated questions','success')
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

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem', color: 'var(--primary)' }}>
          <FontAwesomeIcon icon={faMagicWandSparkles} style={{ marginRight: '0.5rem' }} /> Context & Generation
        </h3>
        <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))' }}>
          <input className="form-input" placeholder="Student ID / Email" value={studentId} onChange={e=>setStudentId(e.target.value)} />
          {/* <input className="form-input" placeholder="Course Name (optional)" value={courseName} onChange={e=>setCourseName(e.target.value)} /> */}
          {/* <input className="form-input" placeholder="Course ID (optional)" value={courseId} onChange={e=>setCourseId(e.target.value)} /> */}
 {/* Existing Courses Dropdown */}
<Select
  options={courses.map(c => ({
    value: c.course_code,
    label: `${c.title} (${c.course_code})`
  }))}
  value={courseId ? { value: courseId, label: `${courseName} (${courseId})` } : null}
  onChange={selected => {
    if (selected) {
      setCourseId(selected.value)
      const c = courses.find(c => c.course_code === selected.value)
      setCourseName(c ? c.title : "")
    }
  }}
  onInputChange={input => setCourseName(input)} // allows new typing
  isClearable
  placeholder="Select or type course name"
  styles={{
    color:"#fff", 
    control: (baseStyles, state) => ({
      ...baseStyles,
      backgroundColor: "var(--bg-lighter)", // 👈 use your CSS variable
      borderColor: state.isFocused ? "#666" : "#555",
      boxShadow: "none",
      color: "#fff",
    }),
    menu: (baseStyles) => ({
      ...baseStyles,
      backgroundColor: "var(--bg-lighter)", // dropdown background
    }),
    option: (baseStyles, { isFocused, isSelected }) => ({
      ...baseStyles,
      backgroundColor: isSelected
        ? "#666"
        : isFocused
        ? "#555"
        : "var(--bg-lighter)",
      color: "#fff",
      cursor: "pointer",
    }),
    singleValue: (baseStyles) => ({
      ...baseStyles,
      color: "#fff",
    }),
  }}
/>





          <select className="form-input" value={domain} onChange={e=>setDomain(e.target.value)}>
            <option value="">Select Domain *</option>
            {options.domains.map(d=> <option key={d} value={d}>{d}</option>)}
          </select>
          <select className="form-input" value={service} onChange={e=>setService(e.target.value)}>
            <option value="">Service/Product</option>
            {options.service_categories.map(s=> <option key={s} value={s}>{s}</option>)}
          </select>
          <select className="form-input" value={department} onChange={e=>setDepartment(e.target.value)}>
            <option value="">Department</option>
            {options.departments.map(d=> <option key={d} value={d}>{d}</option>)}
          </select>
          <input className="form-input" placeholder="Topics (comma separated)" value={topics} onChange={e=>setTopics(e.target.value)} />
          <input className="form-input" placeholder="Handouts (URLs, comma separated)" value={handouts} onChange={e=>setHandouts(e.target.value)} />
        </div>
        <div style={{ textAlign: 'center', marginTop: '1rem' }}>
          <button className="btn btn-primary" onClick={generate} disabled={loading || !studentId || !domain}>
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
                    {q}
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
                  onClick={saveAssignment}
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

      {/* Saved Assignments Section */}
      {savedAssignments.length > 0 && (
        <div className="card" style={{ marginTop: '2rem' }}>
          <h3 style={{ marginBottom: '1rem' }}>
            <FontAwesomeIcon icon={faSave} style={{ marginRight: '0.5rem' }} />
            Saved Assignments
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {savedAssignments.map((assignment) => (
              <div key={assignment.id} className="card" style={{ padding: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
                  <div>
                    <h4 style={{ margin: 0, color: 'var(--primary)' }}>{assignment.assignment_name}</h4>
                    <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                      {assignment.domain && <span>Domain: {assignment.domain}</span>}
                      {assignment.course_name && (
                        <span style={{ marginLeft: '1rem' }}>Course: {assignment.course_name}</span>
                      )}
                    </div>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    Saved on {new Date(assignment.created_at).toLocaleDateString()}
                  </div>
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
                  {assignment.description}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default StudentWorkflow





