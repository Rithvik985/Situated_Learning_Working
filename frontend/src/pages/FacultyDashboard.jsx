import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faFilter, faCheckCircle, faClock, faFileAlt } from '@fortawesome/free-solid-svg-icons'
import { getApiUrl, SERVERS, ENDPOINTS } from '../config/api'

const FacultyDashboard = () => {
  const [students, setStudents] = useState([])
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(false)
  const [approvalFilter, setApprovalFilter] = useState('all')
  const [evaluationFilter, setEvaluationFilter] = useState('all')
  const [courseFilter, setCourseFilter] = useState('all')
  const navigate = useNavigate()

  // const load = async () => {
  //   setLoading(true)
  //   try {
  //     const res = await fetch(getApiUrl(SERVERS.FACULTY, ENDPOINTS.FACULTY_APPROVE_QUESTION))
  //     const data = await res.json()
  //     setStudents(data)
  //   } catch (e) {
  //     console.error(e)
  //   } finally {
  //     setLoading(false)
  //   }
  // }

  const load = async () => {
    setLoading(true)
    try {
      // Load dashboard data
      const dashboardRes = await fetch('/api/faculty/dashboard')
      if (!dashboardRes.ok) throw new Error(`HTTP error! status: ${dashboardRes.status}`)
      const dashboardData = await dashboardRes.json()
      
      // Load courses for filter
      const coursesRes = await fetch('/api/faculty/courses')
      if (coursesRes.ok) {
        const coursesData = await coursesRes.json()
        setCourses(coursesData)
      }
      
      setStudents(dashboardData)
    } catch (e) {
      console.error('Error loading dashboard:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleApprove = async (questionSetId) => {
    try {
      const res = await fetch(
        getApiUrl(SERVERS.FACULTY, ENDPOINTS.FACULTY_APPROVE_QUESTION) + `/${questionSetId}/approve`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ approve: true, remarks: 'Looks good', faculty_id: 'FAC123' })
        }
      )
      const data = await res.json()
      if (data.approval_status === 'approved') {
        setStudents(prev =>
          prev.map(s =>
            s.id === data.id ? { ...s, approval_status: 'approved' } : s
          )
        )
      }
    } catch (e) {
      console.error(e)
    }
  }

  const handleReviewClick = (studentId) => {
    navigate(`/faculty/review/${studentId}`)
  }

  // ✅ Cycle through approval filter states
  const handleApprovalFilterClick = () => {
    setApprovalFilter(prev => {
      if (prev === 'all') return 'pending'
      if (prev === 'pending') return 'approved'
      return 'all'
    })
  }

  // ✅ Cycle through evaluation filter states
  const handleEvaluationFilterClick = () => {
    setEvaluationFilter(prev => {
      if (prev === 'all') return 'pending'
      if (prev === 'pending') return 'evaluated'
      if (prev === 'evaluated') return 'finalized'
      return 'all'
    })
  }

   // ✅ Apply all filters
  const filteredStudents = students.filter(s => {
    const approvalMatch = 
      approvalFilter === 'all' || 
      (approvalFilter === 'pending' && s.approval_status !== 'approved') ||
      (approvalFilter === 'approved' && s.approval_status === 'approved')
    
    const evaluationMatch = 
      evaluationFilter === 'all' ||
      (evaluationFilter === 'pending' && (!s.evaluation_status || s.evaluation_status === 'pending_faculty')) ||
      (evaluationFilter === 'evaluated' && s.evaluation_status === 'evaluated') ||
      (evaluationFilter === 'finalized' && s.evaluation_status === 'finalized')
    
    const courseMatch = 
      courseFilter === 'all' || 
      s.course_name === courseFilter
    
    return approvalMatch && evaluationMatch && courseMatch
  })

  // Get unique course names for filter dropdown
  const uniqueCourseNames = [...new Set(students.map(s => s.course_name).filter(Boolean))]
  // ✅ Count stats for clarity
  const totalCount = students.length
  const pendingApprovalCount = students.filter(s => s.approval_status !== 'approved').length
  const approvedCount = students.filter(s => s.approval_status === 'approved').length
  
  const pendingEvaluationCount = students.filter(s => !s.evaluation_status || s.evaluation_status === 'pending_faculty').length
  const evaluatedCount = students.filter(s => s.evaluation_status === 'evaluated').length
  const finalizedCount = students.filter(s => s.evaluation_status === 'finalized').length

  // // ✅ Get grade color based on score
  // const getGradeColor = (score, maxScore = 72) => {
  //   const percentage = (score / maxScore) * 100
  //   if (percentage >= 80) return '#28a745' // Green
  //   if (percentage >= 60) return '#ffc107' // Yellow
  //   if (percentage >= 40) return '#fd7e14' // Orange
  //   return '#dc3545' // Red
  // }

  // // ✅ Get grade letter based on score
  // const getGradeLetter = (score, maxScore = 72) => {
  //   const percentage = (score / maxScore) * 100
  //   if (percentage >= 80) return 'A'
  //   if (percentage >= 70) return 'B'
  //   if (percentage >= 60) return 'C'
  //   if (percentage >= 50) return 'D'
  //   return 'F'
  // }

  // ✅ Format evaluation status display
  const getEvaluationDisplay = (student) => {
    if (!student.evaluation_status) {
      return <span style={{ color: '#95a5a6' }}>Not Submitted</span>
    }

    switch (student.evaluation_status) {
      case 'pending_faculty':
        return (
          <span style={{ color: '#f39c12', fontWeight: '600' }}>
            <FontAwesomeIcon icon={faClock} style={{ marginRight: '5px' }} />
            Pending Evaluation
          </span>
        )
      
      case 'evaluated':
        return (
          <div style={{ textAlign: 'center' }}>
            <div style={{ color: '#17a2b8', fontWeight: '600', marginBottom: '2px' }}>
              <FontAwesomeIcon icon={faFileAlt} style={{ marginRight: '5px' }} />
              Evaluated
            </div>
            {student.evaluation_score && (
              <div style={{ 
                fontSize: '0.85em', 
                // color: getGradeColor(student.evaluation_score),
                fontWeight: '600'
              }}>
                {student.evaluation_score}/72
              </div>
            )}
          </div>
        )
      
      case 'finalized':
        return (
          <div style={{ textAlign: 'center' }}>
            <div style={{ color: '#28a745', fontWeight: '600', marginBottom: '2px' }}>
              <FontAwesomeIcon icon={faCheckCircle} style={{ marginRight: '5px' }} />
              Finalized
            </div>
            {student.evaluation_score && (
              <div>
                <div style={{ 
                  fontSize: '0.85em', 
                  // color: getGradeColor(student.evaluation_score),
                  fontWeight: '600',
                  marginBottom: '2px'
                }}>
                  {student.evaluation_score}/72
                </div>
                <div style={{ 
                  fontSize: '0.75em', 
                  // color: getGradeColor(student.evaluation_score),
                  fontWeight: '600',
                  // backgroundColor: `${getGradeColor(student.evaluation_score)}15`,
                  padding: '1px 6px',
                  borderRadius: '12px',
                  display: 'inline-block'
                }}>
                  {/* {getGradeLetter(student.evaluation_score)} */}
                </div>
              </div>
            )}
          </div>
        )
      
      default:
        return <span style={{ color: '#95a5a6' }}>{student.evaluation_status}</span>
    }
  }

  return (
    <div className="container" style={{ padding: '2rem 0', minHeight: '100vh' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '1.5rem' }}>Faculty Dashboard</h1>
      <p style={{ textAlign: 'center', color: 'gray', marginBottom: '2rem' }}>
        View student submissions and manage approvals.
      </p>
      {/* ✅ Filters Section */}
      <div style={{ 
        display: 'flex', 
        gap: '1rem', 
        marginBottom: '2rem', 
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        {/* Course Filter */}
        <div>
          <label style={{ marginRight: '0.5rem', fontWeight: '600' }}>Course:</label>
          <select 
            value={courseFilter}
            onChange={(e) => setCourseFilter(e.target.value)}
            style={{ 
              padding: '0.5rem', 
              borderRadius: '4px', 
              border: '1px solid #ccc',
              minWidth: '150px'
            }}
          >
            <option value="all">All Courses</option>
            {uniqueCourseNames.map(course => (
              <option key={course} value={course}>{course}</option>
            ))}
          </select>
        </div>

        {/* Approval Filter Button */}
        <button
          onClick={handleApprovalFilterClick}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: 
              approvalFilter === 'pending' ? '#fff3cd' :
              approvalFilter === 'approved' ? '#d4edda' : '#f8f9fa',
            color: 
              approvalFilter === 'pending' ? '#856404' :
              approvalFilter === 'approved' ? '#155724' : '#343a40',
            border: '1px solid #dee2e6',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: '600'
          }}
        >
          <FontAwesomeIcon icon={faFilter} style={{ marginRight: '5px' }} />
          {approvalFilter === 'all' ? 'All Approvals' : 
           approvalFilter === 'pending' ? 'Pending Approvals' : 'Approved Only'}
        </button>

        {/* Evaluation Filter Button */}
        <button
          onClick={handleEvaluationFilterClick}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: 
              evaluationFilter === 'pending' ? '#fff3cd' :
              evaluationFilter === 'evaluated' ? '#d1ecf1' :
              evaluationFilter === 'finalized' ? '#d4edda' : '#f8f9fa',
            color: 
              evaluationFilter === 'pending' ? '#856404' :
              evaluationFilter === 'evaluated' ? '#0c5460' :
              evaluationFilter === 'finalized' ? '#155724' : '#343a40',
            border: '1px solid #dee2e6',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: '600'
          }}
        >
          <FontAwesomeIcon icon={faFilter} style={{ marginRight: '5px' }} />
          {evaluationFilter === 'all' ? 'All Evaluations' :
           evaluationFilter === 'pending' ? 'Pending Evaluation' :
           evaluationFilter === 'evaluated' ? 'Evaluated Only' : 'Finalized Only'}
        </button>
      </div>
      {/* ✅ Statistics Overview */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
        gap: '1rem', 
        marginBottom: '2rem' 
      }}>
        <div style={{ 
          padding: '1rem', 
          backgroundColor: '#f8f9fa', 
          borderRadius: '8px', 
          textAlign: 'center',
          border: '1px solid #dee2e6'
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#343a40' }}>{totalCount}</div>
          <div style={{ color: '#6c757d' }}>Total Students</div>
        </div>
        <div style={{ 
          padding: '1rem', 
          backgroundColor: '#fff3cd', 
          borderRadius: '8px', 
          textAlign: 'center',
          border: '1px solid #ffeaa7'
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#856404' }}>{pendingApprovalCount}</div>
          <div style={{ color: '#856404' }}>Pending Approval</div>
        </div>
        <div style={{ 
          padding: '1rem', 
          backgroundColor: '#d1ecf1', 
          borderRadius: '8px', 
          textAlign: 'center',
          border: '1px solid #bee5eb'
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#0c5460' }}>{pendingEvaluationCount}</div>
          <div style={{ color: '#0c5460' }}>Pending Evaluation</div>
        </div>
        <div style={{ 
          padding: '1rem', 
          backgroundColor: '#d4edda', 
          borderRadius: '8px', 
          textAlign: 'center',
          border: '1px solid #c3e6cb'
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#155724' }}>{finalizedCount}</div>
          <div style={{ color: '#155724' }}>Finalized</div>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center' }}>Loading...</div>
      ) : (
        <div className="table-container" style={{ overflowX: 'auto' }}>
          <table className="table table-striped" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: 'rgb(52,73,94)', textAlign: 'left', color: 'white' }}>
                <th style={{ padding: '12px' }}>Student ID / Email</th>
                <th style={{ padding: '12px' }}>Course Name</th>
                <th style={{ padding: '12px', textAlign: 'center' }}>
                  Approval Status
                  <button
                    onClick={handleApprovalFilterClick}
                    title={
                      approvalFilter === 'all' ? 'Showing All' :
                      approvalFilter === 'pending' ? 'Showing Pending Only' :
                      'Showing Approved Only'
                    }
                    style={{
                      marginLeft: '10px',
                      backgroundColor: 'transparent',
                      border: 'none',
                      cursor: 'pointer',
                      color:
                        approvalFilter === 'pending' ? '#f1c40f' :
                        approvalFilter === 'approved' ? '#2ecc71' : 'white',
                      transition: 'color 0.2s ease',
                      fontSize: '1rem'
                    }}
                  >
                    <FontAwesomeIcon icon={faFilter} />
                  </button>
                </th>
                <th style={{ padding: '12px', textAlign: 'center' }}>
                  Evaluation Status & Marks
                  <button
                    onClick={handleEvaluationFilterClick}
                    title={
                      evaluationFilter === 'all' ? 'Showing All' :
                      evaluationFilter === 'pending' ? 'Showing Pending Only' :
                      evaluationFilter === 'evaluated' ? 'Showing Evaluated Only' :
                      'Showing Finalized Only'
                    }
                    style={{
                      marginLeft: '10px',
                      backgroundColor: 'transparent',
                      border: 'none',
                      cursor: 'pointer',
                      color:
                        evaluationFilter === 'pending' ? '#f1c40f' :
                        evaluationFilter === 'evaluated' ? '#3498db' :
                        evaluationFilter === 'finalized' ? '#2ecc71' : 'white',
                      transition: 'color 0.2s ease',
                      fontSize: '1rem'
                    }}
                  >
                    <FontAwesomeIcon icon={faFilter} />
                  </button>
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredStudents.length === 0 ? (
                <tr>
                  <td colSpan="4" style={{ textAlign: 'center', padding: '2rem' }}>
                    No submissions found matching the current filters.
                  </td>
                </tr>
              ) : (
                filteredStudents.map((s) => (
                  <tr key={s.id} style={{ borderBottom: '1px solid #ddd' }}>
                    <td style={{ padding: '12px' }}>{s.student_email || s.student_id}</td>
                    <td style={{ padding: '12px' }}>{s.course_name || 'N/A'}</td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      {s.approval_status === 'approved' ? (
                        <button
                          style={{
                            backgroundColor: 'rgba(54, 134, 87, 1)',
                            color: 'white',
                            border: 'none',
                            padding: '6px 10px',
                            borderRadius: '6px',
                            fontWeight: '600',
                            cursor: 'default',
                            display: 'block',
                            margin: '0 auto'
                          }}
                        >
                          Approved
                        </button>
                      ) : (
                        <button
                          onClick={() => handleReviewClick(s.student_id)}
                          style={{
                            backgroundColor: 'rgb(52, 72, 94)',
                            color: 'white',
                            border: 'none',
                            padding: '6px 25px',
                            borderRadius: '6px',
                            fontWeight: '600',
                            cursor: 'pointer',
                            transition: 'background-color 0.3s ease',
                            display: 'block',
                            margin: '0 auto'
                          }}
                          onMouseEnter={(e) => e.target.style.backgroundColor = 'rgb(42, 62, 84)'}
                          onMouseLeave={(e) => e.target.style.backgroundColor = 'rgb(52, 72, 94)'}
                        >
                          Pending
                        </button>
                      )}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      {getEvaluationDisplay(s)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* ✅ Filter Status Display - Updated */}
      <div style={{ 
        marginTop: '1rem', 
        padding: '0.5rem', 
        backgroundColor: '#f8f9fa', 
        borderRadius: '4px',
        fontSize: '0.9em',
        color: '#6c757d',
        textAlign: 'center'
      }}>
        Showing: 
        <strong style={{ marginLeft: '5px' }}>
          {courseFilter === 'all' ? 'All Courses' : courseFilter}
        </strong>
        {' • '}
        <strong>
          {approvalFilter === 'all' ? 'All Approvals' : 
           approvalFilter === 'pending' ? 'Pending Approvals' : 'Approved Only'}
        </strong>
        {' • '}
        <strong>
          {evaluationFilter === 'all' ? 'All Evaluations' :
           evaluationFilter === 'pending' ? 'Pending Evaluation' :
           evaluationFilter === 'evaluated' ? 'Evaluated Only' : 'Finalized Only'}
        </strong>
        {' • '}
        {filteredStudents.length} of {totalCount} students
      </div>
    </div>
  )
}

export default FacultyDashboard