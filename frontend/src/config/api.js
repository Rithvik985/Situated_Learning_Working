// API Configuration
const API_CONFIG = {
  UPLOAD_URL: process.env.NODE_ENV === 'production' ? 'http://upload-server:8001' : 'http://localhost:8001',
  GENERATION_URL: process.env.NODE_ENV === 'production' ? 'http://generation-server:8017' : 'http://localhost:8017',
  EVALUATION_URL: process.env.NODE_ENV === 'production' ? 'http://evaluation-server:8019' : 'http://localhost:8019',
  ANALYTICS_URL: process.env.NODE_ENV === 'production' ? 'http://analytics-server:8004' : 'http://localhost:8004'
}

// Helper function to get the full URL for upload endpoints
export const getUploadUrl = (endpoint) => `${API_CONFIG.UPLOAD_URL}${endpoint}`

// Helper function to get the full URL for generation endpoints
export const getGenerationUrl = (endpoint) => `${API_CONFIG.GENERATION_URL}${endpoint}`

// Helper function to get the full URL for evaluation endpoints
export const getEvaluationUrl = (endpoint) => `${API_CONFIG.EVALUATION_URL}${endpoint}`

// Helper function to get the full URL for analytics endpoints
export const getAnalyticsUrl = (endpoint) => `${API_CONFIG.ANALYTICS_URL}${endpoint}`

export { API_CONFIG }