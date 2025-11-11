import React from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import Header from './components/Header'
import Footer from './components/Footer'
import Home from './pages/Home'
import GenerateAssignment from './pages/GenerateAssignment'
import Evaluation from './pages/Evaluation'
import UploadPastAssignment from './pages/UploadPastAssignment'
import Analytics from './pages/Analytics'
import StudentWorkflow from './pages/StudentWorkflow'
import FacultyDashboard from './pages/FacultyDashboard'
import RubricManagement from './pages/RubricManagement'
import FacultyReviewPage from './pages/FacultyReviewPage'
import StudentEvaluation from './pages/StudentEvaluation'
import FacultyEvaluation from './pages/FacultyEvaluation'
import StudentPDFUpload from './pages/StudentPDFUpload'

import './styles/App.css'
import ProtectedRoute from './middlewares/routeprotection'

function App() {
  const location = useLocation()
  const hideLayout = location.pathname === "/" // hide header/footer only on home

  return (
    <div className="app">
      {!hideLayout && <Header />}
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/student/evaluation" element={<StudentEvaluation />} />
          <Route path="/student-pdf-upload" element={<StudentPDFUpload />} />

          <Route element={<ProtectedRoute />}>
            <Route path="/generate-assignment" element={<GenerateAssignment />} />
            <Route path="/faculty/evaluation" element={<FacultyEvaluation />} />
            <Route path="/student-workflow" element={<StudentWorkflow />} />
            <Route path="/faculty/dashboard" element={<FacultyDashboard />} />
            <Route path="/faculty/review/:studentId" element={<FacultyReviewPage />} />
            <Route path="/upload-past-assignment" element={<UploadPastAssignment />} />
            <Route path="/dashboard" element={<Analytics />} />
            <Route path="/rubric-management" element={<RubricManagement />} />
            {/* <Route path="/faculty-table" element={<StudentsTable />} /> */}
            <Route path="/evaluate-assignment" element={<Evaluation />} />



          </Route>
        </Routes>
      </main>
       <Footer />
    </div>
  )
}

export default App
