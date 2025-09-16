import React, { useState } from "react";
import { usePortfolioStore } from "./PortfolioStore"; // 1. Import the global store hook

// 2. The component no longer needs portfolio or balance as props
function Home({ handleAddMoney, lastPrice }) {
  // 3. Get live portfolio, balance, and loading state directly from the store
  const { portfolio, balance, loading } = usePortfolioStore();

  // In a real app, you would fetch live market prices for each ticker
  // const [lastPrice, setLastPrice] = useState({ TATAMOTORS: 1000 });

  // 4. Show a loading message while the initial portfolio is being fetched
  if (loading) {
    return <div className="p-6 text-center">Loading Portfolio...</div>;
  }

  // --- Calculations use the new property names ---
  const totalCost = portfolio.reduce(
    (acc, p) => acc + p.average_buy_price * p.quantity,
    0
  );
  const totalCurrent = portfolio.reduce(
    (acc, p) => acc + (lastPrice[p.ticker] || p.average_buy_price) * p.quantity,
    0
  );
  const totalPercent =
    totalCost > 0
      ? (((totalCurrent - totalCost) / totalCost) * 100).toFixed(2)
      : 0;

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <h1 className="text-4xl font-bold mb-6 text-gray-800">📊 Portfolio</h1>

      <div className="mb-6 flex items-center gap-4">
        <button
          onClick={handleAddMoney}
          className="bg-green-600 hover:bg-green-700 transition text-white px-5 py-2 rounded-lg shadow"
        >
          + Add Money
        </button>
        <span className="text-lg font-semibold text-gray-700 bg-white px-4 py-2 rounded-lg shadow">
          Balance: <span className="text-green-700">₹{balance.toLocaleString("en-IN")}</span>
        </span>
      </div>

      <div className="bg-white rounded-xl shadow-lg p-6">
        {portfolio.length === 0 ? (
          <p className="text-gray-600 text-lg">No stocks owned yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-200 text-gray-700 text-sm uppercase">
                  <th className="px-4 py-2">Ticker</th>
                  <th className="px-4 py-2">Quantity</th>
                  <th className="px-4 py-2">Avg. Buy Price</th>
                  <th className="px-4 py-2">Total Cost</th>
                  <th className="px-4 py-2">Current Value</th>
                  <th className="px-4 py-2">% Change</th>
                </tr>
              </thead>
              <tbody>
                {/* 5. The table now maps over the portfolio using the correct property names */}
                {portfolio.map((p) => {
                  const currentVal = (lastPrice[p.ticker] || p.average_buy_price) * p.quantity;
                  const totalBuy = p.average_buy_price * p.quantity;
                  const percent =
                    totalBuy > 0
                      ? (((currentVal - totalBuy) / totalBuy) * 100).toFixed(2)
                      : 0;

                  return (
                    <tr
                      key={p.ticker} // Use a more stable key
                      className="odd:bg-gray-50 even:bg-white hover:bg-gray-100 transition"
                    >
                      <td className="px-4 py-2 font-medium text-gray-800">{p.ticker}</td>
                      <td className="px-4 py-2">{p.quantity}</td>
                      <td className="px-4 py-2">₹{p.average_buy_price.toFixed(2)}</td>
                      <td className="px-4 py-2">₹{totalBuy.toFixed(2)}</td>
                      <td className="px-4 py-2">₹{currentVal.toFixed(2)}</td>
                      <td className={`px-4 py-2 font-semibold ${percent >= 0 ? "text-green-600" : "text-red-600"}`}>
                        {percent}%
                      </td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr className="bg-gray-200 font-bold text-gray-800">
                  <td className="px-4 py-2" colSpan={3}>
                    Total
                  </td>
                  <td className="px-4 py-2">₹{totalCost.toFixed(2)}</td>
                  <td className="px-4 py-2">₹{totalCurrent.toFixed(2)}</td>
                  <td
                    className={`px-4 py-2 ${
                      totalPercent >= 0 ? "text-green-700" : "text-red-700"
                    }`}
                  >
                    {totalPercent}%
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default Home;
