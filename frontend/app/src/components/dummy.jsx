import './App.css';
import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from "react-router-dom";
import Application from './components/Application';
import Login from './components/login';
import Signup from './components/Signup';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(true);

  return (
    <Router>
      {/* Show nav only if authenticated */}
      {isAuthenticated && (
        <nav className="p-4 bg-gray-200 flex gap-4">
          <Link to="/" className="text-blue-600 font-semibold">Home</Link>
          <Link to="/dashboard" className="text-blue-600 font-semibold">Dashboard</Link>
          <button
            onClick={() => setIsAuthenticated(false)}
            className="ml-auto text-red-600 font-semibold"
          >
            Logout
          </button>
        </nav>
      )}

      <Routes>
        {/* Default route → If logged in go to app, else login */}
        <Route
          path="/"
          element={
            isAuthenticated ? <Application /> : <Navigate to="/login" replace />
          }
        />

        {/* Protect Application routes */}
        <Route
          path="/*"
          element={
            isAuthenticated ? <Application /> : <Navigate to="/login" replace />
          }
        />

        {/* Login & Signup remain open */}
        <Route
          path="/login"
          element={<Login setIsAuthenticated={setIsAuthenticated} />}
        />
        <Route path="/signup" element={<Signup />} />
      </Routes>
    </Router>
  );
}

export default App;
