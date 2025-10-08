import React from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import Header from './components/Header'
import Footer from './components/Footer'
import Home from './pages/Home'
import GenerateAssignment from './pages/GenerateAssignment'
import Evaluation from './pages/Evaluation'
import UploadPastAssignment from './pages/UploadPastAssignment'
import Analytics from './pages/Analytics'
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
          <Route element={<ProtectedRoute />}>
          <Route path="/generate-assignment" element={<GenerateAssignment />} />
          <Route path="/evaluate-assignment" element={<Evaluation />} />
          <Route path="/upload-past-assignment" element={<UploadPastAssignment />} />
          <Route path="/dashboard" element={<Analytics />} />
          </Route>

        </Routes>
      </main>
       <Footer />
    </div>
  )
}

export default App
