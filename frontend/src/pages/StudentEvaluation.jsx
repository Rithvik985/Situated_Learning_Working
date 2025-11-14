import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown'; 
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faChartLine, faCheckCircle, faSync, 
  faExclamationTriangle, faLightbulb,
  faChevronLeft, faClipboardCheck,
  faUpload
} from '@fortawesome/free-solid-svg-icons';
import { getApiUrl, getBaseUrl, SERVERS, ENDPOINTS } from '../config/api';
import { useLocation, useNavigate } from 'react-router-dom';
import { useNotifications } from '../hooks/useNotifications';
import NotificationModal from '../components/NotificationModal';

const StudentEvaluation = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { notifications, showNotification, removeNotification } = useNotifications();
  
  // Initialize state from navigation if available - FIX THIS
  const [submission, setSubmission] = useState(location.state?.submissionContent || '');
  const [studentId, setStudentId] = useState(location.state?.studentId || '');
  const [savedAssignments, setSavedAssignments] = useState([]);
  const [selectedAssignment, setSelectedAssignment] = useState(location.state?.selectedAssignment || null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [submissionId, setSubmissionId] = useState(location.state?.submissionId || null);
  const [submissions, setSubmissions] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [aiDetectionResults, setAiDetectionResults] = useState(null);

  // Handle incoming state from PDF upload - ADD THIS EFFECT
  useEffect(() => {
    if (location.state?.fromUpload) {
      console.log('Received state from upload:', location.state);
      
      if (location.state.selectedAssignment) {
        setSelectedAssignment(location.state.selectedAssignment);
      }
      if (location.state.studentId) {
        setStudentId(location.state.studentId);
      }
      if (location.state.submissionContent) {
        setSubmission(location.state.submissionContent);
      }
      if (location.state.submissionId) {
        setSubmissionId(location.state.submissionId);
      }
      if (location.state.uploadedFiles) {
        console.log('Uploaded files:', location.state.uploadedFiles);
        // You might want to do something with the uploaded files data
      }
      
      // Clear the location state to avoid re-triggering
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  // Load saved assignments and submission history when studentId changes
  useEffect(() => {
    const fetchData = async () => {
      try {
        if (!studentId) return;
        
        // Fetch saved assignments
        const assignmentsRes = await fetch(getApiUrl(SERVERS.STUDENT, ENDPOINTS.LIST_ASSIGNMENTS) + `?student_id=${studentId}`);
        if (!assignmentsRes.ok) throw new Error('Failed to fetch assignments');
        const assignmentsData = await assignmentsRes.json();
        setSavedAssignments(assignmentsData);

        // If we have a selectedAssignment from navigation but not in local state, find it
        if (location.state?.selectedAssignment && !selectedAssignment) {
          const navAssignment = assignmentsData.find(a => a.id === location.state.selectedAssignment.id);
          if (navAssignment) {
            setSelectedAssignment(navAssignment);
          }
        }

        // Fetch submission history
        const submissionsRes = await fetch(getApiUrl(SERVERS.STUDENT, ENDPOINTS.STUDENT_MY_SUBMISSIONS) + `/${studentId}`);
        if (!submissionsRes.ok) throw new Error('Failed to fetch submissions');
        const submissionsData = await submissionsRes.json();
        setSubmissions(submissionsData);
      } catch (e) {
        setError(e.message);
      }
    };
    fetchData();
  }, [studentId, location.state, selectedAssignment]);


  const submitForAnalysis = async () => {
    setLoading(true);
    setError(null);
    showNotification('📊 Analyzing your submission...', 'info', 0);
    try {
      // Prepare payload based on whether we have file upload or manual text
      const payload = submissionId ? {
        student_id: studentId,
        assignment_id: selectedAssignment.id,
        submission_id: submissionId,  // Use existing submission from file upload
        content: submission || ''      // Include manual text if any, but extracted_text will be used
      } : {
        student_id: studentId,
        assignment_id: selectedAssignment.id,
        content: submission            // Manual text input
      };

      const res = await fetch(getApiUrl(SERVERS.STUDENT, ENDPOINTS.STUDENT_ANALYZE), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Failed to analyze submission');
      }
      
      const data = await res.json();
      console.log("SWOT analysis response:", data);

      setAnalysis(data);
      
      // Update submissionId if this created a new one
      if (data.submission_id && !submissionId) {
        setSubmissionId(data.submission_id);
      }
      
      showNotification('✅ Analysis completed successfully!', 'success');
      
      // Refresh submissions list
      const submissionsRes = await fetch(getApiUrl(SERVERS.STUDENT, ENDPOINTS.STUDENT_MY_SUBMISSIONS) + `/${studentId}`);
      if (submissionsRes.ok) {
        const submissionsData = await submissionsRes.json();
        setSubmissions(submissionsData);
      }
    } catch (e) {
      setError(e.message);
      showNotification(`❌ Analysis failed: ${e.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const submitToFaculty = async (submissionId) => {
    setLoading(true);
    setError(null);
    showNotification('📤 Submitting to faculty...', 'info', 0);
    try {
      console.log("Submitting to faculty with:", { studentId, submissionId });

      const res = await fetch(getApiUrl(SERVERS.STUDENT, ENDPOINTS.STUDENT_SUBMIT_TO_FACULTY), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: studentId,
          submission_id: submissionId
        })
      });

      if (!res.ok) throw new Error('Failed to submit to faculty');
      
      showNotification('✅ Submitted to faculty successfully!', 'success');
      // Refresh submissions list
      const submissionsRes = await fetch(getApiUrl(SERVERS.STUDENT, ENDPOINTS.STUDENT_MY_SUBMISSIONS) + `/${studentId}`);
      if (submissionsRes.ok) {
        const submissionsData = await submissionsRes.json();
        setSubmissions(submissionsData);
      }
    } catch (e) {
      setError(e.message);
      showNotification(`❌ Submission failed: ${e.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ padding: '2rem' }}>
      {/* Notification Modal */}
      <NotificationModal 
        notifications={notifications} 
        onRemove={removeNotification} 
      />

      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem' }}>
          <button 
            className="btn btn-secondary" 
            onClick={() => navigate('/student-workflow')}
            style={{ marginRight: '1rem' }}
          >
            <FontAwesomeIcon icon={faChevronLeft} /> Back to Workflow
          </button>
        </div>
        <div style={{ textAlign: 'center' }}>
          <h1>
            <FontAwesomeIcon icon={faChartLine} style={{ marginRight: '1rem' }} />
            SWOT Analysis Feedback
          </h1>
          <p>Submit your work for analysis and receive detailed SWOT feedback</p>
        </div>
      </div>

      {error && (
        <div className="card error" style={{ marginBottom: '1rem', color: '#dc3545' }}>
          <FontAwesomeIcon icon={faExclamationTriangle} /> {error}
        </div>
      )}

      {/* Student ID Input */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <h3>Enter Student ID</h3>
        <input
          type="text"
          className="form-input"
          value={studentId}
          onChange={(e) => setStudentId(e.target.value)}
          placeholder="Enter your student ID..."
          style={{ marginBottom: '1rem' }}
        />
      </div>

      {/* Assignment Selection */}
      {studentId && savedAssignments.length > 0 && (
        <div className="card" style={{ marginBottom: '2rem' }}>
          <h3>Select Assignment</h3>
          <select
            className="form-input"
            value={selectedAssignment?.id || ''}
            onChange={(e) => setSelectedAssignment(savedAssignments.find(a => a.id === e.target.value))}
            style={{ marginBottom: '1rem' }}
          >
            <option value="">Select an assignment...</option>
            {savedAssignments.map(assignment => (
              <option key={assignment.id} value={assignment.id}>
                {assignment.assignment_name} - {assignment.course_name}
              </option>
            ))}
          </select>
          {selectedAssignment && (
            <div className="card" style={{marginBottom: '1rem' }}>
              <h4>{selectedAssignment.title}</h4>
                          <div style={{
                            padding: '1.5rem',
                            borderRadius: '6px',
                            marginBottom: '1rem'
                          }}>
                            <ReactMarkdown>{selectedAssignment.description}</ReactMarkdown>
                          </div>
              {/* <p>{selectedAssignment.description}</p> */}
            </div>
          )}
        </div>
      )}

      {/* Submission Input */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <h3>Your Submission</h3>
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
          <button
            className="btn btn-secondary"
            onClick={() => navigate('/student-pdf-upload', {
              state: {
                studentId,
                selectedAssignment
              }
            })}
            disabled={!selectedAssignment || !studentId}
          >
            <FontAwesomeIcon icon={faUpload} /> Upload PDF
          </button>
        </div>
        <p style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>
          Or type your submission directly:
        </p>
        <textarea
          className="form-input"
          value={submission}
          onChange={(e) => setSubmission(e.target.value)}
          placeholder="Enter your submission here..."
          rows={10}
          style={{ marginBottom: '1rem' }}
        />
        <button 
          className="btn btn-primary"
          onClick={submitForAnalysis}
          disabled={loading || !submission.trim() || !selectedAssignment || !studentId}
        >
            
          {loading ? (
            <>
              <FontAwesomeIcon icon={faSync} spin /> Analyzing...
            </>
          ) : (
            <>
              <FontAwesomeIcon icon={faLightbulb} /> Get SWOT Analysis
            </>
          )}
        </button>
      </div>

      {analysis && (
        <div className="card">
          <div className="grid" style={{ gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))' }}>
            <div className="card">
              <h4>Strengths</h4>
              <ul>
                {analysis.strengths.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
            
            <div className="card">
              <h4>Weaknesses</h4>
              <ul>
                {analysis.weaknesses.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
            
            <div className="card">
              <h4>Opportunities</h4>
              <ul>
                {analysis.opportunities.map((o, i) => (
                  <li key={i}>{o}</li>
                ))}
              </ul>
            </div>
            
            <div className="card">
              <h4>Threats</h4>
              <ul>
                {analysis.threats.map((t, i) => (
                  <li key={i}>{t}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="card" style={{ marginTop: '1rem' }}>
            <h4>Suggestions for Improvement</h4>
            <ul>
              {analysis.suggestions.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </div>

          <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
            <button 
              className="btn btn-primary"
              onClick={() => submitToFaculty(submissionId)}
              disabled={loading}
            >
              <FontAwesomeIcon icon={faClipboardCheck} /> Submit to Faculty
            </button>
          </div>
        </div>
      )}

      {/* Submission History */}
      <div className="card" style={{ 
        marginTop: '2rem',
        backgroundColor: '#34495e',
        color: '#ecf0f1',
        border: '1px solid #2c3e50'
      }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          marginBottom: '1rem' 
        }}>
          <h3 style={{ color: '#ecf0f1' }}>Submission History</h3>
          <button 
            className="btn btn-secondary"
            onClick={() => setShowHistory(!showHistory)}
            style={{
              backgroundColor: '#7f8c8d',
              color: 'white',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            {showHistory ? 'Hide History' : 'Show History'}
          </button>
        </div>

        {showHistory && submissions.map((sub) => (
          <div key={sub.id} className="card" style={{ 
            marginBottom: '1rem',
            backgroundColor: '#2c3e50',
            color: '#ecf0f1',
            border: '1px solid #34495e',
            padding: '1rem',
            borderRadius: '6px'
          }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              color: '#ecf0f1'
            }}>
              <div>
                <strong style={{ color: '#f39c12' }}>Submitted:</strong> 
                <span style={{ marginLeft: '0.5rem', color: '#ecf0f1' }}>
                  {new Date(sub.submission_date).toLocaleDateString()}
                </span>
                <br />
                <strong style={{ color: '#f39c12' }}>Status:</strong> 
                <span style={{ marginLeft: '0.5rem', color: '#ecf0f1' }}>
                  {sub.status}
                </span>
              </div>
              {sub.status === 'draft' && (
                <button 
                  className="btn btn-primary"
                  onClick={() => submitToFaculty(sub.id)}
                  disabled={loading}
                >
                  Submit to Faculty
                </button>
              )}
            </div>

            {sub.faculty_evaluation && (
              <div className="card" style={{ 
                marginTop: '1rem',
                backgroundColor: '#34495e',
                color: '#ecf0f1',
                border: '1px solid #2c3e50'
              }}>
                <h4 style={{ color: '#ecf0f1', marginBottom: '1rem' }}>Faculty Evaluation</h4>
                <div style={{ color: '#ecf0f1' }}>
                  <div style={{ marginBottom: '1rem' }}>
                    <strong style={{ color: '#f39c12' }}>Score:</strong> 
                    <span style={{ color: '#ecf0f1', marginLeft: '0.5rem' }}>
                      {
                        Array.isArray(sub.faculty_evaluation.rubric_scores)
                          ? sub.faculty_evaluation.rubric_scores.reduce((sum, item) => sum + (item.score || 0), 0)
                          : sub.evaluation_score || 0
                      } / {
                        Array.isArray(sub.faculty_evaluation.rubric_scores)
                          ? sub.faculty_evaluation.rubric_scores.reduce((sum, item) => sum + (item.max_score || 0), 0)
                          : 72
                      }
                    </span>
                  </div>
                  <div style={{ marginBottom: '1rem' }}>
                    <strong style={{ color: '#f39c12' }}>Comments:</strong>
                    <div style={{
                      padding: '1.5rem',
                      borderRadius: '6px',
                      marginTop: '0.5rem',
                      backgroundColor: '#2c3e50',
                      color: '#ecf0f1',
                      border: '1px solid #34495e'
                    }}>
                      <ReactMarkdown>{sub.faculty_evaluation.comments}</ReactMarkdown>
                    </div>
                  </div>
                  
                  {/* Display detailed rubric scores */}
                  {Array.isArray(sub.faculty_evaluation.rubric_scores) && sub.faculty_evaluation.rubric_scores.length > 0 && (
                    <div style={{ marginTop: '1rem' }}>
                      <strong style={{ color: '#f39c12' }}>Detailed Scores:</strong>
                      {sub.faculty_evaluation.rubric_scores.map((category, idx) => (
                        <div key={idx} style={{ 
                          marginTop: '0.5rem', 
                          padding: '0.75rem',
                          background: '#2c3e50',
                          borderRadius: '4px',
                          border: '1px solid #34495e',
                          color: '#ecf0f1'
                        }}>
                          <div style={{ color: '#ecf0f1' }}>
                            <strong style={{ color: '#f39c12' }}>{category.category}:</strong> 
                            <span style={{ marginLeft: '0.5rem' }}>
                              {category.score} / {category.max_score} ({category.percentage}%)
                            </span>
                          </div>
                          {category.feedback && (
                            <div style={{ 
                              marginTop: '0.5rem', 
                              fontSize: '0.9em', 
                              color: '#bdc3c7',
                              padding: '0.5rem',
                              backgroundColor: '#1a252f',
                              borderRadius: '4px'
                            }}>
                              <ReactMarkdown>{category.feedback}</ReactMarkdown>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {sub.swot_analyses && sub.swot_analyses.length > 0 && (
              <div style={{ marginTop: '1rem' }}>
                <h4 style={{ color: '#ecf0f1' }}>SWOT Analyses ({sub.swot_analyses.length})</h4>
                {sub.swot_analyses.map((swot, index) => (
                  <div key={index} className="card" style={{ 
                    marginTop: '0.5rem',
                    backgroundColor: '#34495e',
                    color: '#ecf0f1',
                    border: '1px solid #2c3e50',
                    padding: '1rem',
                    borderRadius: '6px'
                  }}>
                    <strong style={{ color: '#f39c12' }}>
                      Analysis {index + 1}
                    </strong> 
                    <span style={{ color: '#bdc3c7', marginLeft: '0.5rem' }}>
                      - {new Date(swot.analysis_date).toLocaleDateString()}
                    </span>
                    <div className="grid" style={{ 
                      gap: '0.5rem', 
                      marginTop: '0.5rem',
                      color: '#ecf0f1'
                    }}>
                      <div>Strengths: {swot.strengths.length}</div>
                      <div>Weaknesses: {swot.weaknesses.length}</div>
                      <div>Opportunities: {swot.opportunities.length}</div>
                      <div>Threats: {swot.threats.length}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default StudentEvaluation;