import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faCloudUpload,
  faSpinner,
  faFilePdf,
  faFileWord,
  faTrash,
  faSave
} from '@fortawesome/free-solid-svg-icons';

const PDFUploadSteps = ({ 
  selectedAssignment,
  uploadedFiles = [],
  uploadingFiles = false,
  formatFileSize,
  getClassificationBadge,
  removeFile,
  getRootProps,
  getInputProps,
  isDragActive,
  uploadSubmissions
}) => {
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
      
      {/* File Upload Dropzone */}
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
  );
};

export default PDFUploadSteps;