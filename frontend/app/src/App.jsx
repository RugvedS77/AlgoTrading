import './App.css';
import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from "react-router-dom";
import Application from './components/Application';
import Login from './components/Login';
import Signup from './components/Signup';
import {useAuthStore} from './components/AuthStore';


function ProtectedRoute({ children }) {
  const { user, loading } = useAuthStore();
  if (loading) return <div>Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  return (
    
    <Router>
      <Routes>
        {/* Default route → If logged in go to app, else login */}
        {/* <Route
          path="/"
          element={isAuthenticated ? <Application /> : <Navigate to="/login" replace />}
        /> */}
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        {/* Protect Application routes */}
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <Application />
            </ProtectedRoute>
          }
        />

        {/* Login & Signup remain open */}
        {/* <Route path="/login" element={<Login setIsAuthenticated={setIsAuthenticated} />} />
        <Route path="/signup" element={<Signup />} /> */}
        
      </Routes>
    </Router>
  );
}


export default App;



// // src/App.js
// import './App.css';
// import React from 'react';
// import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
// import Application from './components/Application';
// import Login from './components/Login';
// import Signup from './components/Signup';
// import { AuthProvider, useAuth } from './components/AuthContext';

// function ProtectedRoute({ children }) {
//   const { user, loading } = useAuth();

//   if (loading) {
//     return <div>Loading session...</div>;
//   }

//   if (!user) {
//     return <Navigate to="/login" replace />;
//   }

//   return children;
// }

// function App() {
//   // REMOVED: No more local state for authentication here
//   // const [isAuthenticated, setIsAuthenticated] = useState(false);

//   return (
//     <AuthProvider>
//       <Router>
//         <Routes>
//           {/* Login no longer receives any props */}
//           <Route path="/login" element={<Login />} />
//           <Route path="/signup" element={<Signup />} />

//           <Route
//             path="/*"
//             element={
//               <ProtectedRoute>
//                 <Application />
//               </ProtectedRoute>
//             }
//           />
//         </Routes>
//       </Router>
//     </AuthProvider>
//   );
// }

// export default App;