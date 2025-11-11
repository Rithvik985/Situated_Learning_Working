/**
 * API Configuration for Situated Learning System Frontend
 * Manages endpoints for the separated FastAPI servers
 */

// API Configuration for all services
const API_CONFIG = {
  // Faculty Service
  FACULTY: {
    BASE_URL: '/api/faculty',
    ENDPOINTS: {
      PENDING_SUBMISSIONS: '/pending-submissions',
      EVALUATE_SUBMISSION: '/pending-submissions',
      FACULTY_EVALUATION_UPDATE: '/evaluate',
      RUBRIC: '/rubric',
    }
  },

  // Upload Service
  UPLOAD: {
    BASE_URL: '/upload',
    ENDPOINTS: {
      UPLOAD: '/past-assignments',
      ASSIGNMENTS: '/assignments',
      ASSIGNMENT: '/assignments',
      STATUS: '/status',
      HEALTH: '/health'
    }
  },

  // Generation Service
  GENERATION: {
    BASE_URL: '/generation',
    ENDPOINTS: {
      GENERATE: '/generate',
      GENERATE_PROGRESSIVE: '/generate-progressive',
      DOMAINS: '/domains',
      EDIT_ASSIGNMENT: '/assignments',
      RUBRIC_EDIT: '/rubric',
      RUBRIC_DOWNLOAD: '/rubric',
      SAVE_ASSIGNMENT: '/assignments/save',
      DOWNLOAD_ASSIGNMENT: '/assignments',
      DOWNLOAD_MULTIPLE: '/assignments/download',
      HEALTH: '/health',
      STATUS: '/status'
    }
  },

  // Evaluation Service
  EVALUATION: {
    BASE_URL: '/evaluation',
    ENDPOINTS: {
      COURSES: '/courses',
      COURSE_FILTERS: '/courses',
      ASSIGNMENTS: '/assignments',
      RUBRICS: '/rubrics',
      RUBRIC_EDIT: '/rubrics',
      SUBMIT: '/submissions/upload',
      STUDENT_SWOT: '/student/swot',
      // FACULTY_EVALUATE: '/faculty/evaluate',
      // PENDING_SUBMISSIONS: '/faculty/pending',
      PROGRESS: '/status',
      RESULTS: '/assignments',
      REVIEW: '/submissions',
      REPORT: '/assignments',
      HEALTH: '/health',
      STATUS: '/status'
    }
  },

  // Analytics Service
  ANALYTICS: {
    BASE_URL: '/analytics',
    ENDPOINTS: {
      OVERVIEW: '/overview',
      USAGE: '/usage',
      CONTENT: '/content',
      LEARNING: '/learning',
      COURSES: '/courses',
      EXPORT: '/export',
      HEALTH: '/health',
      STATUS: '/status'
    }
  },

  // Student Service
  STUDENT: {
    BASE_URL: '/api/student',
    ENDPOINTS: {
      CONTEXT_OPTIONS: '/context-options',
      GENERATE_QUESTIONS: '/questions/generate',
      SELECT_QUESTION: '/questions',
      STATUS: '/questions',
      SUBMIT: '/submissions',
      SAVE_ASSIGNMENT: '/assignments/save',
      LIST_ASSIGNMENTS: '/assignments',
      COURSES: '/courses',
      AI_CHECK: '/ai-check',
      HEALTH: '/health',
    }
  },

    // Faculty Service
  FACULTY: {
    BASE_URL: '/api/faculty',
    ENDPOINTS: {
      QUESTIONS: '/questions',
      FINALIZE: '/finalize',
      COURSES: '/courses',
      STUDENTS: '/students',
      EVALUATION: '/evaluation',
      FACULTY_EVALUATION_UPDATE: '/evaluation/update',  // Add this for criterion updates
      HEALTH: '/health',
      STATUS: '/status',
      FACULTY_STUDENTS: '/students',
      FACULTY_APPROVE_QUESTION: '/questions',
      FACULTY_QUESTIONS_BY_STUDENT: '/questions/student',
      GET_SUBMISSION: '/submissions',


      // core endpoints used by frontend
      GET_RUBRIC: '/rubric',
      PENDING_SUBMISSIONS: '/pending-submissions', // GET /api/faculty/pending-submissions
      EVALUATE_SUBMISSION: '/pending-submissions',  // will append /{id}/evaluate on the client
      FACULTY_EVALUATION_UPDATE: '/evaluate',  // for criterion score updates - matches backend route
      DETECT_AI: '/submissions'  // for AI detection - will append /{id}/detect-ai on the client
    }
  }

};

/**
 * Helper function to construct the full API URL for a given server and endpoint
 * @param {string} server - The server identifier (e.g., 'FACULTY', 'STUDENT')
 * @param {string} endpoint - The endpoint identifier (e.g., 'QUESTIONS', 'STATUS')
 * @returns {string} The complete API URL
 */
export const getApiUrl = (server, endpoint) => {
  const serverConfig = API_CONFIG[server];
  if (!serverConfig) {
    throw new Error(`Unknown server: ${server}`);
  }
  
  const endpointPath = serverConfig.ENDPOINTS[endpoint];
  if (!endpointPath) {
    throw new Error(`Unknown endpoint: ${endpoint} for server: ${server}`);
  }
  
  return `${serverConfig.BASE_URL}${endpointPath}`;
};

/**
 * Helper function to get the base URL for a server
 * @param {string} server - The server identifier
 * @returns {string} The base URL for the server
 */
export const getBaseUrl = (server) => {
  const serverConfig = API_CONFIG[server];
  if (!serverConfig) {
    throw new Error(`Unknown server: ${server}`);
  }
  return serverConfig.BASE_URL;
};

// Export for use in components
export const SERVERS = {
  UPLOAD: 'UPLOAD',
  GENERATION: 'GENERATION',
  EVALUATION: 'EVALUATION',
  ANALYTICS: 'ANALYTICS',
  STUDENT: 'STUDENT',
  FACULTY: 'FACULTY'
};

// Export the endpoints
export const ENDPOINTS = {
  // Upload endpoints
  UPLOAD_ASSIGNMENT: 'UPLOAD',
  UPLOAD_ASSIGNMENTS: 'ASSIGNMENTS',
  UPLOAD_ASSIGNMENT_SINGLE: 'ASSIGNMENT',
  UPLOAD_STATUS: 'STATUS',
  
  // Generation endpoints
  GENERATE_ASSIGNMENTS: 'GENERATE',
  GENERATE_PROGRESSIVE: 'GENERATE_PROGRESSIVE',
  GET_DOMAINS: 'DOMAINS',
  EDIT_ASSIGNMENT: 'EDIT_ASSIGNMENT',
  RUBRIC_EDIT: 'RUBRIC_EDIT',
  RUBRIC_DOWNLOAD: 'RUBRIC_DOWNLOAD',
  SAVE_ASSIGNMENT: 'SAVE_ASSIGNMENT',
  DOWNLOAD_ASSIGNMENT: 'DOWNLOAD_ASSIGNMENT',
  DOWNLOAD_MULTIPLE: 'DOWNLOAD_MULTIPLE',
  
  // Student workflow endpoints
  CONTEXT_OPTIONS: 'CONTEXT_OPTIONS',
  GENERATE_QUESTIONS: 'GENERATE_QUESTIONS',
  SELECT_QUESTION: 'SELECT_QUESTION',
  STATUS: 'STATUS',
  SUBMIT: 'SUBMIT',
  LIST_ASSIGNMENTS: 'LIST_ASSIGNMENTS',
  STUDENT_COURSES: 'COURSES',
  AI_CHECK: 'AI_CHECK',

  // Faculty endpoints
  FACULTY_APPROVE_QUESTION: 'QUESTIONS',
  FACULTY_FINALIZE: 'FINALIZE',
  FACULTY_COURSES: 'COURSES',
  FACULTY_STUDENTS: 'STUDENTS',
  FACULTY_EVALUATION_DATA: 'EVALUATION',
  FACULTY_EVALUATION_UPDATE: 'EVALUATE_CRITERION',
  FACULTY_STUDENTS: 'FACULTY_STUDENTS',
  FACULTY_APPROVE_QUESTION: 'FACULTY_APPROVE_QUESTION',
  FACULTY_QUESTIONS_BY_STUDENT: 'FACULTY_QUESTIONS_BY_STUDENT',
  
  // Evaluation endpoints
  EVALUATION_COURSES: 'COURSES',
  EVALUATION_COURSE_FILTERS: 'COURSE_FILTERS',
  EVALUATION_ASSIGNMENTS: 'ASSIGNMENTS',
  EVALUATION_RUBRICS: 'RUBRICS',
  EVALUATION_RUBRIC_EDIT: 'RUBRIC_EDIT',
  SUBMIT_EVALUATION: 'SUBMIT',
  EVALUATE_SUBMISSION: 'EVALUATE',
  EVALUATION_PROGRESS: 'PROGRESS',
  EVALUATION_RESULTS: 'RESULTS',
  EVALUATION_REVIEW: 'REVIEW',
  EVALUATION_REPORT: 'REPORT',
  
  // Analytics endpoints
  ANALYTICS_OVERVIEW: 'OVERVIEW',
  ANALYTICS_USAGE: 'USAGE',
  ANALYTICS_CONTENT: 'CONTENT',
  ANALYTICS_LEARNING: 'LEARNING',
  ANALYTICS_COURSES: 'COURSES',
  ANALYTICS_EXPORT: 'EXPORT',
  
  // Common endpoints
  HEALTH: 'HEALTH',
  STATUS: 'STATUS'
};

export default API_CONFIG;