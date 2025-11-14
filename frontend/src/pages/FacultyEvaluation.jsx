import React, { useState, useEffect } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import axios from "axios";
import {
  faClipboardCheck,
  faCheckCircle,
  faExclamationTriangle,
  faUser,
  faRobot,
  faSpinner,
  faMagnifyingGlass,
  faSearch,
  faPlus,
  faMinus
} from "@fortawesome/free-solid-svg-icons";
import { getApiUrl, getBaseUrl, SERVERS, ENDPOINTS } from "../config/api";

const FacultyEvaluation = () => {
  const [submissions, setSubmissions] = useState([]);
  const [selectedSubmission, setSelectedSubmission] = useState(null);
  const [evaluationResult, setEvaluationResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [aiDetectionResults, setAiDetectionResults] = useState(null);
  const [courseFilter, setCourseFilter] = useState('all');
  const [courses, setCourses] = useState([]);

  // ✅ Fetch courses for filter
  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const res = await fetch(getApiUrl(SERVERS.FACULTY, "COURSES"));
        if (res.ok) {
          const data = await res.json();
          setCourses(data);
        }
      } catch (e) {
        console.error("Error loading courses:", e);
      }
    };
    fetchCourses();
  }, []);

  // ✅ Fetch pending submissions (basic info)
  useEffect(() => {
    const fetchSubmissions = async () => {
      try {
        const res = await fetch(getApiUrl(SERVERS.FACULTY, "PENDING_SUBMISSIONS"));
        if (!res.ok) throw new Error("Failed to fetch pending submissions");
        const data = await res.json();
        console.log(data);
        setSubmissions(data);
      } catch (e) {
        setError("Error loading submissions: " + e.message);
      }
    };
    fetchSubmissions();
  }, []);

  // ✅ Fetch detailed submission when one is selected
  useEffect(() => {
    const fetchSubmissionDetails = async () => {
      if (!selectedSubmission) return;
      
      try {
        const res = await fetch(`${getApiUrl(SERVERS.FACULTY, "GET_SUBMISSION")}/${selectedSubmission.id}`);
        if (!res.ok) throw new Error("Failed to fetch submission details");
        const detailedSubmission = await res.json();
        
        // Update selected submission with full details
        setSelectedSubmission(detailedSubmission);
      } catch (e) {
        setError("Error loading submission details: " + e.message);
      }
    };
    
    fetchSubmissionDetails();
  }, [selectedSubmission?.id]); // Only fetch when submission ID changes

  // Handle updates to individual criterion scores
  const handleCriterionScoreUpdate = (dimensionIndex, criterionIndex, delta) => {
    if (!evaluationResult) return;
    setError(null);
    setSuccess(false);

    setEvaluationResult(prev => {
      if (!prev) return prev;
      
      const updated = { ...prev };
      const dimensions = [...updated.criterion_feedback];
      
      // Update the specific criterion score
      const dimension = { ...dimensions[dimensionIndex] };
      const criteria = [...dimension.question_results];
      const criterion = { ...criteria[criterionIndex] };
      
      // Update score with 0.25 increments, clamped between 1-4
      const newScore = Math.max(1, Math.min(4, Number(criterion.score || 1) + delta));
      criterion.score = Math.round(newScore * 100) / 100; // Round to 2 decimal places
      criteria[criterionIndex] = criterion;
      
      // Update dimension with new criteria
      dimension.question_results = criteria;
      
      // Recalculate dimension score (sum of all criteria in this dimension)
      dimension.score = criteria.reduce((sum, crit) => sum + Number(crit.score || 0), 0);
      dimension.max_score = criteria.length * 4; // Should be 12 for 3 criteria
      dimension.percentage = (dimension.score / dimension.max_score) * 100;
      
      // Update dimensions array
      dimensions[dimensionIndex] = dimension;
      
      // Recalculate overall score (sum of all dimension scores)
      updated.overall_score = dimensions.reduce((sum, dim) => sum + Number(dim.score || 0), 0);
      updated.criterion_feedback = dimensions;
      
      return updated;
    });
  };

  // Handle evaluation finalization
  const handleFinalizeEvaluation = async () => {
    if (!selectedSubmission) return;
    setLoading(true);
    setError(null);

    try {
      // Prepare per-criterion payload to send to backend: flatten as "Dimension > Criterion" => score
      const flatScores = {};
      if (evaluationResult && evaluationResult.criterion_feedback) {
        evaluationResult.criterion_feedback.forEach(dim => {
          (dim.question_results || []).forEach(q => {
            const key = `${dim.category} > ${q.question}`;
            flatScores[key] = Number(q.score || 0);
          });
        });
      }

      // Use POST evaluate endpoint which accepts criteria_scores dict
      try {
        const evalUrl = `${getApiUrl(SERVERS.FACULTY, 'GET_SUBMISSION')}/${selectedSubmission.id}/evaluate`;
        console.log('Finalizing - posting evaluation to:', evalUrl, { criteria_scores: flatScores });

        const postRes = await fetch(evalUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            submission_id: selectedSubmission.id, 
            criteria_scores: flatScores, 
            feedback: evaluationResult?.overall_feedback || '' 
          }),
          credentials: 'include'
        });

        if (!postRes.ok) {
          const errBody = await postRes.json().catch(() => ({}));
          throw new Error(errBody.detail || 'Failed to save evaluation');
        }
      } catch (err) {
        throw new Error('Failed to save updated scores before finalizing: ' + err.message);
      }

      // Now call finalize endpoint with the final marks
      const finalMarks = Math.max(18, Math.min(72, Number(evaluationResult?.overall_score || 0)));
      const finalizeUrl = getApiUrl(SERVERS.FACULTY, 'FINALIZE');
      console.log('Calling finalize endpoint:', finalizeUrl, { 
        submission_id: selectedSubmission.id, 
        final_marks: finalMarks 
      });

      const finRes = await fetch(finalizeUrl, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          submission_id: selectedSubmission.id, 
          final_marks: finalMarks, 
          final_feedback: evaluationResult?.overall_feedback || '' 
        }),
        credentials: 'include'
      });

      if (!finRes.ok) {
        const err = await finRes.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to finalize evaluation');
      }

      // Update evaluation result to show finalized state
      setEvaluationResult(prev => ({
        ...prev,
        is_finalized: true,
        overall_score: finalMarks
      }));
      setSuccess(true);
    } catch (e) {
      console.error("Score update error:", e);
      setError("Failed to update score: " + (e.message || "Unknown error"));
    } finally {
      setLoading(false);
    }
  };

  // Detect AI generated content
  const detectAIContent = async () => {
    if (!selectedSubmission) return;
    
    setLoading(true);
    setError(null);
    setAiDetectionResults(null);
    
    try {
      const response = await axios.post(
        `${getBaseUrl(SERVERS.FACULTY)}/submissions/${selectedSubmission.id}/detect-ai`,
        { submission_id: selectedSubmission.id }
      );
      if (response.data) {
        setAiDetectionResults(response.data);
        setSuccess(true);
      } else {
        throw new Error("No analysis results received");
      }
    } catch (err) {
      console.error("AI detection error:", err);
      setError(
        err.response?.data?.detail || 
        err.message || 
        "Failed to analyze submission for AI content"
      );
      setAiDetectionResults(null);
    } finally {
      setLoading(false);
    }
  };

  // ✅ Trigger auto-evaluation (LLM-based)
  const evaluateSubmission = async () => {
    if (!selectedSubmission) return;
    setLoading(true);
    setError(null);
    setSuccess(false);
    setEvaluationResult(null);

    try {
      // Build dynamic evaluation URL correctly
      const baseUrl = getApiUrl(SERVERS.FACULTY, "EVALUATE_SUBMISSION");
      const evalUrl = `${baseUrl}/${selectedSubmission.id}/evaluate`;

      const res = await fetch(evalUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          faculty_id: "f20220162", // TODO: replace with actual faculty ID/email from auth
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Evaluation failed");
      }

      const data = await res.json();
      console.log('Auto-eval response:', data);

      // Normalize response to internal shape used by this component
      const dimsSource = data.dimensions || data.criterion_feedback || [];
      const normalized = {
        submission_id: data.submission_id || selectedSubmission.id,
        overall_score: data.overall_score || 0,
        overall_feedback: data.overall_feedback || '',
        is_finalized: false,
        criterion_feedback: dimsSource.map(dim => {
          const question_results = dim.question_results
            ? dim.question_results.map(q => ({ 
                question: q.question || q.name, 
                score: q.score, 
                reasoning: q.feedback || q.reasoning 
              }))
            : (dim.criteria || []).map(c => ({ 
                question: c.name, 
                score: c.score, 
                reasoning: c.feedback 
              }));

          return {
            category: dim.name || dim.category,
            score: dim.dimension_score || dim.score || 0,
            max_score: dim.dimension_max_score || dim.max_score || 12,
            percentage: dim.dimension_percentage || dim.percentage || 0,
            feedback: dim.dimension_feedback || dim.feedback || '',
            question_results: question_results
          };
        })
      };

      setEvaluationResult(normalized);
      setSuccess(true);

      // Remove evaluated submission from pending list
      setSubmissions((prev) => prev.filter((s) => s.id !== selectedSubmission.id));
    } catch (e) {
      setError("Evaluation failed: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ padding: "2rem" }}>
      <div style={{ marginBottom: "2rem", textAlign: "center" }}>
        <h1>
          <FontAwesomeIcon icon={faClipboardCheck} style={{ marginRight: "1rem" }} />
          Faculty Evaluation
        </h1>
        <p>Automatically evaluate student submissions using LLM-generated rubric scoring</p>
      </div>

      {/* ✅ Status Messages */}
      {error && (
        <div className="card error" style={{ marginBottom: "1rem", color: "#dc3545" }}>
          <FontAwesomeIcon icon={faExclamationTriangle} /> {error}
        </div>
      )}

      {success && (
        <div className="card success" style={{ marginBottom: "1rem", color: "#28a745" }}>
          <FontAwesomeIcon icon={faCheckCircle} /> Evaluation completed successfully!
        </div>
      )}

      <div className="grid" style={{ gap: "2rem", gridTemplateColumns: "300px 1fr" }}>
        {/* ✅ Pending Submissions List */}
        <div className="card">
          <h3>Pending Evaluations</h3>
          
          {/* Course Filter */}
          <div style={{ marginBottom: "1rem" }}>
            <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "600" }}>
              Filter by Course:
            </label>
            <select
              value={courseFilter}
              onChange={(e) => setCourseFilter(e.target.value)}
              style={{
                width: "100%",
                padding: "0.5rem",
                borderRadius: "4px",
                border: "1px solid #ccc",
                fontSize: "0.9rem"
              }}
            >
              <option value="all">All Courses</option>
              {[...new Set(submissions.map(s => s.course_name).filter(Boolean))].map((courseName) => (
                <option key={courseName} value={courseName}>
                  {courseName}
                </option>
              ))}
            </select>
          </div>

          <div style={{ maxHeight: "600px", overflowY: "auto" }}>
            {submissions
              .filter(sub => courseFilter === 'all' || sub.course_name === courseFilter)
              .map((submission) => (
              <div
                key={submission.id}
                className={`card clickable ${selectedSubmission?.id === submission.id ? "selected" : ""}`}
                onClick={() => {
                  setSelectedSubmission(submission);
                  setEvaluationResult(null);
                  setAiDetectionResults(null);
                  setSuccess(false);
                }}
                style={{ marginBottom: "0.5rem", cursor: "pointer" }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <FontAwesomeIcon icon={faUser} />
                  <div style={{ flex: 1 }}>
                    <div>{submission.student_id}</div>
                    {submission.course_name && (
                      <div style={{ fontSize: "0.85em", color: "var(--text-secondary)", marginTop: "0.25rem" }}>
                        {submission.course_name}
                      </div>
                    )}
                    <small style={{ color: "var(--text-secondary)" }}>
                      {new Date(submission.submission_date || submission.created_at).toLocaleDateString()}
                    </small>
                  </div>
                </div>
              </div>
            ))}
            {submissions.filter(sub => courseFilter === 'all' || sub.course_name === courseFilter).length === 0 && (
              <div style={{ textAlign: "center", color: "var(--text-secondary)", padding: "1rem" }}>
                {courseFilter === 'all' 
                  ? 'No pending evaluations' 
                  : `No pending evaluations for ${courseFilter}`}
              </div>
            )}
          </div>
        </div>

        {/* ✅ Evaluation Panel */}
        {selectedSubmission && (
          <div>
            {/* ✅ Student Submission Content - DISPLAYED FIRST */}
            <div className="card" style={{ marginBottom: "1rem" }}>
              <h3>
                <FontAwesomeIcon icon={faUser} style={{ marginRight: "0.5rem" }} />
                Student Submission
              </h3>
              
              {/* Submission Metadata */}
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: '1fr 1fr', 
                gap: '1rem', 
                marginBottom: '1rem',
                padding: '1rem',
                // backgroundColor: '#f8f9fa',
                borderRadius: '4px'
              }}>
                <div>
                  <strong>Student ID:</strong> {selectedSubmission.student_id}
                </div>
                <div>
                  <strong>Submitted:</strong> {new Date(selectedSubmission.submission_date).toLocaleDateString()}
                </div>
                {selectedSubmission.assignment_details && (
                  <>
                    <div>
                      <strong>Assignment:</strong> {selectedSubmission.assignment_details.title}
                    </div>
                    <div>
                      <strong>Course:</strong> {selectedSubmission.assignment_details.course_name}
                    </div>
                  </>
                )}
              </div>

              {/* Submission Content */}
              <div style={{
                // border: '1px solid #e9ecef',
                borderRadius: '4px',
                padding: '1rem',
                // backgroundColor: '#fff',
                maxHeight: '400px',
                overflowY: 'auto',
                whiteSpace: 'pre-wrap',
                lineHeight: '1.5',
                fontSize: '0.95rem'
              }}>
                {selectedSubmission.content || 'No submission content available.'}
              </div>
            </div>

            {/* Analysis Panel */}
            <div className="card" style={{ marginBottom: "1rem" }}>
              <h3>Submission Analysis</h3>
              <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
                <button
                  className="btn btn-primary"
                  onClick={evaluateSubmission}
                  disabled={loading}
                  style={{ flex: 1 }}
                >
                  {loading ? (
                    <>
                      <FontAwesomeIcon icon={faSpinner} spin /> Evaluating...
                    </>
                  ) : (
                    <>
                      <FontAwesomeIcon icon={faRobot} /> Run AI Evaluation
                    </>
                  )}
                </button>
                <button
                  className="btn btn-warning"
                  onClick={detectAIContent}
                  disabled={loading}
                  style={{ flex: 1 }}
                >
                  {loading ? (
                    <>
                      <FontAwesomeIcon icon={faSpinner} spin /> Detecting...
                    </>
                  ) : (
                    <>
                      <FontAwesomeIcon icon={faMagnifyingGlass} /> Detect AI Content
                    </>
                  )}
                </button>
              </div>
            </div>
            
            {aiDetectionResults && (
              <div className="card" style={{ marginBottom: "1rem" }}>
                <h3>
                  <FontAwesomeIcon icon={faSearch} /> AI Content Detection Results
                </h3>
                <div className="alert" style={{
                  backgroundColor: (aiDetectionResults.ai_detection_results?.is_likely_ai || false) ? '#ffc107' : '#28a745',
                  color: '#000',
                  padding: '1rem',
                  borderRadius: '4px',
                  marginBottom: '1rem'
                }}>
                  <strong>Risk Level:</strong> {aiDetectionResults.risk_assessment?.risk_level || 'Unknown'}
                  <div>
                    <strong>AI Probability:</strong> {
                      aiDetectionResults.ai_detection_results?.ai_probability !== undefined
                        ? (aiDetectionResults.ai_detection_results.ai_probability * 100).toFixed(1)
                        : 'N/A'
                    }%
                  </div>
                </div>

                <h4>Recommendations:</h4>
                <ul style={{ paddingLeft: '1.5rem' }}>
                  {(aiDetectionResults.recommendations || []).map((rec, idx) => (
                    <li key={idx}>{rec}</li>
                  ))}
                </ul>

                <div style={{ marginTop: '1rem' }}>
                  <h4>Submission Statistics:</h4>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div>
                      <strong>Text Length:</strong> {aiDetectionResults.submission_stats?.text_length || 'N/A'}
                    </div>
                    <div>
                      <strong>Word Count:</strong> {aiDetectionResults.submission_stats?.word_count || 'N/A'}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* ✅ Show results if evaluation completed */}
            {evaluationResult && (
              <div className="card">
                <div style={{ marginBottom: '1rem' }}>
                  <h3>Evaluation Results</h3>
                  <div style={{ padding: '1rem', borderRadius: '4px', marginBottom: '1rem' }}>
                    <h4 style={{ margin: '0 0 0.5rem 0'}}>
                      Overall Score: <strong>{evaluationResult.overall_score?.toFixed(2)}/72</strong>
                    </h4>
                    <p style={{ margin: 0}}>
                      {evaluationResult.overall_feedback}
                    </p>
                  </div>
                </div>

                {/* Dimensions with editable criteria */}
                <h4>Rubric Dimensions</h4>
                {evaluationResult.criterion_feedback?.map((dimension, dimIndex) => (
                  <div 
                    key={dimIndex} 
                    className="card" 
                    style={{ 
                      marginBottom: "1.5rem", 
                    }}
                  >
                    {/* Dimension Header */}
                    <div style={{ 
                      display: "flex", 
                      justifyContent: "space-between", 
                      alignItems: "center",
                      padding: "1rem",
                    }}>
                      <div>
                        <strong style={{ fontSize: '1.1em' }}>{dimension.category}</strong>
                        <div style={{ color: "var(--text-secondary)", fontSize: "0.9em", marginTop: '0.25rem' }}>
                          {dimension.feedback}
                        </div>
                      </div>
                      <div style={{ 
                        display: "flex", 
                        alignItems: "center", 
                        gap: "0.5rem",
                        padding: '0.5rem 1rem',
                        borderRadius: '4px',
                      }}>
                        <span style={{ 
                          fontWeight: "bold", 
                          fontSize: '1.1em',
                          minWidth: "5rem", 
                          textAlign: "center" 
                        }}>
                          {dimension.score?.toFixed(2)}/{dimension.max_score}
                        </span>
                      </div>
                    </div>

                    {/* Individual Criteria */}
                    <div style={{ padding: "1rem" }}>
                      <strong style={{ display: 'block', marginBottom: '0.75rem'}}>
                        Criteria Breakdown:
                      </strong>
                      {dimension.question_results?.map((criterion, critIndex) => (
                        <div 
                          key={critIndex} 
                          style={{ 
                            display: "flex", 
                            justifyContent: "space-between", 
                            alignItems: "flex-start",
                            padding: "0.75rem",
                            marginBottom: "0.5rem",
                            borderRadius: '4px',
                          }}
                        >
                          <div style={{ flex: 1, marginRight: '1rem' }}>
                            <div style={{ fontWeight: '500', marginBottom: '0.25rem' }}>
                              {criterion.question}
                            </div>
                            <div style={{ 
                              color: "var(--text-secondary)", 
                              fontSize: "0.85em",
                              lineHeight: '1.4'
                            }}>
                              {criterion.reasoning}
                            </div>
                          </div>
                          
                          <div style={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            gap: '0.75rem',
                            minWidth: '140px'
                          }}>
                            <button
                              className="btn btn-sm"
                              onClick={() => handleCriterionScoreUpdate(dimIndex, critIndex, -0.25)}
                              disabled={criterion.score <= 1}
                              style={{
                                padding: '0.375rem 0.75rem',
                                background: criterion.score <= 1 ? '#6c757d' : '#dc3545',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: criterion.score <= 1 ? 'not-allowed' : 'pointer'
                              }}
                            >
                              <FontAwesomeIcon icon={faMinus} />
                            </button>
                            
                            <span style={{ 
                              minWidth: "3.5rem", 
                              textAlign: "center", 
                              fontWeight: "bold",
                              fontSize: '1em',
                              padding: '0.375rem 0.75rem',
                              borderRadius: '4px',
                            }}>
                              {Number(criterion.score).toFixed(2)}/4
                            </span>
                            
                            <button
                              className="btn btn-sm"
                              onClick={() => handleCriterionScoreUpdate(dimIndex, critIndex, 0.25)}
                              disabled={criterion.score >= 4}
                              style={{
                                padding: '0.375rem 0.75rem',
                                background: criterion.score >= 4 ? '#6c757d' : '#28a745',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: criterion.score >= 4 ? 'not-allowed' : 'pointer'
                              }}
                            >
                              <FontAwesomeIcon icon={faPlus} />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}

                {/* Finalize Button */}
                <div style={{ 
                  marginTop: "2rem", 
                  paddingTop: "1rem", 
                  display: "flex", 
                  justifyContent: "space-between", 
                  alignItems: "center" 
                }}>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: '70%' }}>
                    <strong>Note:</strong> Adjust criteria scores using +/- buttons. Changes update dimension and overall scores in real-time. Click "Finalize Evaluation" to save all scores to the server.
                  </div>
                  <button
                    className="btn btn-primary"
                    onClick={handleFinalizeEvaluation}
                    disabled={loading || evaluationResult.is_finalized}
                    style={{ 
                      padding: '0.75rem 1.5rem',
                      fontSize: '1rem'
                    }}
                  >
                    {loading ? (
                      <>
                        <FontAwesomeIcon icon={faSpinner} spin /> Finalizing...
                      </>
                    ) : evaluationResult.is_finalized ? (
                      "Evaluation Finalized"
                    ) : (
                      "Finalize Evaluation"
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default FacultyEvaluation;