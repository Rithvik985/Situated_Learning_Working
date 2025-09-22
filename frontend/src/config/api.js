/**
 * API Configuration for Situated Learning System Frontend
 * Manages endpoints for the separated FastAPI servers
 */

const API_CONFIG = {
  // Upload Server (Port 8020)
  UPLOAD: {
    BASE_URL: '/uploadAss',
    ENDPOINTS: {
      UPLOAD: '/past-assignments',
      ASSIGNMENTS: '/assignments',
      ASSIGNMENT: '/assignments',
      STATUS: '/status',
      HEALTH: '/health'
    }
  },

  // Generation Server (Port 8021)
  GENERATION: {
    BASE_URL: '/generation',
    ENDPOINTS: {
      GENERATE: '/generate',
      GENERATE_PROGRESSIVE: '/generate-progressive',
      DOMAINS: '/domains',
      EDIT_ASSIGNMENT: '/assignments',
      RUBRIC_GENERATE: '/rubric/generate',
      RUBRIC_EDIT: '/rubric',
      RUBRIC_DOWNLOAD: '/rubric',
      SAVE_ASSIGNMENT: '/assignments/save',
      DOWNLOAD_ASSIGNMENT: '/assignments',
      DOWNLOAD_MULTIPLE: '/assignments/download',
      HEALTH: '/health',
      STATUS: '/api/status'
    }
  },

  // Evaluation Server (Port 8022)
  EVALUATION: {
    BASE_URL: '/evaluation',
    ENDPOINTS: {
      COURSES: '/courses',
      COURSE_FILTERS: '/courses',
      ASSIGNMENTS: '/courses',
      RUBRICS: '/assignments',
      RUBRIC_GENERATE: '/assignments',
      RUBRIC_EDIT: '/rubric',
      SUBMIT: '/submissions/upload',
      EVALUATE: '/evaluate',
      PROGRESS: '/status',
      RESULTS: '/assignments',
      REVIEW: '/submissions',
      REPORT: '/assignments',
      HEALTH: '/health',
      STATUS: '/api/status'
    }
  },

  // Analytics Server (Port 8023)
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
      STATUS: '/api/status'
    }
  }
};

// Helper function to get full URL for an endpoint
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

// Helper function to get base URL for a server
export const getBaseUrl = (server) => {
  const serverConfig = API_CONFIG[server];
  if (!serverConfig) {
    throw new Error(`Unknown server: ${server}`);
  }
  return serverConfig.BASE_URL;
};

// Server names for easy reference
export const SERVERS = {
  UPLOAD: 'UPLOAD',
  GENERATION: 'GENERATION',
  EVALUATION: 'EVALUATION',
  ANALYTICS: 'ANALYTICS'
};

// Endpoint names for easy reference
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
  RUBRIC_GENERATE: 'RUBRIC_GENERATE',
  RUBRIC_EDIT: 'RUBRIC_EDIT',
  RUBRIC_DOWNLOAD: 'RUBRIC_DOWNLOAD',
  SAVE_ASSIGNMENT: 'SAVE_ASSIGNMENT',
  DOWNLOAD_ASSIGNMENT: 'DOWNLOAD_ASSIGNMENT',
  DOWNLOAD_MULTIPLE: 'DOWNLOAD_MULTIPLE',
  
  // Evaluation endpoints
  EVALUATION_COURSES: 'COURSES',
  EVALUATION_COURSE_FILTERS: 'COURSE_FILTERS',
  EVALUATION_ASSIGNMENTS: 'ASSIGNMENTS',
  EVALUATION_RUBRICS: 'RUBRICS',
  EVALUATION_RUBRIC_GENERATE: 'RUBRIC_GENERATE',
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