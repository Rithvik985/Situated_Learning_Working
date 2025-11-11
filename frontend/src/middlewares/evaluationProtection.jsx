import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

const EvaluationRouteProtection = ({ children }) => {
  const location = useLocation();

  // Check if we have the required state from the workflow
  const hasValidState = location.state && 
    (location.state.studentId || location.state.fromWorkflow);

  // If trying to access directly without state, redirect to workflow
  if (!hasValidState) {
    return <Navigate to="/student-workflow" replace />;
  }

  return children;
};

export default EvaluationRouteProtection;