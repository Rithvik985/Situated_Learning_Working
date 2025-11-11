import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getApiUrl, SERVERS, ENDPOINTS } from '../config/api'

const FacultyReviewPage = () => {
  const { studentId } = useParams()
  const [questions, setQuestions] = useState([])
  const [remarks, setRemarks] = useState({})
  const navigate = useNavigate()

  const fetchData = async () => {
    try {
    const res = await fetch(`${getApiUrl(SERVERS.FACULTY, ENDPOINTS.FACULTY_QUESTIONS_BY_STUDENT)}/${studentId}`)

      if (!res.ok) throw new Error('No data found')
      const data = await res.json()
      setQuestions(data)
    } catch (e) {
      console.error(e)
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
      await fetchData()
      console.log(`Question ${id} ${approve ? 'approved' : 'rejected'}`)
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <div className="container" style={{ padding: '2rem 0' }}>
      <h2 style={{ marginBottom: '1rem' }}>Review Questions for {studentId}</h2>

      {questions.length === 0 ? (
        <div>No questions found.</div>
      ) : (
        questions.map((q) => (
          <div key={q.id} className="card" style={{ marginBottom: '1rem', padding: '1rem' }}>
            <div style={{ fontWeight: 'bold' }}>{q.domain} {q.service_category ? `• ${q.service_category}` : ''}</div>
            <p style={{ marginTop: '0.5rem' }}>{q.selected_question}</p>

            <input
              className="form-input"
              placeholder="Remarks (optional)"
              style={{ marginRight: '1rem', width: '300px' }}
              value={remarks[q.id] || ''}
              onChange={(e) => setRemarks((r) => ({ ...r, [q.id]: e.target.value }))}
            />

            <button
              className="btn"
              style={{ background: 'green', color: 'white', marginRight: '0.5rem', padding: '6px 10px', borderRadius: '4px', border: 'none' }}
              onClick={() => handleAction(q.id, true)}
            >
              Approve
            </button>

            <button
              className="btn"
              style={{ background: 'gray', color: 'white', padding: '6px 10px', borderRadius: '4px', border: 'none' }}
              onClick={() => handleAction(q.id, false)}
            >
              Reject
            </button>
          </div>
        ))
      )}

      <button
        onClick={() => navigate(-1)}
        style={{ marginTop: '1rem', background: '#ccc', padding: '8px 16px', borderRadius: '5px', border: 'none' }}
      >
        ← Back
      </button>
    </div>
  )
}

export default FacultyReviewPage
