// // src/AuthContext.js

// import React, { createContext, useState, useContext, useEffect } from 'react';
// import { jwtDecode } from 'jwt-decode';

// const AuthContext = createContext(null);

// export const AuthProvider = ({ children }) => {
//   const [user, setUser] = useState(null);
//   const [loading, setLoading] = useState(true); // To handle initial load

//   // This effect runs on app start to check for an existing token
//   useEffect(() => {
//     const token = localStorage.getItem('token');
//     if (token) {
//       try {
//         const decoded = jwtDecode(token);
//         if (decoded.exp * 1000 > Date.now()) {
//           setUser({ username: decoded.sub });
//         } else {
//           localStorage.removeItem('token');
//         }
//       } catch (error) {
//         localStorage.removeItem('token');
//       }
//     }
//     setLoading(false); // Finished checking token
//   }, []);

//   const login = async (username, password) => {
//     const formData = new URLSearchParams();
//     formData.append('username', username);
//     formData.append('password', password);

//     const res = await fetch("http://localhost:8000/login", {
//       method: "POST",
//       headers: { "Content-Type": "application/x-www-form-urlencoded" },
//       body: formData,
//     });

//     if (!res.ok) {
//       const errorData = await res.json();
//       throw new Error(errorData.detail || "Login failed");
//     }

//     const data = await res.json();
//     const token = data.access_token;
    
//     localStorage.setItem('token', token);
//     const decoded = jwtDecode(token);
//     setUser({ username: decoded.sub });
//   };

//   const logout = () => {
//     localStorage.removeItem('token');
//     setUser(null);
//   };

//   const value = { user, login, logout, loading };

//   return (
//     <AuthContext.Provider value={value}>
//       {children}
//     </AuthContext.Provider>
//   );
// };

// // Custom hook for easy access to the context
// export const useAuth = () => {
//   return useContext(AuthContext);
// };

// src/components/AuthContext.jsx

import React, { createContext, useState, useContext, useEffect } from 'react';
import { jwtDecode } from 'jwt-decode';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const decoded = jwtDecode(token);
        if (decoded.exp * 1000 > Date.now()) {
          setUser({ username: decoded.sub });
        } else {
          localStorage.removeItem('token');
        }
      } catch (error) {
        localStorage.removeItem('token');
      }
    }
    setLoading(false);
  }, []);

  // This login function simply takes the token and updates the state
  const login = (token) => {
    localStorage.setItem('token', token);
    const decoded = jwtDecode(token);
    setUser({ username: decoded.sub });
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  const value = { user, login, logout, loading };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  return useContext(AuthContext);
};