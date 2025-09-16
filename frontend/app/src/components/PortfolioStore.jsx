// src/portfolioStore.js

import { create } from 'zustand';
import { useAuthStore } from './AuthStore'; // To get the username

export const usePortfolioStore = create((set, get) => ({
  portfolio: [],
  balance: 0,
  loading: true,

  fetchPortfolio: async () => {
    const { user } = useAuthStore.getState();
    if (!user?.username) return;

    set({ loading: true });
    try {
      const res = await fetch(`http://localhost:8000/portfolio/${user.username}`);
      const data = await res.json();
      set({ portfolio: data.open_positions || [], balance: data.cash_available || 0 });
    } catch (error) {
      console.error("Failed to fetch portfolio:", error);
    } finally {
      set({ loading: false });
    }
  },

  executeTrade: async (tradeData) => {
    const { user } = useAuthStore.getState();
    if (!user?.username) throw new Error("User not authenticated");

    try {
      const res = await fetch("http://localhost:8000/account/trade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: user.username, ...tradeData }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Trade failed");
      
      // After a successful trade, refresh the portfolio data
      await get().fetchPortfolio();
      return { success: true, message: data.message };
    } catch (error) {
      alert(`Trade Error: ${error.message}`);
      return { success: false, message: error.message };
    }
  },
}));

// Listen to changes in the auth store to automatically fetch the portfolio on login
useAuthStore.subscribe(
  (state) => state.user,
  (user) => {
    if (user) {
      usePortfolioStore.getState().fetchPortfolio();
    }
  }
);