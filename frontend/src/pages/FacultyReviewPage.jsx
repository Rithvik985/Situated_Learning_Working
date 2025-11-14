import React, { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown';
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { getApiUrl, SERVERS, ENDPOINTS } from '../config/api'

const FacultyReviewPage = () => {
  const { questionSetId } = useParams()
  const location = useLocation()
  const [questionSetDetail, setQuestionSetDetail] = useState(null)
  const [remarks, setRemarks] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const fetchData = async () => {
    setLoading(true)
    try {
      // Use the new endpoint to get a single question set detail
      const res = await fetch(`/api/faculty/questions/${questionSetId}`)
      if (!res.ok) throw new Error('No data found')
      const data = await res.json()
      setQuestionSetDetail(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Check if we have data from navigation state first
    if (location.state?.questionSetDetail) {
      setQuestionSetDetail(location.state.questionSetDetail)
    } else {
      fetchData()
    }
  }, [questionSetId, location.state])

  const handleAction = async (approve) => {
    if (!questionSetDetail) return
    
    try {
      await fetch(`${getApiUrl(SERVERS.FACULTY, ENDPOINTS.FACULTY_APPROVE_QUESTION)}/${questionSetDetail.id}/approve`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approve, remarks: remarks || '', faculty_id: 'FAC123' })
      })
      
      // Update local state to show approval status immediately
      setQuestionSetDetail(prev => ({
        ...prev,
        approval_status: approve ? 'approved' : 'rejected',
        faculty_remarks: remarks
      }))
      
      console.log(`Question ${questionSetDetail.id} ${approve ? 'approved' : 'rejected'}`)
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <div className="container" style={{ padding: '2rem 0', backgroundColor: '#2c3e50', minHeight: '100vh', color: '#ecf0f1' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 style={{ color: '#ecf0f1' }}>Review Assignment Request</h2>
        <button
          onClick={fetchData}
          disabled={loading}
          style={{
            background: '#3498db',
            color: 'white',
            padding: '8px 16px',
            borderRadius: '5px',
            border: 'none',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1
          }}
        >
          {loading ? 'Refreshing...' : '🔄 Refresh'}
        </button>
      </div>

      {loading && !questionSetDetail ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#ecf0f1' }}>Loading...</div>
      ) : !questionSetDetail ? (
        <div style={{ 
          textAlign: 'center', 
          padding: '2rem',
          color: '#95a5a6',
          fontStyle: 'italic'
        }}>
          No question set found.
        </div>
      ) : (
        <div 
          className="card" 
          style={{ 
            marginBottom: '1rem', 
            padding: '1.5rem',
            backgroundColor: '#34495e',
            borderRadius: '8px',
            borderLeft: questionSetDetail.approval_status === 'approved' 
              ? '4px solid #27ae60' 
              : '4px solid transparent',
            color: '#ecf0f1',
            boxShadow: '0 2px 8px rgba(0,0,0,0.3)'
          }}
        >
          {/* Approval Status Badge */}
          {questionSetDetail.approval_status === 'approved' && (
            <div style={{
              display: 'inline-block',
              background: '#27ae60',
              color: 'white',
              padding: '4px 8px',
              borderRadius: '4px',
              fontSize: '0.8rem',
              fontWeight: 'bold',
              marginBottom: '0.5rem'
            }}>
              ✅ Approved
            </div>
          )}

          {/* Course and Student Info */}
          <div style={{ marginBottom: '1rem', color: '#bdc3c7', fontSize: '0.9rem' }}>
            <div><strong style={{ color: '#ecf0f1' }}>Student:</strong> {questionSetDetail.student_id}</div>
            {questionSetDetail.course_name && (
              <div><strong style={{ color: '#ecf0f1' }}>Course:</strong> {questionSetDetail.course_name}</div>
            )}
            <div><strong style={{ color: '#ecf0f1' }}>Domain:</strong> {questionSetDetail.domain}</div>
            {questionSetDetail.service_category && (
              <div><strong style={{ color: '#ecf0f1' }}>Service Category:</strong> {questionSetDetail.service_category}</div>
            )}
            {questionSetDetail.department && (
              <div><strong style={{ color: '#ecf0f1' }}>Department:</strong> {questionSetDetail.department}</div>
            )}
          </div>

          {/* Assignment Details */}
          {questionSetDetail.assignment_details && (
            <div style={{ 
              background: '#2c3e50', 
              padding: '1rem', 
              borderRadius: '6px',
              marginBottom: '1rem',
              border: '1px solid #34495e'
            }}>
              <h4 style={{ marginTop: 0, color: '#f39c12' }}>Assignment Details</h4>
              {questionSetDetail.assignment_details.title && (
                <div style={{ color: '#ecf0f1' }}><strong style={{ color: '#f39c12' }}>Title:</strong> {questionSetDetail.assignment_details.title}</div>
              )}
              {questionSetDetail.assignment_details.description && (
                <div style={{ marginTop: '0.5rem', color: '#ecf0f1' }}>
                  <strong style={{ color: '#f39c12' }}>Description:</strong>
                  <div style={{ marginTop: '0.25rem', color: '#ecf0f1' }}>
                    <ReactMarkdown>{questionSetDetail.assignment_details.description}</ReactMarkdown>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* Selected Question */}
          <div style={{ fontWeight: 'bold', marginBottom: '0.5rem', color: '#ecf0f1' }}>
            Selected Question:
          </div>
          
          <div style={{
            padding: '1.5rem',
            borderRadius: '6px',
            marginBottom: '1rem',
            background: '#2c3e50',
            border: '1px solid #34495e',
            color: '#ecf0f1'
          }}>
            <ReactMarkdown>{questionSetDetail.selected_question || 'No question selected'}</ReactMarkdown>
          </div>

          {/* Remarks Input - Only show for pending questions */}
          {(!questionSetDetail.approval_status || questionSetDetail.approval_status === 'pending') && (
            <input
              className="form-input"
              placeholder="Remarks (optional)"
              style={{ 
                marginRight: '1rem', 
                width: '300px', 
                marginBottom: '1rem',
                backgroundColor: '#2c3e50',
                color: '#ecf0f1',
                border: '1px solid #34495e',
                padding: '8px',
                borderRadius: '4px'
              }}
              value={remarks}
              onChange={(e) => setRemarks(e.target.value)}
            />
          )}

          {/* Show remarks if provided and approved */}
          {questionSetDetail.approval_status === 'approved' && (questionSetDetail.faculty_remarks || remarks) && (
            <div style={{ 
              padding: '0.5rem', 
              borderRadius: '4px',
              marginBottom: '1rem',
              fontSize: '0.9rem',
              color: '#ecf0f1',
              background: '#2c3e50'
            }}>
              <strong>Remarks:</strong> {questionSetDetail.faculty_remarks || remarks}
            </div>
          )}

          {/* Action Buttons - Only show for pending questions */}
          {(!questionSetDetail.approval_status || questionSetDetail.approval_status === 'pending') ? (
            <div>
              <button
                className="btn"
                style={{ 
                  background: '#27ae60', 
                  color: 'white', 
                  marginRight: '0.5rem', 
                  padding: '6px 10px', 
                  borderRadius: '4px', 
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'background 0.3s'
                }}
                onMouseEnter={(e) => e.target.style.background = '#229954'}
                onMouseLeave={(e) => e.target.style.background = '#27ae60'}
                onClick={() => handleAction(true)}
              >
                Approve
              </button>

              <button
                className="btn"
                style={{ 
                  background: '#e74c3c', 
                  color: 'white', 
                  padding: '6px 10px', 
                  borderRadius: '4px', 
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'background 0.3s'
                }}
                onMouseEnter={(e) => e.target.style.background = '#c0392b'}
                onMouseLeave={(e) => e.target.style.background = '#e74c3c'}
                onClick={() => handleAction(false)}
              >
                Reject
              </button>
            </div>
          ) : (
            <div style={{ 
              color: questionSetDetail.approval_status === 'approved' ? '#27ae60' : '#e74c3c',
              fontWeight: 'bold',
              fontSize: '0.9rem'
            }}>
              {questionSetDetail.approval_status === 'approved' ? 'Approved' : 'Rejected'}
            </div>
          )}
        </div>
      )}

      <button
        onClick={() => navigate(-1)}
        style={{ 
          marginTop: '1rem', 
          background: '#7f8c8d', 
          color: 'white',
          padding: '8px 16px', 
          borderRadius: '5px', 
          border: 'none',
          cursor: 'pointer',
          transition: 'background 0.3s'
        }}
        onMouseEnter={(e) => e.target.style.background = '#95a5a6'}
        onMouseLeave={(e) => e.target.style.background = '#7f8c8d'}
      >
        ← Back
      </button>
    </div>
  )
}

export default FacultyReviewPage