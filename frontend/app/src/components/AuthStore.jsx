// src/authStore.js

import { create } from 'zustand';
import { jwtDecode } from 'jwt-decode';

export const useAuthStore = create((set) => ({
  user: null,
  loading: true,
  
  // Action to check for a token in localStorage when the app starts
  checkAuth: () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const decoded = jwtDecode(token);
        if (decoded.exp * 1000 > Date.now()) {
          set({ user: { username: decoded.sub } });
        } else {
          localStorage.removeItem('token');
        }
      } catch (error) {
        localStorage.removeItem('token');
      }
    }
    set({ loading: false });
  },

  // Action to handle logging in
  login: async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const res = await fetch("http://localhost:8000/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded", 
        "Accept": "application/json",
      },
      
      body: formData,
    });

    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || "Login failed");
    }

    const data = await res.json();
    const token = data.access_token;
    
    localStorage.setItem('token', token);
    const decoded = jwtDecode(token);
    set({ user: { username: decoded.sub } });
  },

  // Action to handle logging out
  logout: () => {
    localStorage.removeItem('token');
    set({ user: null });
  },
}));

// Run the initial auth check as soon as the app loads
useAuthStore.getState().checkAuth();