/**
 * Centralized endpoint configuration for the Situated Learning System
 */

export const ENDPOINTS = {
  // Student Service endpoints
  STUDENT: {
    ASSIGNMENTS: '/assignments',
    ANALYZE: '/analyze',
    SUBMIT_TO_FACULTY: '/submit-to-faculty',
    MY_SUBMISSIONS: '/my-submissions',
    SAVED_ASSIGNMENTS: '/assignments',
    UPLOAD_SUBMISSION: '/upload-submission'
  },
  // Faculty Service endpoints
  FACULTY: {
    PENDING_SUBMISSIONS: '/pending-submissions',   // used with getBaseUrl('FACULTY')
    EVALUATE_SUBMISSION: '/pending-submissions',   // append /{id}/evaluate in call
    GET_SUBMISSION: '/submissions',
    APPROVE_QUESTION: '/questions',               // if you need single submission retrieval
  },


  // Evaluation Service endpoints
  EVALUATION: {
    COURSES: '/courses',
    COURSE_FILTERS: '/courses',
    ASSIGNMENTS: '/assignments',
    RUBRICS: '/rubrics',
    RUBRIC_EDIT: '/rubrics',
    SUBMIT: '/submissions/upload',
    STUDENT_SWOT: '/student/swot',
    FACULTY_EVALUATE: '/faculty/evaluate',
    PENDING_SUBMISSIONS: '/faculty/pending',
    REVIEW: '/submissions',
    EVALUATE_CRITERION: '/evaluate',

  }
};