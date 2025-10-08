import React, { useState, useCallback,useEffect } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { 
  faUpload, 
  faDatabase, 
  faCogs, 
  faFilePdf, 
  faFileWord,
  faTrash,
  faSpinner,
  faCheckCircle,
  faExclamationTriangle,
  faCloudUpload,
  faFolderOpen
} from '@fortawesome/free-solid-svg-icons'
import { useDropzone } from 'react-dropzone'
import { getApiUrl, SERVERS, ENDPOINTS } from '../config/api'
import './UploadPastAssignment.css'

const UploadPastAssignment = () => {
  // Generate academic years from 2009-10 to 2025-26
  const generateAcademicYears = () => {
    const years = []
    for (let year = 2009; year <= 2025; year++) {
      const nextYear = year + 1
      years.push(`${year}-${nextYear.toString().slice(-2)}`)
    }
    return years
  }

  const academicYears = generateAcademicYears()

  const [formData, setFormData] = useState({
    courseTitle: '',
    courseCode: '',
    academicYear: '',
    semester: 1
  })
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [uploadResults, setUploadResults] = useState(null)
  const [uploadError, setUploadError] = useState('')
  const [error, setError] = useState('')
  const [samlData, setSamlData] = useState({});
  const [userData, setUserData] = useState({});

      useEffect(() => {
    const fetchSamlData = async () => {
      try {
        // IMPORTANT: use exact backend path (qpra not qbg)
        const url = `/sla/get-saml-data`;
        console.log("[SAML] Fetching SAML data from:", url);
  
        const response = await fetch(url, {
          method: "GET",
          credentials: "include", // include HttpOnly cookie
          headers: {
            "Accept": "application/json",
          },
        });
  
        if (!response.ok) {
          console.warn("[SAML] fetch returned non-ok:", response.status);
          // If unauthorized, redirect to login (start SAML flow)
          if (response.status === 401) {
            console.log("[SAML] Session missing/expired — redirecting to login");
            window.location.href = `/`;
            return;
          }
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
  
        const data = await response.json();
        setUserData(data);
        // Defensive extraction
        const courseData = {};
        const apiData = data?.api_data;
  
        if (Array.isArray(apiData)) {
          apiData.forEach((source, srcIndex) => {
            const ds = source?.["data-source"] || source?.data_source || `source_${srcIndex}`;
            const courses = Array.isArray(source?.courses) ? source.courses : Array.isArray(source?.data) ? source.data : [];
  
            courses.forEach((course) => {
              if (!course || typeof course !== "object") return;
  
              if (ds === "taxila") {
                // Taxila: key = fullname, value = shortname
                if (course.fullname && course.shortname) {
                  courseData[course.fullname] = course.shortname;
                }
              } else if (ds === "canvas") {
                // Canvas: key = name, value = course_code
                if (course.name && course.course_code) {
                  courseData[course.name] = course.course_code;
                }
              } else {
                // generic fallback — try common fields
                const title = course.fullname || course.name || course.title;
                const code = course.shortname || course.course_code || course.code || course.id;
                if (title && code) courseData[title] = code;
              }
            });
          });
        } else {
          console.warn("[SAML] api_data missing or not an array:", apiData);
        }
  
        setSamlData(courseData);
        setError(null);
      } catch (err) {
        console.error("Error fetching SAML data:", err);
        setError(err.message || "Unknown error");
        setSamlData({}); // ensure consistent state shape
      }
    };
  
    fetchSamlData();
  }, []);

  // Handle form input changes
  const handleInputChange = (e) => {
    const { name, value } = e.target
      if (name === "courseTitle") {
    setFormData((prev) => ({
      ...prev,
      courseTitle: value,        
      courseCode: samlData[value] || "", 
    }));
  } else {
    setFormData(prev => ({
      ...prev,
      [name]: name === 'semester' ? parseInt(value) : value
    }))
  }
  }

  // Handle file drop
  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    // Handle rejected files
    if (rejectedFiles.length > 0) {
      const errorMessages = rejectedFiles.map(({ file, errors }) => 
        `${file.name}: ${errors.map(e => e.message).join(', ')}`
      )
      setUploadError(`Invalid files: ${errorMessages.join('; ')}`)
      return
    }

    // Check total file count
    if (files.length + acceptedFiles.length > 10) {
      setUploadError('Maximum 10 files allowed')
      return
    }

    // Add files with metadata
    const newFiles = acceptedFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      name: file.name,
      size: file.size,
      type: file.name.toLowerCase().endsWith('.pdf') ? 'pdf' : 'docx',
      status: 'ready'
    }))

    setFiles(prev => [...prev, ...newFiles])
    setUploadError('')
  }, [files])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    maxFiles: 10,
    multiple: true
  })

  // Remove file
  const removeFile = (fileId) => {
    setFiles(prev => prev.filter(f => f.id !== fileId))
  }

  // Format file size
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Validate form
    if (!formData.courseTitle.trim()) {
      setUploadError('Course name is required')
      return
    }
    if (!formData.courseCode.trim()) {
      setUploadError('Course code is required')
      return
    }
    if (!formData.academicYear.trim()) {
      setUploadError('Academic year is required')
      return
    }
    if (files.length === 0) {
      setUploadError('At least one file is required')
      return
    }

    setUploading(true)
    setUploadError('')
    setUploadResults(null)

    try {
      // Prepare form data
      const uploadFormData = new FormData()
      uploadFormData.append('course_title', formData.courseTitle)
      uploadFormData.append('course_code', formData.courseCode)
      uploadFormData.append('academic_year', formData.academicYear)
      uploadFormData.append('semester', formData.semester.toString())
      
      // Add files
      files.forEach(fileObj => {
        uploadFormData.append('files', fileObj.file)
      })

      // Make API call
      const response = await fetch(getApiUrl(SERVERS.UPLOAD, ENDPOINTS.UPLOAD_ASSIGNMENT), {
        method: 'POST',
        body: uploadFormData
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Upload failed')
      }

      const result = await response.json()
      setUploadResults(result)
      
      // Reset form
      setFormData({
        courseTitle: '',
        courseCode: '',
        academicYear: '',
        semester: 1
      })
      setFiles([])

    } catch (error) {
      setUploadError(error.message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="upload-container">
      <div className="container">
   <div className="upload-header">
  <div className="upload-title">
    <div className="upload-icon">
      <FontAwesomeIcon icon={faUpload} />
    </div>
    <h1>Upload Past Assignments</h1>
  </div>
  <p>
    Build your reference corpus by uploading past assignments for intelligent assignment generation
  </p>
</div>


        {/* Upload Form */}
        <div className="upload-form-container">
          <form onSubmit={handleSubmit} className="upload-form">
            {/* Course Information */}
            <div className="form-section">
              <h3>
                <FontAwesomeIcon icon={faDatabase} />
                Course Information
              </h3>
              
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="courseTitle" className="form-label">
                    Course Name *
                  </label>
                  <select
                    type="text"
                    id="courseTitle"
                    name="courseTitle"
                    className="form-input"
                    placeholder="e.g., Introduction to Computer Science"
                    value={formData.courseTitle}
                    onChange={handleInputChange}
                    required
                  >
                          <option value="" disabled>Select a Course</option>
        {Object.keys(samlData).map((courseName, index) => (
          <option key={index} value={courseName}>
            {courseName}
          </option>
        ))}
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="courseCode" className="form-label">
                    Course Id *
                  </label>
                  <input
                    type="text"
                    id="courseCode"
                    name="courseCode"
                    className="form-input"
                    placeholder="e.g., CS101"
                    value={formData.courseCode}
                    readOnly
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="academicYear" className="form-label">
                    Academic Year *
                  </label>
                  <select
                    id="academicYear"
                    name="academicYear"
                    className="form-input"
                    value={formData.academicYear}
                    onChange={handleInputChange}
                    required
                  >
                    <option value="">Select Academic Year</option>
                    {academicYears.map(year => (
                      <option key={year} value={year}>
                        {year}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="semester" className="form-label">
                    Semester *
                  </label>
                  <select
                    id="semester"
                    name="semester"
                    className="form-input"
                    value={formData.semester}
                    onChange={handleInputChange}
                    required
                  >
                    <option value={1}>Semester 1</option>
                    <option value={2}>Semester 2</option>
                  </select>
                </div>
              </div>
            </div>

            {/* File Upload */}
            <div className="form-section">
              <h3>
                <FontAwesomeIcon icon={faCloudUpload} />
                Upload Assignment Files
              </h3>
              
              <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
                <input {...getInputProps()} />
                <div className="dropzone-content">
                  <FontAwesomeIcon icon={faFolderOpen} className="dropzone-icon" />
                  {isDragActive ? (
                    <p>Drop files here...</p>
                  ) : (
                    <>
                      <p>Drag & drop assignment files here, or <span className="browse-link">browse</span></p>
                      <p className="dropzone-hint">PDF and DOCX files supported (max 10 files, 50MB each)</p>
                    </>
                  )}
                </div>
              </div>

              {/* File List */}
              {files.length > 0 && (
                <div className="file-list">
                  <h4>Selected Files ({files.length}/10)</h4>
                  {files.map(fileObj => (
                    <div key={fileObj.id} className="file-item">
                      <div className="file-info">
                        <div className="file-icon">
                          <FontAwesomeIcon 
                            icon={fileObj.type === 'pdf' ? faFilePdf : faFileWord} 
                            className={fileObj.type === 'pdf' ? 'pdf-icon' : 'docx-icon'}
                          />
                        </div>
                        <div className="file-details">
                          <div className="file-name">{fileObj.name}</div>
                          <div className="file-size">{formatFileSize(fileObj.size)}</div>
                        </div>
                      </div>
                      <button
                        type="button"
                        className="remove-file-btn"
                        onClick={() => removeFile(fileObj.id)}
                        disabled={uploading}
                      >
                        <FontAwesomeIcon icon={faTrash} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Error Display */}
            {uploadError && (
              <div className="error-message">
                <FontAwesomeIcon icon={faExclamationTriangle} />
                {uploadError}
              </div>
            )}

            {/* Success Display */}
            {uploadResults && (
              <div className="success-message">
                <FontAwesomeIcon icon={faCheckCircle} />
                <div>
                  <h4>Upload Successful!</h4>
                  <p>{uploadResults.message}</p>
                  <p>Uploaded {uploadResults.uploaded_files.length} files for processing.</p>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <div className="form-actions">
              <button
                type="submit"
                className="btn btn-primary upload-btn"
                disabled={uploading || files.length === 0}
              >
                {uploading ? (
                  <>
                    <FontAwesomeIcon icon={faSpinner} className="spinner" />
                    Uploading & Processing...
                  </>
                ) : (
                  <>
                    <FontAwesomeIcon icon={faUpload} />
                    Upload Assignments
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Information Section */}
        {/* <div className="info-section">
          <div className="info-card">
            <h3>
              <FontAwesomeIcon icon={faDatabase} />
              What Happens After Upload?
            </h3>
            <ul>
              <li>Files are automatically processed and questions are extracted</li>
              <li>Original files are stored securely in MinIO object storage</li>
              <li>Questions are partitioned into separate files for analysis</li>
              <li>Text content is extracted and stored in the database</li>
              <li>Metadata and topics are automatically tagged for future use</li>
            </ul>
          </div>
        </div> */}
      </div>
    </div>
  )
}

export default UploadPastAssignment
