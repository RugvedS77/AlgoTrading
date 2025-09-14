import React, { useState, useEffect } from "react";
import { Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./Dashboard";
import Home from "./Home";

function Application() {
  const [portfolio, setPortfolio] = useState([]);
  const [balance, setBalance] = useState(100000);
  const [lastPrice, setLastPrice] = useState({ "Tata Motors": 700 });

  // Fetch stock price dynamically
  useEffect(() => {
    fetch("/assets/Tata_motors_1_day_data.json")
      .then((res) => res.json())
      .then((data) => {
        if (data.length > 0) {
          setLastPrice({ "Tata Motors": data[data.length - 1].close });
        }
      })
      .catch((err) => console.error("Error loading JSON:", err));
  }, []);

  const handleAddMoney = () => {
    const amount = parseFloat(prompt("Enter amount to add:"));
    if (!isNaN(amount) && amount > 0) setBalance((prev) => prev + amount);
  };

  return (
    <div className="min-h-screen bg-gray-100 text-gray-900">
      {/* Single Header / Navbar */}
      <header className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto flex justify-between items-center py-4 px-6">
          <h1 className="text-2xl font-bold text-blue-600 flex items-center gap-2">
            📈 Stock Portfolio
          </h1>
          <nav className="flex gap-6">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `font-medium transition ${
                  isActive ? "text-blue-600 border-b-2 border-blue-600" : "text-gray-700 hover:text-blue-600"
                }`
              }
            >
              Home
            </NavLink>
            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                `font-medium transition ${
                  isActive ? "text-blue-600 border-b-2 border-blue-600" : "text-gray-700 hover:text-blue-600"
                }`
              }
            >
              Dashboard
            </NavLink>
          </nav>
        </div>
      </header>

      {/* Routes */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <Routes>
          <Route
            path="/"
            element={
              <Home
                portfolio={portfolio}
                balance={balance}
                handleAddMoney={handleAddMoney}
                lastPrice={lastPrice}
              />
            }
          />
          <Route
            path="/dashboard"
            element={
              <Dashboard
                portfolio={portfolio}
                setPortfolio={setPortfolio}
                balance={balance}
                setBalance={setBalance}
              />
            }
          />
        </Routes>
      </main>
    </div>
  );
}

export default Application;
