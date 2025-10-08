import React, { useState, useEffect } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import axios from 'axios';

const ProtectedRoute = () => {
  const [isValidSession, setIsValidSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.post(`/sla/verify-session`, {}, { withCredentials: true })
      .then((response) => {
        if (response.data.isValid) {
          setIsValidSession(true);
        } else {
          setIsValidSession(false);
        }
      })
      .catch(() => {
        setIsValidSession(false);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!isValidSession) {
    // Redirect to /qprs instead of /
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
};

export default ProtectedRoute;
