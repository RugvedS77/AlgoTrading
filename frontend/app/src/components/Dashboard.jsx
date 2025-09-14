import React, { useState, useEffect } from "react";
import StockChart from "./StockChart";

function Dashboard({ portfolio, setPortfolio, balance, setBalance }) {
  const [ticker, setTicker] = useState("None"); // Default to None
  const [jsonData, setJsonData] = useState([]);
  const [shares, setShares] = useState(0);
  const [username, setUsername] = useState(""); // Username state

  useEffect(() => {
    if (ticker !== "None") {
      fetch("/assets/Tata_motors_1_day_data.json")
        .then((res) => res.json())
        .then((data) => setJsonData(data))
        .catch((err) => console.error("Error loading JSON:", err));
    } else {
      setJsonData([]);
    }
  }, [ticker]);

  const lastPrice = jsonData.length > 0 ? jsonData[jsonData.length - 1].close : 0;

  const handleSharesChange = (e) => {
    const value = parseInt(e.target.value);
    setShares(isNaN(value) || value < 0 ? 0 : value);
  };

  const handleBuy = () => {
    if (ticker === "None") return alert("Select a ticker first!");
    if (shares <= 0) return alert("Number of shares must be greater than 0");
    const cost = lastPrice * shares;
    if (cost > balance) return alert("Not enough balance!");

    setBalance((prev) => prev - cost);

    setPortfolio((prev) => {
      const existing = prev.find((p) => p.ticker === ticker);
      if (existing) {
        existing.shares += shares;
        existing.buyPrice = lastPrice;
        return [...prev];
      }
      return [...prev, { ticker, shares, buyPrice: lastPrice }];
    });

    alert(`Bought ${shares} shares at ₹${lastPrice} each for ₹${cost}`);
    setShares(0);
  };

  const handleSell = () => {
    if (ticker === "None") return alert("Select a ticker first!");
    if (shares <= 0) return alert("Number of shares must be greater than 0");

    const existing = portfolio.find((p) => p.ticker === ticker);
    if (!existing || existing.shares < shares)
      return alert("Not enough shares to sell!");

    const revenue = lastPrice * shares;

    setBalance((prev) => prev + revenue);

    setPortfolio((prev) =>
      prev
        .map((p) =>
          p.ticker === ticker ? { ...p, shares: p.shares - shares } : p
        )
        .filter((p) => p.shares > 0)
    );

    alert(`Sold ${shares} shares at ₹${lastPrice} each for ₹${revenue}`);
    setShares(0);
  };

  const handleStart = () => {
    console.log("Ticker:", ticker);
    console.log("Username:", username);
  };

  const signals = [
    { type: "buy", price: lastPrice - 5 },
    { type: "sell", price: lastPrice + 5 },
  ];

  return (
    <div className="p-6 bg-gradient-to-br from-gray-50 to-gray-100 min-h-screen">
      {/* Balance Section */}
      <div className="mb-6 p-6 bg-white rounded-2xl shadow-md flex justify-between items-center">
        <span className="font-semibold text-xl text-gray-700">💰 Current Balance</span>
        <span className="text-green-600 font-bold text-2xl">
          ₹{balance.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
        </span>
      </div>

      {/* Grid: Left Controls & Right Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Panel: Controls */}
        <div className="col-span-1 space-y-6">
          {/* Ticker Selection */}
          <div className="p-6 bg-white rounded-2xl shadow-md">
            <label className="font-semibold text-gray-700 block mb-2">
              Select Ticker:
            </label>
            <select
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              className="w-full border px-3 py-2 rounded-lg focus:ring-2 focus:ring-blue-400"
            >
              <option value="None">None</option>
              <option value="Tata Motors">Tata Motors</option>
            </select>
          </div>

          {/* Signals */}
          <div className="p-6 bg-white rounded-2xl shadow-md">
            <h2 className="font-bold text-lg mb-3 text-gray-700">📈 Signals</h2>
            <ul className="space-y-2">
              {signals.map((s, idx) => (
                <li
                  key={idx}
                  className={`font-medium ${
                    s.type === "buy" ? "text-green-600" : "text-red-600"
                  }`}
                >
                  {s.type.toUpperCase()} at ₹{s.price}
                </li>
              ))}
            </ul>
          </div>

          {/* Buy/Sell Form */}
          <div className="p-6 bg-white rounded-2xl shadow-md space-y-4">
            <p className="font-semibold text-gray-700">📊 Last Price: ₹{lastPrice}</p>
            <input
              type="number"
              placeholder="Number of shares"
              value={shares}
              onChange={handleSharesChange}
              className="w-full border px-3 py-2 rounded-lg focus:ring-2 focus:ring-blue-400"
            />
            <div className="flex gap-4">
              <button
                onClick={handleBuy}
                className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold shadow hover:bg-blue-700 transition"
              >
                Buy
              </button>
              <button
                onClick={handleSell}
                className="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg font-semibold shadow hover:bg-red-700 transition"
              >
                Sell
              </button>
            </div>
          </div>

          {/* Username Input & Start Button */}
          <div className="p-6 bg-white rounded-2xl shadow-md space-y-3">
            <label className="font-semibold text-gray-700 block">Enter Username:</label>
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full border px-3 py-2 rounded-lg focus:ring-2 focus:ring-blue-400"
            />
            <button
              onClick={handleStart}
              className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold shadow hover:bg-blue-700 transition"
            >
              Start
            </button>
          </div>
        </div>

        {/* Right Panel: Stock Chart */}
        <div className="col-span-2 p-6 bg-white rounded-2xl shadow-md">
          <h2 className="font-bold text-lg mb-4 text-gray-700">📉 Stock Chart</h2>
          <StockChart />
        </div>
      </div>

      {/* Full-width Execution Analysis Section */}
      <div className="mt-6 p-6 bg-white rounded-2xl shadow-md">
        <h2 className="font-bold text-xl mb-4 text-gray-700">📝 Execution Analysis</h2>
        <p className="text-gray-700">
          Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla facilisi. 
          Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium.
        </p>
      </div>
    </div>
  );
}

export default Dashboard;
