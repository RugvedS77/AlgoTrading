// src/components/PortfolioContext.jsx

import React, { createContext, useState, useContext, useEffect } from 'react';
import { useAuth } from './AuthContext'; // To get the logged-in user

const PortfolioContext = createContext(null);

export const PortfolioProvider = ({ children }) => {
  const { user } = useAuth();
  const [portfolio, setPortfolio] = useState([]);
  const [balance, setBalance] = useState(0);
  const [loading, setLoading] = useState(true);

  // This function fetches the latest portfolio data from the backend
  const fetchPortfolio = async () => {
    if (user?.username) {
      setLoading(true);
      try {
        const res = await fetch(`http://localhost:8000/portfolio/${user.username}`);
        if (!res.ok) throw new Error("Could not fetch portfolio data.");
        
        const data = await res.json();
        setPortfolio(data.open_positions || []);
        setBalance(data.cash_available || 0);
      } catch (error) {
        console.error("Failed to fetch portfolio:", error);
      } finally {
        setLoading(false);
      }
    }
  };

  // Fetch the portfolio as soon as the user is authenticated
  useEffect(() => {
    fetchPortfolio();
  }, [user]);

  // This function sends a trade request to the backend
  const executeTrade = async (tradeData) => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/account/trade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: user.username, ...tradeData }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Trade failed");
      
      // After a successful trade, refresh the portfolio data
      await fetchPortfolio(); 
      return { success: true, message: data.message };
    } catch (error) {
      alert(error.message); // Show the error from the backend to the user
      return { success: false, message: error.message };
    } finally {
        setLoading(false);
    }
  };

  const value = { portfolio, balance, loading, executeTrade, fetchPortfolio };

  return (
    <PortfolioContext.Provider value={value}>
      {children}
    </PortfolioContext.Provider>
  );
};

// Custom hook for easy access to the context
export const usePortfolio = () => {
  return useContext(PortfolioContext);
};