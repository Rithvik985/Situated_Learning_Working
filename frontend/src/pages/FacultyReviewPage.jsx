import React, { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown';
import { useParams, useNavigate } from 'react-router-dom'
import { getApiUrl, SERVERS, ENDPOINTS } from '../config/api'

const FacultyReviewPage = () => {
  const { studentId } = useParams()
  const [questions, setQuestions] = useState([])
  const [remarks, setRemarks] = useState({})
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${getApiUrl(SERVERS.FACULTY, ENDPOINTS.FACULTY_QUESTIONS_BY_STUDENT)}/${studentId}`)
      if (!res.ok) throw new Error('No data found')
      const data = await res.json()
      setQuestions(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [studentId])

  const handleAction = async (id, approve) => {
    try {
      await fetch(`${getApiUrl(SERVERS.FACULTY, ENDPOINTS.FACULTY_APPROVE_QUESTION)}/${id}/approve`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approve, remarks: remarks[id] || '' })
      })
      
      // Update local state to show approval status immediately
      setQuestions(prev => prev.map(q => 
        q.id === id 
          ? { ...q, approval_status: approve ? 'approved' : 'rejected' }
          : q
      ))
      
      console.log(`Question ${id} ${approve ? 'approved' : 'rejected'}`)
    } catch (e) {
      console.error(e)
    }
  }

  // Filter out rejected questions
  const activeQuestions = questions.filter(q => q.approval_status !== 'rejected')

  return (
    <div className="container" style={{ padding: '2rem 0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2>Review Questions for {studentId}</h2>
        <button
          onClick={fetchData}
          disabled={loading}
          style={{
            background: '#007bff',
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

      {activeQuestions.length === 0 ? (
        <div style={{ 
          textAlign: 'center', 
          padding: '2rem',
          color: '#666',
          fontStyle: 'italic'
        }}>
          No pending questions to review.
        </div>
      ) : (
        activeQuestions.map((q) => (
          <div 
            key={q.id} 
            className="card" 
            style={{ 
              marginBottom: '1rem', 
              padding: '1rem',
              borderLeft: q.approval_status === 'approved' 
                ? '4px solid #28a745' 
                : '4px solid transparent',
              // background: q.approval_status === 'approved' 
              //   ? '#f8fff9' 
              //   : 'white'
            }}
          >
            {/* Approval Status Badge */}
            {q.approval_status === 'approved' && (
              <div style={{
                display: 'inline-block',
                background: '#28a745',
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
            
            <div style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>
              {q.domain} {q.service_category ? `• ${q.service_category}` : ''}
            </div>
            
            <div style={{
              padding: '1.5rem',
              borderRadius: '6px',
              marginBottom: '1rem'
            }}>
              <ReactMarkdown>{q.selected_question}</ReactMarkdown>
            </div>

            {/* Remarks Input - Only show for pending questions */}
            {(!q.approval_status || q.approval_status === 'pending') && (
              <input
                className="form-input"
                placeholder="Remarks (optional)"
                style={{ marginRight: '1rem', width: '300px', marginBottom: '1rem' }}
                value={remarks[q.id] || ''}
                onChange={(e) => setRemarks((r) => ({ ...r, [q.id]: e.target.value }))}
              />
            )}

            {/* Show remarks if provided and approved */}
            {q.approval_status === 'approved' && remarks[q.id] && (
              <div style={{ 
                // background: '#e9ecef', 
                padding: '0.5rem', 
                borderRadius: '4px',
                marginBottom: '1rem',
                fontSize: '0.9rem'
              }}>
                <strong>Remarks:</strong> {remarks[q.id]}
              </div>
            )}

            {/* Action Buttons - Only show for pending questions */}
            {(!q.approval_status || q.approval_status === 'pending') ? (
              <div>
                <button
                  className="btn"
                  style={{ 
                    background: 'green', 
                    color: 'white', 
                    marginRight: '0.5rem', 
                    padding: '6px 10px', 
                    borderRadius: '4px', 
                    border: 'none',
                    cursor: 'pointer'
                  }}
                  onClick={() => handleAction(q.id, true)}
                >
                  Approve
                </button>

                <button
                  className="btn"
                  style={{ 
                    background: '#dc3545', 
                    color: 'white', 
                    padding: '6px 10px', 
                    borderRadius: '4px', 
                    border: 'none',
                    cursor: 'pointer'
                  }}
                  onClick={() => handleAction(q.id, false)}
                >
                  Reject
                </button>
              </div>
            ) : (
              <div style={{ 
                color: q.approval_status === 'approved' ? '#28a745' : '#dc3545',
                fontWeight: 'bold',
                fontSize: '0.9rem'
              }}>
                {q.approval_status === 'approved' ? 'Approved' : 'Rejected'}
              </div>
            )}
          </div>
        ))
      )}

      <button
        onClick={() => navigate(-1)}
        style={{ 
          marginTop: '1rem', 
          background: '#6c757d', 
          color: 'white',
          padding: '8px 16px', 
          borderRadius: '5px', 
          border: 'none',
          cursor: 'pointer'
        }}
      >
        ← Back
      </button>
    </div>
  )
}

export default FacultyReviewPage