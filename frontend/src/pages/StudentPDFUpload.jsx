import React, { useState, useEffect, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faChevronLeft, 
  faUpload, 
  faFilePdf, 
  faFileWord, 
  faExclamationTriangle 
} from '@fortawesome/free-solid-svg-icons';
import { useDropzone } from 'react-dropzone';
import PDFUploadSteps from '../components/PDFUploadSteps';
import { getBaseUrl, getApiUrl, SERVERS, ENDPOINTS } from '../config/api';

const StudentPDFUpload = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(4); // Start at upload step
  const [selectedAssignment] = useState(location.state?.selectedAssignment);
  const [studentId] = useState(location.state?.studentId);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploadingFiles, setUploadingFiles] = useState(false);
  const [completedSteps, setCompletedSteps] = useState(new Set([1, 2, 3])); // Mark previous steps as completed
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
  const onDrop = useCallback((acceptedFiles) => {
    const newFiles = acceptedFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      originalFile: file,
      name: file.name,
      size: file.size,
      type: file.name.toLowerCase().endsWith('.pdf') ? 'pdf' : 'docx',
      processing_status: 'pending'
    }));

    setUploadedFiles(current => [...current, ...newFiles]);
  }, []);

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
    if (fileObj.type === 'pdf') {
      return (
        <span className="badge" style={{ backgroundColor: '#d32f2f', color: 'white' }}>
          <FontAwesomeIcon icon={faFilePdf} style={{ marginRight: '0.25rem' }} />
          PDF
        </span>
      );
    }
    return (
      <span className="badge" style={{ backgroundColor: '#1976d2', color: 'white' }}>
        <FontAwesomeIcon icon={faFileWord} style={{ marginRight: '0.25rem' }} />
        DOCX
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
        throw new Error('Failed to upload files');
      }

      const result = await response.json();
      // Navigate back to StudentEvaluation with the processed submission
      navigate('/student/evaluation', {
        state: {
          studentId,
          selectedAssignment,
          submissionContent: result.content,
          submissionId: result.submission_id
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
  };

  return (
    <div className="container" style={{ padding: '2rem' }}>
      <div style={{ marginBottom: '2rem' }}>
        <button 
          className="btn btn-secondary" 
          onClick={() => navigate('/student/evaluation', { 
            state: { studentId, selectedAssignment } 
          })}
        >
          <FontAwesomeIcon icon={faChevronLeft} /> Back to Evaluation
        </button>
        <h2 className="text-center">
          <FontAwesomeIcon icon={faUpload} className="mr-2" /> Upload Assignment
        </h2>
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
        <PDFUploadSteps 
          selectedAssignment={selectedAssignment}
          uploadedFiles={uploadedFiles}
          setUploadedFiles={setUploadedFiles}
          uploadingFiles={uploadingFiles}
          uploadSubmissions={uploadSubmissions}
          removeFile={removeFile}
          getRootProps={getRootProps}
          getInputProps={getInputProps}
          isDragActive={isDragActive}
          formatFileSize={formatFileSize}
          getClassificationBadge={getClassificationBadge}
        />
      )}
    </div>
  );
};

export default StudentPDFUpload;