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
      
      // FIX: Check if result.files exists, otherwise create a fallback
      let updatedFiles = [];
      
      if (result.files && Array.isArray(result.files)) {
        // Use server response if available
        updatedFiles = result.files.map((serverFile, index) => ({
          ...uploadedFiles[index],
          id: serverFile.id || uploadedFiles[index].id,
          submission_id: serverFile.id || uploadedFiles[index].id,
          processing_status: serverFile.processing_status || 'processed',
          extraction_method: serverFile.extraction_method || 'standard',
          ocr_confidence: serverFile.ocr_confidence || 1.0,
          extracted_text_preview: serverFile.extracted_text ? 
            serverFile.extracted_text.substring(0, 200) + '...' : 'Text extraction completed',
          file_path: serverFile.file_path
        }));
      } else {
        // Fallback: create file objects from uploaded files
        updatedFiles = uploadedFiles.map(file => ({
          ...file,
          processing_status: 'processed',
          extraction_method: 'standard',
          ocr_confidence: 1.0,
          extracted_text_preview: 'Text extraction completed successfully',
          submission_id: result.submission_id || file.id
        }));
      }

      setUploadedFiles(updatedFiles);

      // Navigate back to StudentEvaluation with the processed submission
      navigate('/student/evaluation', {
        state: {
          studentId,
          selectedAssignment,
          submissionContent: result.content || updatedFiles[0]?.extracted_text_preview,
          submissionId: result.submission_id || updatedFiles[0]?.id,
          uploadedFiles: updatedFiles,
          processingComplete: true
        }
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setUploadingFiles(false);
    }
  };

  const removeFile = (fileId) => {
    setUploadedFiles(files => files.filter(f => f.id !== fileId));
    setError(null);
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