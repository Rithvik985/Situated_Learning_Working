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
  faPlay,
  faEye,
  faPaperPlane
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
  const [processingFiles, setProcessingFiles] = useState(false);
  const [error, setError] = useState(null);
  const [showTextModal, setShowTextModal] = useState(false);
  const [currentTextContent, setCurrentTextContent] = useState('');

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

  // NEW: Separate processing function
// NEW: Enhanced processing function with better text extraction
// NEW: Enhanced processing function with better text handling
const processFiles = async () => {
  setProcessingFiles(true);
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
      throw new Error(errorData.detail || 'Failed to process files');
    }

    const result = await response.json();
    console.log('Process response:', result);
    debugResponse(result);

    // FIXED: Robust text extraction from response
    let extractedText = '';
    let finalSubmissionId = '';
    let extractionMethod = 'standard';
    
    if (result && result.length > 0) {
      const processedSubmission = result[0];
      finalSubmissionId = processedSubmission.id;
      extractionMethod = processedSubmission.extraction_method || 'standard';
      
      // Try multiple possible fields for extracted text
      const possibleTextFields = [
        'extracted_text',      // Primary field for file extraction
        'content',             // Fallback field
        'text',                // Alternative field name
        'submission_content',  // Another possible field
        'processed_text'       // Yet another possibility
      ];
      
      for (const field of possibleTextFields) {
        if (processedSubmission[field] && typeof processedSubmission[field] === 'string') {
          extractedText = processedSubmission[field].trim();
          console.log(`Found text in field "${field}", length:`, extractedText.length);
          console.log(`First 500 chars:`, extractedText.substring(0, 500));
          break;
        }
      }
      
      // If no text found, log all available fields for debugging
      if (!extractedText) {
        console.warn('No text content found in response. Available fields:', Object.keys(processedSubmission));
      }
    } else {
      throw new Error('No processed submission data received from server');
    }

    // Handle case where text is very short (likely incomplete extraction)
    let processingStatus = 'processed';
    let userMessage = '';
    
    if (!extractedText) {
      extractedText = 'File was processed successfully but no text content could be extracted. This might be due to:\n- Image-based PDF with poor OCR results\n- Empty or corrupted file\n- Processing error\n\nPlease try manual input or upload a different file.';
      processingStatus = 'failed';
      userMessage = 'No text could be extracted from your file.';
    } else if (extractedText.length < 50) {
      userMessage = 'Very little text was extracted. The file might be image-based or contain mostly non-text elements.';
      console.warn('Very short text extracted:', extractedText);
    } else if (extractedText.length < 200) {
      userMessage = 'Limited text was extracted. You may want to verify the content or try manual input.';
      console.warn('Short text extracted:', extractedText);
    }

    if (userMessage) {
      setError(userMessage);
    }

    // Update local files state with processing results
    const updatedFiles = uploadedFiles.map((file, index) => ({
      ...file,
      id: finalSubmissionId || file.id,
      submission_id: finalSubmissionId,
      processing_status: processingStatus,
      extraction_method: extractionMethod,
      ocr_confidence: 1.0,
      extracted_text_preview: extractedText ? 
        (extractedText.length > 200 ? extractedText.substring(0, 200) + '...' : extractedText) : 'No text extracted',
      file_path: result[0]?.file_path,
      // Store the full extracted text for analysis
      full_extracted_text: extractedText
    }));

    setUploadedFiles(updatedFiles);

  } catch (err) {
    setError(err.message);
    console.error('Processing error:', err);
  } finally {
    setProcessingFiles(false);
  }
};
  // NEW: Submit function (navigate with extracted text)
  const submitForEvaluation = () => {
    if (uploadedFiles.length === 0) {
      setError('No files processed yet');
      return;
    }

    const processedFile = uploadedFiles[0];
    if (processedFile.processing_status !== 'processed') {
      setError('Please process the file first before submitting');
      return;
    }

    const extractedText = processedFile.full_extracted_text || '';
    
    navigate('/student/evaluation', {
      state: {
        studentId,
        selectedAssignment,
        submissionContent: extractedText,
        submissionId: processedFile.submission_id,
        uploadedFiles: uploadedFiles,
        processingComplete: true,
        fromUpload: true
      },
      replace: true
    });
  };

  // NEW: Function to view extracted text
  const viewExtractedText = (fileObj) => {
    const textContent = fileObj.full_extracted_text || 
                       fileObj.extracted_text_preview || 
                       'No text content available';
    setCurrentTextContent(textContent);
    setShowTextModal(true);
  };

  const removeFile = (fileId) => {
    setUploadedFiles(files => files.filter(f => f.id !== fileId));
    setError(null);
  };

  // const debugResponse = (result) => {
  //   console.log('=== DEBUG API RESPONSE ===');
  //   console.log('Full response:', result);
  //   if (result && result.length > 0) {
  //     const firstItem = result[0];
  //     console.log('First item keys:', Object.keys(firstItem));
  //     console.log('extracted_text exists:', 'extracted_text' in firstItem);
  //     console.log('extracted_text value:', firstItem.extracted_text);
  //     console.log('extracted_text length:', firstItem.extracted_text ? firstItem.extracted_text.length : 0);
  //     console.log('content exists:', 'content' in firstItem);
  //     console.log('content value:', firstItem.content);
  //   }
  //   console.log('=== END DEBUG ===');
  // };
//  In your uploadSubmissions function, the response parsing needs to be more robust:
// const debugResponse = (result) => {
//     console.log('=== DEBUG API RESPONSE ===');
//     console.log('Full response structure:', JSON.stringify(result, null, 2));
//     if (result && result.length > 0) {
//         const firstItem = result[0];
//         console.log('Available fields:', Object.keys(firstItem));
        
//         // Check ALL possible text fields
//         const textFields = ['extracted_text', 'content', 'text', 'submission_content', 'processed_text'];
//         textFields.forEach(field => {
//             if (firstItem[field]) {
//                 console.log(`Field "${field}":`, firstItem[field].substring(0, 100) + '...');
//                 console.log(`Field "${field}" length:`, firstItem[field].length);
//             }
//         });
//     }
//     console.log('=== END DEBUG ===');
// };
const debugResponse = (result) => {
  console.log('=== DEBUG API RESPONSE ===');
  console.log('Response type:', typeof result);
  console.log('Is array:', Array.isArray(result));
  
  if (Array.isArray(result)) {
    console.log('Array length:', result.length);
    result.forEach((item, index) => {
      console.log(`\n--- Item ${index} ---`);
      console.log('Type:', typeof item);
      console.log('Keys:', Object.keys(item));
      
      // Check all fields
      Object.keys(item).forEach(key => {
        const value = item[key];
        if (typeof value === 'string') {
          console.log(`Field "${key}" (length: ${value.length}):`, 
            value.length > 300 ? value.substring(0, 300) + '...' : value
          );
        } else {
          console.log(`Field "${key}":`, value);
        }
      });
    });
  } else if (typeof result === 'object') {
    console.log('Object keys:', Object.keys(result));
    Object.keys(result).forEach(key => {
      const value = result[key];
      if (typeof value === 'string') {
        console.log(`Field "${key}" (length: ${value.length}):`, 
          value.length > 300 ? value.substring(0, 300) + '...' : value
        );
      } else {
        console.log(`Field "${key}":`, value);
      }
    });
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
{/* Text Preview */}
{/* {fileObj.extracted_text_preview && (
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
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
      <strong>Extracted Text Preview:</strong>
      {fileObj.full_extracted_text && fileObj.full_extracted_text.length > 200 && (
        <button
          className="btn btn-link btn-sm"
          onClick={() => viewExtractedText(fileObj)}
          style={{ padding: '0', fontSize: '0.8rem' }}
        >
          View Full Text ({fileObj.full_extracted_text.length} chars)
        </button>
      )}
    </div>
    <div style={{ marginTop: '0.5rem', lineHeight: '1.4', whiteSpace: 'pre-wrap' }}>
      {fileObj.extracted_text_preview}
    </div>
  </div>
)} */}
{/* Text Preview */}
{(fileObj.extracted_text_preview || fileObj.processing_status === 'failed') && (
  <div style={{ 
    marginTop: '0.5rem',
    padding: '0.75rem',
    backgroundColor: fileObj.processing_status === 'failed' ? '#fff3cd' : 'var(--bg-lighter)',
    borderRadius: '4px',
    fontSize: '0.85rem',
    color: fileObj.processing_status === 'failed' ? '#856404' : 'var(--text-secondary)',
    fontFamily: 'monospace',
    maxHeight: '100px',
    overflow: 'auto',
    border: `1px solid ${fileObj.processing_status === 'failed' ? '#ffeaa7' : 'var(--border-color)'}`
  }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
      <strong>
        {fileObj.processing_status === 'failed' ? 'Extraction Failed:' : 'Extracted Text Preview:'}
        {fileObj.full_extracted_text && ` (${fileObj.full_extracted_text.length} chars)`}
      </strong>
      {fileObj.full_extracted_text && fileObj.full_extracted_text.length > 200 && (
        <button
          className="btn btn-link btn-sm"
          onClick={() => viewExtractedText(fileObj)}
          style={{ padding: '0', fontSize: '0.8rem' }}
        >
          View Full Text
        </button>
      )}
    </div>
    <div style={{ marginTop: '0.5rem', lineHeight: '1.4', whiteSpace: 'pre-wrap' }}>
      {fileObj.extracted_text_preview}
    </div>
    {fileObj.full_extracted_text && fileObj.full_extracted_text.length < 200 && (
      <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: '#ff9800' }}>
        ⚠️ Only {fileObj.full_extracted_text.length} characters extracted. This might be incomplete.
      </div>
    )}
  </div>
)}
                      </div>
                      
                      <div style={{ display: 'flex', gap: '0.5rem', marginLeft: '1rem' }}>
                        {/* View Text Button - Only show when file is processed */}
                        {fileObj.processing_status === 'processed' && (
                          <button
                            className="btn btn-outline btn-sm"
                            onClick={() => viewExtractedText(fileObj)}
                            title="View Full Extracted Text"
                          >
                            <FontAwesomeIcon icon={faEye} />
                          </button>
                        )}
                        
                        <button
                          className="btn btn-outline btn-sm"
                          onClick={() => removeFile(fileObj.id)}
                          disabled={processingFiles || uploadingFiles}
                        >
                          <FontAwesomeIcon icon={faTrash} />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Action Buttons */}
              <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '2rem', flexWrap: 'wrap' }}>
                {/* Process Button - Only show if file is not processed yet */}
                {uploadedFiles.some(file => file.processing_status !== 'processed') && (
                  <button 
                    className="btn btn-primary btn-lg"
                    onClick={processFiles}
                    disabled={processingFiles}
                  >
                    {processingFiles ? (
                      <>
                        <FontAwesomeIcon icon={faSpinner} spin style={{ marginRight: '0.5rem' }} />
                        Processing File...
                      </>
                    ) : (
                      <>
                        <FontAwesomeIcon icon={faPlay} style={{ marginRight: '0.5rem' }} />
                        Process File
                      </>
                    )}
                  </button>
                )}
                
                {/* Submit Button - Only show when file is processed */}
                {uploadedFiles.some(file => file.processing_status === 'processed') && (
                  <button 
                    className="btn btn-success btn-lg"
                    onClick={submitForEvaluation}
                    disabled={uploadingFiles}
                  >
                    {uploadingFiles ? (
                      <>
                        <FontAwesomeIcon icon={faSpinner} spin style={{ marginRight: '0.5rem' }} />
                        Submitting...
                      </>
                    ) : (
                      <>
                        <FontAwesomeIcon icon={faPaperPlane} style={{ marginRight: '0.5rem' }} />
                        Submit for Evaluation
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
          )}
          
          <div style={{ textAlign: 'center', marginTop: '2rem' }}>
            {uploadedFiles.length > 0 && (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                {uploadedFiles.some(file => file.processing_status !== 'processed') 
                  ? 'Click "Process File" to extract text from your submission, then "Submit for Evaluation" to proceed.'
                  : 'Text extraction complete! Review the extracted text and click "Submit for Evaluation" to proceed.'}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Extracted Text Modal */}
      {showTextModal && (
        <div className="modal" style={{ 
          position: 'fixed', 
          top: 0, 
          left: 0, 
          right: 0, 
          bottom: 0, 
          backgroundColor: 'rgba(0,0,0,0.5)', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          zIndex: 1000 
        }}>
          <div className="modal-content" style={{ 
            backgroundColor: 'white', 
            padding: '2rem', 
            borderRadius: '8px', 
            maxWidth: '90%', 
            maxHeight: '90%', 
            width: '800px',
            overflow: 'auto',
            boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h3 style={{ margin: 0, color: 'var(--primary)' }}>
                <FontAwesomeIcon icon={faEye} style={{ marginRight: '0.5rem' }} />
                Extracted Text Content
              </h3>
              <button 
                className="btn btn-secondary btn-sm"
                onClick={() => setShowTextModal(false)}
              >
                Close
              </button>
            </div>
            
            <div style={{ 
              padding: '1rem',
              backgroundColor: 'var(--bg-lighter)',
              borderRadius: '4px',
              border: '1px solid var(--border-color)',
              maxHeight: '500px',
              overflow: 'auto',
              fontFamily: 'monospace',
              fontSize: '0.9rem',
              lineHeight: '1.5',
              whiteSpace: 'pre-wrap'
            }}>
              {currentTextContent || 'No text content available'}
            </div>
            
            <div style={{ marginTop: '1.5rem', textAlign: 'right' }}>
              <button 
                className="btn btn-primary"
                onClick={() => setShowTextModal(false)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StudentPDFUpload;
