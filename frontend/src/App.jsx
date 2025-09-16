import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import Footer from './components/Footer'
import Home from './pages/Home'
import GenerateAssignment from './pages/GenerateAssignment'
import Evaluation from './pages/Evaluation'
import UploadPastAssignment from './pages/UploadPastAssignment'
import Analytics from './pages/Analytics'
import './styles/App.css'

function App() {
  return (
    <div className="app">
      <Header />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/generate-assignment" element={<GenerateAssignment />} />
          <Route path="/evaluation" element={<Evaluation />} />
          <Route path="/upload-past-assignment" element={<UploadPastAssignment />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}

export default App
