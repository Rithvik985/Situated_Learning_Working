import React, { useState, useEffect, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faChevronLeft, 
  faUpload, 
  faFilePdf, 
  faFileWord, 
  faExclamationTriangle,
  faCloudUpload,
  faTrash,
  faSpinner,
  faCheckCircle,
  faPlay
} from '@fortawesome/free-solid-svg-icons';
import { useDropzone } from 'react-dropzone';
import { getApiUrl, SERVERS, ENDPOINTS } from '../config/api';

const StudentPDFUpload = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [selectedAssignment] = useState(location.state?.selectedAssignment);
  const [studentId] = useState(location.state?.studentId);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploadingFiles, setUploadingFiles] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!selectedAssignment || !studentId) {
      setError("Missing required information");
      setTimeout(() => {
        navigate('/student/evaluation');
      }, 3000);
    }
  }, [selectedAssignment, studentId, navigate]);

  // File upload handlers
  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    if (rejectedFiles.length > 0) {
      setError('Some files were rejected. Only PDF and DOCX files are allowed.');
      return;
    }

    if (uploadedFiles.length + acceptedFiles.length > 1) {
      setError('Maximum 1 submission allowed for student upload.');
      return;
    }

    const newFiles = acceptedFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      originalFile: file,
      name: file.name,
      size: file.size,
      type: file.name.toLowerCase().endsWith('.pdf') ? 'pdf' : 'docx',
      processing_status: 'pending',
      extraction_method: 'ready'
    }));

    setUploadedFiles(current => [...current, ...newFiles]);
    setError(null);
  }, [uploadedFiles]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024 // 50MB
  });

  // Utility functions
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getClassificationBadge = (fileObj) => {
    const method = fileObj.extraction_method;
    const confidence = fileObj.ocr_confidence || 1.0;
    
    if (!method || method === 'ready') {
      return (
        <span className="badge" style={{ backgroundColor: '#6c757d', color: 'white' }}>
          Ready to Process
        </span>
      );
    }
    
    if (method === 'failed') {
      return (
        <span className="badge" style={{ backgroundColor: '#dc3545', color: 'white' }}>
          Processing Failed
        </span>
      );
    }
    
    if (method === 'ocr' || method === 'ocr_vision_llm') {
      return (
        <span className="badge" style={{ backgroundColor: '#ff9800', color: 'white' }}>
          Handwritten
        </span>
      );
    } else if (method === 'standard' || method === 'docx_standard') {
      return (
        <span className="badge" style={{ backgroundColor: '#4caf50', color: 'white' }}>
          Typed Text
        </span>
      );
    } else if (method === 'standard_fallback') {
      return (
        <span className="badge" style={{ backgroundColor: '#ff5722', color: 'white' }}>
          Low Quality ({(confidence * 100).toFixed(0)}%)
        </span>
      );
    }
    
    return (
      <span className="badge" style={{ backgroundColor: '#9e9e9e', color: 'white' }}>
        Processing...
      </span>
    );
  };

  const uploadSubmissions = async () => {
    setUploadingFiles(true);
    setError(null);
    
    try {
      if (uploadedFiles.length === 0) {
        throw new Error('No files selected');
      }

      const formData = new FormData();
      formData.append('assignment_id', selectedAssignment.id);
      formData.append('student_id', studentId);
      
      uploadedFiles.forEach(file => {
        formData.append('files', file.originalFile);
      });

      const response = await fetch(getApiUrl(SERVERS.EVALUATION, ENDPOINTS.SUBMIT_EVALUATION), {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to upload files');
      }

      const result = await response.json();
      console.log('Upload response:', result); // Debug log
        // Then in your uploadSubmissions function, call it:
      debugResponse(result); // Add this line
      
      // FIX: Properly extract the text content from response
      let extractedText = '';
      let finalSubmissionId = '';
      
      if (result && result.length > 0) {
        // The backend returns an array of processed submissions
        const processedSubmission = result[0];
        finalSubmissionId = processedSubmission.id;
        
        // EXTRACT THE TEXT CONTENT - FIX THIS PART
        if (processedSubmission.extracted_text) {
          extractedText = processedSubmission.extracted_text;
          console.log('Extracted text length:', extractedText.length);
        } else {
          console.warn('No extracted_text in response, checking other fields:', processedSubmission);
          // Try alternative fields
          if (processedSubmission.content) {
            extractedText = processedSubmission.content;
          }
        }
      } else {
        throw new Error('No processed submission data received from server');
      }

      if (!extractedText) {
        console.warn('No text content extracted from file');
        extractedText = 'File processed but no text could be extracted. Please try manual input or a different file.';
      }

      // Update local files state with processing results
      const updatedFiles = uploadedFiles.map((file, index) => ({
        ...file,
        id: finalSubmissionId || file.id,
        submission_id: finalSubmissionId,
        processing_status: 'processed',
        extraction_method: 'standard',
        ocr_confidence: 1.0,
        extracted_text_preview: extractedText ? 
          extractedText.substring(0, 200) + '...' : 'Text extraction completed',
        file_path: result[0]?.file_path,
        // Store the full extracted text for analysis
        full_extracted_text: extractedText
      }));

      setUploadedFiles(updatedFiles);

      // Navigate back with the ACTUAL EXTRACTED TEXT
      navigate('/student/evaluation', {
        state: {
          studentId,
          selectedAssignment,
          submissionContent: extractedText, // THIS IS THE CRITICAL PART
          submissionId: finalSubmissionId,
          uploadedFiles: updatedFiles,
          processingComplete: true,
          fromUpload: true
        },
        replace: true
      });
    } catch (err) {
      setError(err.message);
      console.error('Upload error:', err);
    } finally {
      setUploadingFiles(false);
    }
  };
  const removeFile = (fileId) => {
    setUploadedFiles(files => files.filter(f => f.id !== fileId));
    setError(null);
  };

    // Add this helper function to debug the API response
  const debugResponse = (result) => {
    console.log('=== DEBUG API RESPONSE ===');
    console.log('Full response:', result);
    if (result && result.length > 0) {
      const firstItem = result[0];
      console.log('First item keys:', Object.keys(firstItem));
      console.log('extracted_text exists:', 'extracted_text' in firstItem);
      console.log('extracted_text value:', firstItem.extracted_text);
      console.log('extracted_text length:', firstItem.extracted_text ? firstItem.extracted_text.length : 0);
      console.log('content exists:', 'content' in firstItem);
      console.log('content value:', firstItem.content);
    }
    console.log('=== END DEBUG ===');
  };



  return (
    <div className="container" style={{ padding: '2rem', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <button 
          className="btn btn-secondary" 
          onClick={() => navigate('/student/evaluation', { 
            state: { studentId, selectedAssignment } 
          })}
          style={{ marginBottom: '1rem' }}
        >
          <FontAwesomeIcon icon={faChevronLeft} /> Back to Evaluation
        </button>
        
        <div className="text-center">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <div style={{ fontSize: '2.5rem', color: 'var(--primary)' }}>
              <FontAwesomeIcon icon={faUpload} />
            </div>
            <h1 style={{ fontSize: '2rem', margin: 0 }}>Upload Your Assignment</h1>
          </div>

          <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', maxWidth: '600px', margin: '0 auto' }}>
            Upload your submission for AI-powered evaluation. Supports PDF and DOCX files with automatic text extraction.
          </p>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger" style={{ marginBottom: '1rem' }}>
          <FontAwesomeIcon icon={faExclamationTriangle} style={{ marginRight: '0.5rem' }} />
          {error}
        </div>
      )}

      {(!selectedAssignment || !studentId) ? (
        <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
          <FontAwesomeIcon icon={faExclamationTriangle} size="2x" style={{ color: '#dc3545', marginBottom: '1rem' }} />
          <h3>Missing Information</h3>
          <p>Redirecting to evaluation page...</p>
        </div>
      ) : (
        <div className="card">
          <h3 style={{ marginBottom: '1.5rem', color: 'var(--primary)' }}>
            <FontAwesomeIcon icon={faCloudUpload} style={{ marginRight: '0.5rem' }} />
            Upload Your Submission
          </h3>
          
          <div style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: 'var(--surface)', borderRadius: '8px' }}>
            <strong>Assignment:</strong> {selectedAssignment.assignment_name}
          </div>
          
          <p style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>
            Upload your submission file (PDF or DOCX format). The system will automatically extract text using OCR if needed.
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
                <p style={{ fontSize: '1.1rem', color: 'var(--primary)' }}>Drop your file here...</p>
              ) : (
                <>
                  <p style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>
                    Drag & drop your submission file here, or <span style={{ color: 'var(--primary)', textDecoration: 'underline' }}>browse</span>
                  </p>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                    PDF and DOCX files supported (max 1 file, 50MB)
                  </p>
                </>
              )}
            </div>
          )}
          
          {/* Uploaded Files List */}
          {uploadedFiles.length > 0 && (
            <div style={{ marginTop: '2rem' }}>
              <h4 style={{ marginBottom: '1rem' }}>
                Your Submission
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
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
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
                          {fileObj.processing_status === 'pending' && (
                            <span className="badge" style={{ backgroundColor: '#ff9800', color: 'white' }}>
                              <FontAwesomeIcon icon={faSpinner} spin style={{ marginRight: '0.25rem' }} />
                              Processing
                            </span>
                          )}
                          {getClassificationBadge(fileObj)}
                        </div>
                        
                        {/* Text Preview */}
                        {fileObj.extracted_text_preview && (
                          <div style={{ 
                            marginTop: '0.5rem',
                            padding: '0.75rem',
                            backgroundColor: 'var(--bg-lighter)',
                            borderRadius: '4px',
                            fontSize: '0.85rem',
                            color: 'var(--text-secondary)',
                            fontFamily: 'monospace',
                            maxHeight: '100px',
                            overflow: 'auto',
                            border: '1px solid var(--border-color)'
                          }}>
                            <strong>Extracted Text Preview:</strong> 
                            <div style={{ marginTop: '0.5rem', lineHeight: '1.4' }}>
                              {fileObj.extracted_text_preview}
                            </div>
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
                <button 
                  className="btn btn-primary btn-lg"
                  onClick={uploadSubmissions}
                  disabled={uploadingFiles}
                >
                  {uploadingFiles ? (
                    <>
                      <FontAwesomeIcon icon={faSpinner} spin style={{ marginRight: '0.5rem' }} />
                      Processing File...
                    </>
                  ) : (
                    <>
                      <FontAwesomeIcon icon={faPlay} style={{ marginRight: '0.5rem' }} />
                      Process & Submit
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
          
          <div style={{ textAlign: 'center', marginTop: '2rem' }}>
            {uploadedFiles.length > 0 && (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                Click "Process & Submit" to extract text from your submission and proceed to evaluation.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default StudentPDFUpload;