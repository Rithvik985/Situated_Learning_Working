import React from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { getApiUrl, SERVERS, ENDPOINTS } from '../config/api'
import { 
  faClipboardCheck, 
  faCloudUpload,
  faRobot,
  faEdit,
  faDownload,
  faChevronRight,
  faChevronLeft,
  faSpinner,
  faCheckCircle,
  faExclamationTriangle,
  faPlay,
  faSave,
  faTimes,
  faEye,
  faFilePdf,
  faFileWord,
  faTrash
} from '@fortawesome/free-solid-svg-icons'

const EvaluationSteps = ({ 
  currentStep = 1, 
  setCurrentStep = () => {},
  selectedAssignment = null,
  selectedRubric = null,
  rubrics = [],
  loadingRubrics = false,
  uploadedFiles = [],
  uploadingFiles = false,
  evaluating = false,
  evaluationResults = null,
  setEvaluationResults = () => {},
  editingResults = false,
  facultyReasons = {},
  markStepComplete = () => {},
  completedSteps = new Set(),
  setSelectedRubric = () => {},
  uploadSubmissions = () => {},
  evaluateSubmissions = () => {},
  setEditingResults = () => {},
  setFacultyReasons = () => {},
  showNotification = () => {},
  formatFileSize = (bytes) => `${bytes} bytes`,
  getClassificationBadge = () => null,
  removeFile = () => {},
  getRootProps = () => ({}),
  getInputProps = () => ({}),
  isDragActive
}) => {

  // For PDF upload flow, we're only interested in step 4
  if (currentStep === 4) {
    return (
      <div className="card">
        <h3 style={{ marginBottom: '1.5rem', color: 'var(--primary)' }}>
          <FontAwesomeIcon icon={faCloudUpload} style={{ marginRight: '0.5rem' }} />
          Step 4: Upload Student Submissions
        </h3>
        
        <div style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: 'var(--surface)', borderRadius: '8px' }}>
          <strong>Assignment:</strong> {selectedAssignment.assignment_name} | <strong>Rubric:</strong> {selectedRubric.rubric_name}
        </div>
        
        <p style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>
          Upload up to 5 student submissions (PDF or DOCX format). Files will be processed to extract text using OCR if needed.
        </p>
        
        {/* File Upload Dropzone - Only show if no files uploaded yet */}
        {uploadedFiles.length === 0 && (
          <div 
            {...getRootProps()} 
            className={`dropzone ${isDragActive ? 'active' : ''}`}
            style={{ 
              border: '2px dashed var(--border-color)',
              borderRadius: '8px',
              padding: '2rem',
              textAlign: 'center',
              cursor: 'pointer',
              backgroundColor: isDragActive ? 'var(--surface)' : 'var(--bg-lighter)',
              transition: 'all 0.3s ease'
            }}
          >
            <input {...getInputProps()} />
            <FontAwesomeIcon icon={faCloudUpload} size="3x" style={{ color: 'var(--primary)', marginBottom: '1rem' }} />
            {isDragActive ? (
              <p style={{ fontSize: '1.1rem', color: 'var(--primary)' }}>Drop files here...</p>
            ) : (
              <>
                <p style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>
                  Drag & drop submission files here, or <span style={{ color: 'var(--primary)', textDecoration: 'underline' }}>browse</span>
                </p>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                  PDF and DOCX files supported (max 5 files, 50MB each)
                </p>
              </>
            )}
          </div>
        )}
        
        {/* Uploaded Files List */}
        {uploadedFiles.length > 0 && (
          <div style={{ marginTop: '2rem' }}>
            <h4 style={{ marginBottom: '1rem' }}>
              Uploaded Files ({uploadedFiles.length}/5)
            </h4>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {uploadedFiles.map(fileObj => (
                <div 
                  key={fileObj.id} 
                  className="card"
                  style={{ padding: '1rem' }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                        <FontAwesomeIcon 
                          icon={fileObj.type === 'pdf' ? faFilePdf : faFileWord} 
                          style={{ color: fileObj.type === 'pdf' ? '#d32f2f' : '#1976d2' }}
                        />
                        <strong>{fileObj.name}</strong>
                        <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                          ({formatFileSize(fileObj.size)})
                        </span>
                      </div>
                      
                      {/* Processing Status and Classification */}
                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        {fileObj.processing_status === 'processed' && (
                          <span className="badge" style={{ backgroundColor: '#4caf50', color: 'white' }}>
                            <FontAwesomeIcon icon={faCheckCircle} style={{ marginRight: '0.25rem' }} />
                            Processed
                          </span>
                        )}
                        {fileObj.processing_status === 'failed' && (
                          <span className="badge" style={{ backgroundColor: '#dc3545', color: 'white' }}>
                            <FontAwesomeIcon icon={faExclamationTriangle} style={{ marginRight: '0.25rem' }} />
                            Failed
                          </span>
                        )}
                        {getClassificationBadge(fileObj)}
                      </div>
                      
                      {/* Text Preview */}
                      {fileObj.extracted_text_preview && (
                        <div style={{ 
                          marginTop: '0.5rem',
                          padding: '0.5rem',
                          backgroundColor: 'var(--bg-lighter)',
                          borderRadius: '4px',
                          fontSize: '0.8rem',
                          color: 'var(--text-secondary)',
                          fontFamily: 'monospace',
                          maxHeight: '60px',
                          overflow: 'hidden'
                        }}>
                          <strong>Text Preview:</strong> {fileObj.extracted_text_preview}
                        </div>
                      )}
                    </div>
                    
                    <button
                      className="btn btn-outline btn-sm"
                      onClick={() => removeFile(fileObj.id)}
                      disabled={uploadingFiles}
                      style={{ marginLeft: '1rem' }}
                    >
                      <FontAwesomeIcon icon={faTrash} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
            
            <div style={{ textAlign: 'center', marginTop: '2rem' }}>
              {/* Show different buttons based on processing status */}
              {!completedSteps.has(4) ? (
                <button 
                  className="btn btn-primary btn-lg"
                  onClick={uploadSubmissions}
                  disabled={uploadingFiles || uploadedFiles.length === 0}
                >
                  {uploadingFiles ? (
                    <>
                      <FontAwesomeIcon icon={faSpinner} spin style={{ marginRight: '0.5rem' }} />
                      Processing Files...
                    </>
                  ) : (
                    <>
                      <FontAwesomeIcon icon={faPlay} style={{ marginRight: '0.5rem' }} />
                      Process All Files ({uploadedFiles.length})
                    </>
                  )}
                </button>
              ) : (
                <button 
                  className="btn btn-primary btn-lg"
                  onClick={() => setCurrentStep(5)}
                >
                  Continue to Evaluation
                  <FontAwesomeIcon icon={faChevronRight} style={{ marginLeft: '0.5rem' }} />
                </button>
              )}
            </div>
          </div>
        )}
        
        <div style={{ textAlign: 'center', marginTop: '2rem' }}>
          <button 
            className="btn btn-secondary"
            onClick={() => setCurrentStep(3)}
          >
            <FontAwesomeIcon icon={faChevronLeft} style={{ marginRight: '0.5rem' }} />
            Back to Rubric Selection
          </button>
          
          {uploadedFiles.length > 0 && !completedSteps.has(4) && (
            <span style={{ marginLeft: '1rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              To change files, go back to Step 1 and start over
            </span>
          )}
        </div>
      </div>
    )
  }

  if (currentStep === 5 && completedSteps.has(4)) {
    return (
      <div className="card">
        <h3 style={{ marginBottom: '1.5rem', color: 'var(--primary)' }}>
          <FontAwesomeIcon icon={faRobot} style={{ marginRight: '0.5rem' }} />
          Step 5: AI Evaluation
        </h3>
        
        <div style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: 'var(--surface)', borderRadius: '8px' }}>
          <strong>Ready to evaluate {uploadedFiles.length} submission(s)</strong> against {selectedRubric.rubric_name}
        </div>
        
        {!evaluating && evaluationResults.length === 0 && (
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <FontAwesomeIcon icon={faRobot} size="3x" style={{ color: 'var(--primary)', marginBottom: '1rem' }} />
            <h4>Ready for AI Evaluation</h4>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
              The system will evaluate each submission against the selected rubric using advanced AI analysis.
              This process may take a few minutes depending on the submission length and complexity.
            </p>
            
            <button 
              className="btn btn-primary btn-lg"
              onClick={evaluateSubmissions}
            >
              <FontAwesomeIcon icon={faPlay} style={{ marginRight: '0.5rem' }} />
              Start AI Evaluation
            </button>
          </div>
        )}
        
        {evaluating && (
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <FontAwesomeIcon icon={faSpinner} spin size="3x" style={{ color: 'var(--primary)', marginBottom: '1rem' }} />
            <h4>Evaluating Submissions...</h4>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              AI is analyzing submissions against the rubric criteria...
            </p>
            <div style={{ 
              width: '100%', 
              backgroundColor: 'var(--bg-lighter)', 
              borderRadius: '4px', 
              height: '8px', 
              overflow: 'hidden',
              marginBottom: '1rem'
            }}>
              <div 
                style={{ 
                  width: `${Math.min(100, (evaluationResults.length / uploadedFiles.length) * 100)}%`, 
                  height: '100%', 
                  backgroundColor: 'var(--primary)', 
                  transition: 'width 0.3s ease'
                }}
              />
            </div>
          </div>
        )}
        
        {evaluationResults.length > 0 && (
          <div>
            <h4 style={{ marginBottom: '1rem' }}>Evaluation Results</h4>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {evaluationResults.map((result, index) => (
                <div key={result.submission_id} className="card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                    <div>
                      <h5 style={{ margin: '0 0 0.5rem 0', color: 'var(--primary)' }}>
                        Submission {index + 1}: {uploadedFiles[index]?.name}
                      </h5>
                      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                        <span style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>
                          Score: {result.overall_score.toFixed(1)}/20
                        </span>
                        <span style={{ 
                          color: result.overall_score >= 16 ? '#4caf50' : result.overall_score >= 12 ? '#ff9800' : '#dc3545'
                        }}>
                          ({((result.overall_score / 20) * 100).toFixed(1)}%)
                        </span>
                      </div>
                    </div>
                    
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      {result.flags && result.flags.length > 0 && (
                        <span className="badge" style={{ backgroundColor: '#ff9800', color: 'white' }}>
                          <FontAwesomeIcon icon={faExclamationTriangle} style={{ marginRight: '0.25rem' }} />
                          Flagged
                        </span>
                      )}
                      {result.faculty_reviewed && (
                        <span className="badge" style={{ backgroundColor: '#4caf50', color: 'white' }}>
                          <FontAwesomeIcon icon={faCheckCircle} style={{ marginRight: '0.25rem' }} />
                          Reviewed
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {/* Overall Feedback */}
                  <div style={{ 
                    padding: '1rem',
                    backgroundColor: 'var(--bg-lighter)',
                    borderRadius: '4px',
                    marginBottom: '1rem'
                  }}>
                    <strong>Overall Feedback:</strong>
                    <p style={{ margin: '0.5rem 0 0 0', color: 'var(--text-secondary)' }}>
                      {result.overall_feedback}
                    </p>
                  </div>
                  
                  {/* Criterion-wise Results */}
                  {result.criterion_results && result.criterion_results.length > 0 && (
                    <div>
                      <h6 style={{ marginBottom: '1rem', color: 'var(--primary)' }}>Criterion-wise Performance:</h6>
                      <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(2, 1fr)' }}>
                        {result.criterion_results.map((criterion, criterionIndex) => (
                          <div key={criterionIndex} className="card" style={{ padding: '1rem', backgroundColor: 'var(--surface)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                              <h6 style={{ margin: 0, color: 'var(--primary)' }}>{criterion.category}</h6>
                              <span style={{ 
                                fontWeight: 'bold',
                                color: criterion.percentage >= 70 ? '#4caf50' : criterion.percentage >= 50 ? '#ff9800' : '#dc3545'
                              }}>
                                {criterion.percentage.toFixed(0)}%
                              </span>
                            </div>
                            <div style={{ 
                              fontSize: '0.9rem', 
                              color: 'var(--text-secondary)', 
                              marginBottom: '0.5rem' 
                            }}>
                              Score: {criterion.score.toFixed(1)}/{criterion.max_score}
                            </div>
                            <div style={{ 
                              fontSize: '0.85rem', 
                              color: 'var(--text-secondary)',
                              lineHeight: '1.4'
                            }}>
                              {criterion.feedback}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
            
            <div style={{ textAlign: 'center', marginTop: '2rem' }}>
              <button 
                className="btn btn-primary"
                onClick={() => setCurrentStep(6)}
              >
                Continue to Review & Edit
                <FontAwesomeIcon icon={faChevronRight} style={{ marginLeft: '0.5rem' }} />
              </button>
            </div>
          </div>
        )}
        
        <div style={{ textAlign: 'center', marginTop: '2rem' }}>
          <button 
            className="btn btn-secondary"
            onClick={() => setCurrentStep(4)}
          >
            <FontAwesomeIcon icon={faChevronLeft} style={{ marginRight: '0.5rem' }} />
            Back to Upload
          </button>
        </div>
      </div>
    )
  }

  if (currentStep === 6 && evaluationResults.length > 0) {
    return (
      <div className="card">
        <h3 style={{ marginBottom: '1.5rem', color: 'var(--primary)' }}>
          <FontAwesomeIcon icon={faEdit} style={{ marginRight: '0.5rem' }} />
          Step 6: Faculty Review & Adjustments
        </h3>
        
        <p style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>
          Review AI evaluation results and make adjustments if needed. All changes require a reason for record-keeping.
        </p>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {evaluationResults.map((result, index) => (
            <div key={result.submission_id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h4 style={{ margin: 0, color: 'var(--primary)' }}>
                  Submission {index + 1}
                </h4>
                
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  {!editingResults[result.submission_id] ? (
                    <button 
                      className="btn btn-outline btn-sm"
                      onClick={() => setEditingResults(prev => ({
                        ...prev,
                        [result.submission_id]: { ...result }
                      }))}
                    >
                      <FontAwesomeIcon icon={faEdit} style={{ marginRight: '0.25rem' }} />
                      Edit Scores
                    </button>
                  ) : (
                    <>
                      <button 
                        className="btn btn-success btn-sm"
                        onClick={async () => {
                          try {
                            // Validate that reason is provided
                            if (!facultyReasons[result.submission_id]?.trim()) {
                              showNotification('Please provide a reason for the changes', 'error')
                              return
                            }

                            const response = await fetch(getApiUrl(SERVERS.EVALUATION, ENDPOINTS.EVALUATION_REVIEW) + `/${result.submission_id}/review`, {
                              method: 'PUT',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({
                                adjusted_scores: {
                                  overall_score: editingResults[result.submission_id].overall_score,
                                  overall_feedback: editingResults[result.submission_id].overall_feedback || result.overall_feedback
                                },
                                faculty_feedback: facultyReasons[result.submission_id],
                                reason_for_adjustment: facultyReasons[result.submission_id]
                              })
                            })
                            
                            if (response.ok) {
                              // Store the updated values before clearing editing state
                              const updatedScore = editingResults[result.submission_id].overall_score
                              const updatedFeedback = editingResults[result.submission_id].overall_feedback || result.overall_feedback
                              
                              // Update the evaluation results with the new data
                              setEvaluationResults(prev => prev.map(evalResult => {
                                if (evalResult.submission_id === result.submission_id) {
                                  return {
                                    ...evalResult,
                                    overall_score: updatedScore,
                                    overall_feedback: updatedFeedback,
                                    faculty_reviewed: true
                                  }
                                }
                                return evalResult
                              }))
                              
                              // Clear editing state after updating results
                              setEditingResults(prev => {
                                const newState = { ...prev }
                                delete newState[result.submission_id]
                                return newState
                              })
                              setFacultyReasons(prev => {
                                const newState = { ...prev }
                                delete newState[result.submission_id]
                                return newState
                              })
                              
                              showNotification('Review saved successfully!', 'success')
                            } else {
                              const errorData = await response.json()
                              throw new Error(errorData.detail || 'Failed to save review')
                            }
                          } catch (error) {
                            showNotification(`Save failed: ${error.message}`, 'error')
                          }
                        }}
                        disabled={!facultyReasons[result.submission_id]?.trim()}
                      >
                        <FontAwesomeIcon icon={faSave} style={{ marginRight: '0.25rem' }} />
                        Save Changes
                      </button>
                      <button 
                        className="btn btn-secondary btn-sm"
                        onClick={() => {
                          setEditingResults(prev => {
                            const newState = { ...prev }
                            delete newState[result.submission_id]
                            return newState
                          })
                          setFacultyReasons(prev => {
                            const newState = { ...prev }
                            delete newState[result.submission_id]
                            return newState
                          })
                        }}
                      >
                        <FontAwesomeIcon icon={faTimes} style={{ marginRight: '0.25rem' }} />
                        Cancel
                      </button>
                    </>
                  )}
                </div>
              </div>
              
              {/* Score Display/Edit */}
              <div style={{ marginBottom: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                  <strong>Overall Score:</strong>
                  {editingResults[result.submission_id] ? (
                    <input 
                      type="number"
                      min="0"
                      max="20"
                      step="0.1"
                      value={editingResults[result.submission_id].overall_score}
                      onChange={(e) => setEditingResults(prev => ({
                        ...prev,
                        [result.submission_id]: {
                          ...prev[result.submission_id],
                          overall_score: parseFloat(e.target.value) || 0
                        }
                      }))}
                      style={{ width: '80px', padding: '0.25rem' }}
                    />
                  ) : (
                    <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--primary)' }}>
                      {result.overall_score.toFixed(1)}/20
                    </span>
                  )}
                  <span style={{ 
                    color: result.overall_score >= 16 ? '#4caf50' : result.overall_score >= 12 ? '#ff9800' : '#dc3545'
                  }}>
                    ({((result.overall_score / 20) * 100).toFixed(1)}%)
                  </span>
                </div>
                
                {/* Overall Feedback Display/Edit */}
                <div style={{ marginBottom: '1rem' }}>
                  <strong>Overall Feedback:</strong>
                  {editingResults[result.submission_id] ? (
                    <textarea
                      value={editingResults[result.submission_id].overall_feedback || result.overall_feedback}
                      onChange={(e) => setEditingResults(prev => ({
                        ...prev,
                        [result.submission_id]: {
                          ...prev[result.submission_id],
                          overall_feedback: e.target.value
                        }
                      }))}
                      style={{ 
                        width: '100%', 
                        minHeight: '80px', 
                        marginTop: '0.5rem',
                        padding: '0.5rem'
                      }}
                    />
                  ) : (
                    <p style={{ 
                      margin: '0.5rem 0 0 0', 
                      padding: '0.75rem',
                      backgroundColor: 'var(--bg-lighter)',
                      borderRadius: '4px'
                    }}>
                      {result.overall_feedback}
                    </p>
                  )}
                </div>
                
                {/* Criterion-wise Scores */}
                {result.criterion_results && result.criterion_results.length > 0 && (
                  <div style={{ marginBottom: '1rem' }}>
                    <strong>Criterion Scores:</strong>
                    <div style={{ marginTop: '0.5rem', display: 'grid', gap: '0.5rem', gridTemplateColumns: 'repeat(2, 1fr)' }}>
                      {result.criterion_results.map((criterion, criterionIndex) => (
                        <div key={criterionIndex} style={{ 
                          display: 'flex', 
                          justifyContent: 'space-between', 
                          padding: '0.5rem',
                          backgroundColor: 'var(--surface)',
                          borderRadius: '4px'
                        }}>
                          <span style={{ fontSize: '0.9rem' }}>{criterion.category}:</span>
                          <span style={{ 
                            fontWeight: 'bold',
                            color: criterion.percentage >= 70 ? '#4caf50' : criterion.percentage >= 50 ? '#ff9800' : '#dc3545'
                          }}>
                            {criterion.score.toFixed(1)}/{criterion.max_score} ({criterion.percentage.toFixed(0)}%)
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              
              {/* Reason for Change (when editing) */}
              {editingResults[result.submission_id] && (
                <div style={{ 
                  padding: '1rem',
                  backgroundColor: 'var(--surface)',
                  borderRadius: '8px',
                  marginTop: '1rem',
                  border: !facultyReasons[result.submission_id]?.trim() ? '2px solid #dc3545' : '2px solid #28a745'
                }}>
                  <strong style={{ color: !facultyReasons[result.submission_id]?.trim() ? '#dc3545' : '#28a745' }}>
                    Reason for Changes (Required) {!facultyReasons[result.submission_id]?.trim() && '*'}
                  </strong>
                  <textarea
                    value={facultyReasons[result.submission_id] || ''}
                    onChange={(e) => setFacultyReasons(prev => ({
                      ...prev,
                      [result.submission_id]: e.target.value
                    }))}
                    placeholder="Please explain why you made these changes to the AI evaluation..."
                    style={{ 
                      width: '100%', 
                      minHeight: '60px', 
                      marginTop: '0.5rem',
                      padding: '0.5rem',
                      border: '1px solid #ccc',
                      borderRadius: '4px',
                      resize: 'vertical'
                    }}
                  />
                  {!facultyReasons[result.submission_id]?.trim() && (
                    <p style={{ color: '#dc3545', fontSize: '0.9rem', margin: '0.5rem 0 0 0' }}>
                      * A reason is required for any changes to the evaluation
                    </p>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
        
        <div style={{ textAlign: 'center', marginTop: '2rem' }}>
          <button 
            className="btn btn-primary"
            onClick={() => {
              markStepComplete(6)
              setCurrentStep(7)
            }}
          >
            Continue to Export Reports
            <FontAwesomeIcon icon={faChevronRight} style={{ marginRight: '0.5rem' }} />
          </button>
        </div>
        
        <div style={{ textAlign: 'center', marginTop: '1rem' }}>
          <button 
            className="btn btn-secondary"
            onClick={() => setCurrentStep(5)}
          >
            <FontAwesomeIcon icon={faChevronLeft} style={{ marginRight: '0.5rem' }} />
            Back to Evaluation Results
          </button>
        </div>
      </div>
    )
  }

  if (currentStep === 7 && completedSteps.has(6)) {
    return (
      <div className="card">
        <h3 style={{ marginBottom: '1.5rem', color: 'var(--primary)' }}>
          <FontAwesomeIcon icon={faDownload} style={{ marginRight: '0.5rem' }} />
          Step 7: Export Evaluation Reports
        </h3>
        
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <FontAwesomeIcon icon={faCheckCircle} size="3x" style={{ color: '#4caf50', marginBottom: '1rem' }} />
          <h4>Evaluation Complete!</h4>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
            Successfully evaluated {evaluationResults.length} submissions. 
            You can now download comprehensive reports or start a new evaluation.
          </p>
          
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button 
              className="btn btn-primary"
              onClick={async () => {
                try {
                  showNotification('Generating comprehensive evaluation report...', 'info')
                  
                  const response = await fetch(getApiUrl(SERVERS.EVALUATION, ENDPOINTS.EVALUATION_REPORT) + `/${selectedAssignment.id}/report`)
                  
                  if (response.ok) {
                    // Get filename from Content-Disposition header or use default
                    const contentDisposition = response.headers.get('Content-Disposition')
                    let filename = `evaluation_report_${selectedAssignment.assignment_name}.pdf`
                    
                    if (contentDisposition) {
                      const filenameMatch = contentDisposition.match(/filename="(.+)"/)
                      if (filenameMatch) {
                        filename = filenameMatch[1]
                      }
                    }
                    
                    const blob = await response.blob()
                    
                    // Verify it's a PDF
                    if (blob.type !== 'application/pdf') {
                      throw new Error('Downloaded file is not a valid PDF')
                    }
                    
                    const url = window.URL.createObjectURL(blob)
                    const a = document.createElement('a')
                    a.href = url
                    a.download = filename
                    a.style.display = 'none'
                    document.body.appendChild(a)
                    a.click()
                    document.body.removeChild(a)
                    window.URL.revokeObjectURL(url)
                    
                    showNotification('Comprehensive evaluation report downloaded successfully!', 'success')
                  } else {
                    const errorText = await response.text()
                    throw new Error(`Failed to generate report: ${errorText}`)
                  }
                } catch (error) {
                  console.error('Report download error:', error)
                  showNotification(`Download failed: ${error.message}`, 'error')
                }
              }}
            >
              <FontAwesomeIcon icon={faDownload} style={{ marginRight: '0.5rem' }} />
              Download Complete Report
            </button>
            
            <button 
              className="btn btn-secondary"
              onClick={() => {
                // Reset all state for new evaluation
                setCurrentStep(1)
                markStepComplete(7)
                showNotification('Ready for new evaluation!', 'success')
                // Additional reset logic would be handled by parent component
              }}
            >
              <FontAwesomeIcon icon={faPlay} style={{ marginRight: '0.5rem' }} />
              Start New Evaluation
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Default case - show the upload interface
  return (
    <div className="card">
      <h3 style={{ marginBottom: '1.5rem', color: 'var(--primary)' }}>
        <FontAwesomeIcon icon={faCloudUpload} style={{ marginRight: '0.5rem' }} />
        Upload Submission
      </h3>
      
      {selectedAssignment && (
        <div style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: 'var(--surface)', borderRadius: '8px' }}>
          <strong>Assignment:</strong> {selectedAssignment.assignment_name}
        </div>
      )}
      
      <p style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>
        Upload your submission (PDF or DOCX format).
      </p>
      
      {/* File Upload Dropzone - Only show if no files uploaded yet */}
      {uploadedFiles.length === 0 && (
        <div 
          {...getRootProps()} 
          className={`dropzone ${isDragActive ? 'active' : ''}`}
          style={{ 
            border: '2px dashed var(--border-color)',
            borderRadius: '8px',
            padding: '2rem',
            textAlign: 'center',
            cursor: 'pointer',
            backgroundColor: isDragActive ? 'var(--surface)' : 'var(--bg-lighter)',
            transition: 'all 0.3s ease'
          }}
        >
          <input {...getInputProps()} />
          <FontAwesomeIcon icon={faCloudUpload} size="3x" style={{ color: 'var(--primary)', marginBottom: '1rem' }} />
          {isDragActive ? (
            <p style={{ fontSize: '1.1rem', color: 'var(--primary)' }}>Drop files here...</p>
          ) : (
            <>
              <p style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>
                Drag & drop submission files here, or <span style={{ color: 'var(--primary)', textDecoration: 'underline' }}>browse</span>
              </p>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                Supports PDF and DOCX files up to 50MB
              </p>
            </>
          )}
        </div>
      )}
      
      {/* Uploaded Files List */}
      {uploadedFiles.length > 0 && (
        <div style={{ marginTop: '1.5rem' }}>
          <h4 style={{ marginBottom: '1rem' }}>Uploaded Files</h4>
          {uploadedFiles.map((file) => (
            <div key={file.id} className="card" style={{ marginBottom: '0.5rem', padding: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  {getClassificationBadge(file)}
                  <span>{file.name}</span>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                    ({formatFileSize(file.size)})
                  </span>
                </div>
                <button
                  className="btn btn-icon"
                  onClick={() => removeFile(file.id)}
                  style={{ color: 'var(--danger)' }}
                >
                  <FontAwesomeIcon icon={faTrash} />
                </button>
              </div>
            </div>
          ))}
          
          <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
            <button
              className="btn btn-primary"
              onClick={uploadSubmissions}
              disabled={uploadingFiles || uploadedFiles.length === 0}
            >
              {uploadingFiles ? (
                <>
                  <FontAwesomeIcon icon={faSpinner} spin style={{ marginRight: '0.5rem' }} />
                  Uploading...
                </>
              ) : (
                <>
                  <FontAwesomeIcon icon={faSave} style={{ marginRight: '0.5rem' }} />
                  Submit Files
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default EvaluationSteps
