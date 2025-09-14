import './App.css';
import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from "react-router-dom";
import Application from './components/Application';
import Login from './components/login';
import Signup from './components/Signup';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  return (
    <Router>
      <Routes>
        {/* Default route → If logged in go to app, else login */}
        <Route
          path="/"
          element={isAuthenticated ? <Application /> : <Navigate to="/login" replace />}
        />

        {/* Protect Application routes */}
        <Route
          path="/*"
          element={isAuthenticated ? <Application /> : <Navigate to="/login" replace />}
        />

        {/* Login & Signup remain open */}
        <Route path="/login" element={<Login setIsAuthenticated={setIsAuthenticated} />} />
        <Route path="/signup" element={<Signup />} />
      </Routes>
    </Router>
  );
}


export default App;
