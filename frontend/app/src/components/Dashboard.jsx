import React, { useState, useEffect } from "react";
import StockChart from "./StockChart";
// IMPORTANT: Add these new icons to your import
import { CheckCircle2, XCircle, ChevronDown } from 'lucide-react';
// import {create} from "zustand";
import { useAuthStore } from "./AuthStore";
import { usePortfolioStore } from "./PortfolioStore";

function Dashboard(
  // { portfolio, setPortfolio, balance, setBalance }
) {
  // --- STATE MANAGEMENT (Unchanged) ---
  const [ticker, setTicker] = useState("None");
  const [jsonData, setJsonData] = useState([]);
  const [shares, setShares] = useState(0);
  // const [username, setUsername] = useState("");

  // const { user } = useAuthStore();
  const { user } = useAuthStore();
  const { executeTrade, portfolio, balance  } = usePortfolioStore();
  const [openAccordion, setOpenAccordion] = useState(null);

  // --- PIPELINE STATE (Unchanged) ---
  const [isLoading, setIsLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState("");

  // --- EXPLAINER AGENT (Unchanged) ---
  const [areExplanationsLoading, setAreExplanationsLoading] = useState(false);
  const [allExplanations, setAllExplanations] = useState([]);
  const [explanationsError, setExplanationsError] = useState("");

  // --- DATA FETCHING WITH AUTO-REFRESH (Unchanged) ---
  useEffect(() => {
    let interval;
    if (ticker !== "None") {
      const fetchData = () => {
        fetch("/assets/Tata_motors_1_day_data.json")
          .then((res) => res.json())
          .then((data) => {
            if (data.length === 0) return;
            const firstRowDate = new Date(data[0].date);
            const jsonDay = firstRowDate.toISOString().split("T")[0];
            const now = new Date();
            const hours = now.getHours();
            const minutes = now.getMinutes();
            const cutoff = new Date(`${jsonDay} ${hours}:${minutes}:00`);
            const filteredData = data.filter(
              (row) => new Date(row.date) <= cutoff
            );
            setJsonData(filteredData);
          })
          .catch((err) => console.error("Error loading JSON:", err));
      };
      fetchData();
      interval = setInterval(fetchData, 60 * 1000);
    } else {
      setJsonData([]);
    }
    return () => clearInterval(interval);
  }, [ticker]);

  // --- CORE LOGIC (Unchanged) ---
  const lastPrice =
    jsonData.length > 0 ? jsonData[jsonData.length - 1].close : 0;
  
  // const portfolioValue = portfolio.reduce((total, stock) => {
  //   if (stock.ticker === ticker) {
  //       return total + stock.shares * lastPrice;
  //   }
  //   return total + stock.shares * stock.buyPrice;
  // }, 0);
  const portfolioValue = portfolio.reduce((total, p) => {
    const currentPrice = lastPrice; // Simplified for this example
    return total + p.quantity * currentPrice;
  }, 0);

  // --- HANDLER FUNCTIONS (Unchanged) ---
  const handleSharesChange = (e) => {
    const value = parseInt(e.target.value);
    setShares(isNaN(value) || value < 0 ? 0 : value);
  };
  const handleBuy = async () => {
    const result = await executeTrade({
      ticker,
      side: "BUY",
      price: lastPrice,
      quantity: shares,
    });
    if (result.success) {
      // alert(result.message);
      alert(`Bought ${shares} shares of ${ticker} at ₹${lastPrice.toFixed(2)} each.`);
      setShares(0);
    }
  };
  // const handleBuy = () => {
  //   if (ticker === "None") return alert("Select a ticker first!");
  //   if (shares <= 0) return alert("Number of shares must be greater than 0");
  //   const cost = lastPrice * shares;
  //   if (cost > balance) return alert("Not enough balance!");
  //   setBalance((prev) => prev - cost);
  //   setPortfolio((prev) => {
  //     const existing = prev.find((p) => p.ticker === ticker);
  //     if (existing) {
  //       existing.shares += shares;
  //       existing.buyPrice = lastPrice;
  //       return [...prev];
  //     }
  //     return [...prev, { ticker, shares, buyPrice: lastPrice }];
  //   });
  //   alert(`Bought ${shares} shares of ${ticker} at ₹${lastPrice.toFixed(2)} each.`);
  //   setShares(0);
  // };
  const handleSell = async () => {
    const result = await executeTrade({
      ticker,
      side: "SELL",
      price: lastPrice,
      quantity: shares,
    });
    if (result.success) {
      // alert(result.message);
      alert(`Sold ${shares} shares of ${ticker} at ₹${lastPrice.toFixed(2)} each.`);
      setShares(0);
    }
  };

  // const handleSell = () => {
  //   if (ticker === "None") return alert("Select a ticker first!");
  //   if (shares <= 0) return alert("Number of shares must be greater than 0");
  //   const existing = portfolio.find((p) => p.ticker === ticker);
  //   if (!existing || existing.shares < shares)
  //     return alert("Not enough shares to sell!");
  //   const revenue = lastPrice * shares;
  //   setBalance((prev) => prev + revenue);
  //   setPortfolio((prev) =>
  //     prev
  //       .map((p) =>
  //         p.ticker === ticker ? { ...p, shares: p.shares - shares } : p
  //       )
  //       .filter((p) => p.shares > 0)
  //   );
  //   alert(`Sold ${shares} shares of ${ticker} at ₹${lastPrice.toFixed(2)} each.`);
  //   setShares(0);
  // };
  
  const toggleAccordion = (id) => {
    setOpenAccordion(openAccordion === id ? null : id);
  };

  // --- UI HELPERS (Modified for Dark Theme) ---
  const getVerdictStyle = (verdict) => {
    switch (verdict?.toUpperCase()) {
      case 'PROCEED':
        return 'bg-green-900/50 text-green-300 border-green-700';
      case 'PROCEED WITH CAUTION':
        return 'bg-yellow-900/50 text-yellow-300 border-yellow-700';
      case 'REJECT':
        return 'bg-red-900/50 text-red-300 border-red-700';
      default:
        return 'bg-gray-700 text-gray-300 border-gray-600';
    }
  };

  // --- PIPELINE START (Unchanged) ---
  const handleStart = async () => {
    if (ticker === "None" || !user?.username) {
      alert("Please select a ticker and enter a username.");
      return;
    }
    setIsLoading(true);
    setError("");
    setAnalysisResult(null);
    try {
      const stockTicker = "TATAMOTORS";
      const url = `http://localhost:8000/run-pipeline?ticker=${stockTicker}&username=${user.username}`;
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (!response.ok) throw new Error(`Error: ${response.status} ${response.statusText}`);
      const data = await response.json();
      setAnalysisResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // --- FETCH EXPLANATIONS (Unchanged) ---
  const handleFetchExplanations = async () => {
    setAreExplanationsLoading(true);
    setExplanationsError("");
    setAllExplanations([]);
    try {
      const response = await fetch("http://localhost:8000/explainer/results");
      if (!response.ok) throw new Error(`HTTP Error: ${response.statusText}`);
      const data = await response.json();
      setAllExplanations(data.explanations.explanations || []);
      if (data.explanations.explanations?.length > 0) {
        setOpenAccordion(data.explanations.explanations[0].run_id);
      }
    } catch (err) {
      setExplanationsError(err.message);
    } finally {
      setAreExplanationsLoading(false);
    }
  };
  
  // --- RENDER (Redesigned Sections) ---
  return (
    <div className="bg-gray-900 text-gray-300 min-h-screen font-sans">
      <div className="container mx-auto p-4">
        
        <header className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
                <h3 className="text-sm text-gray-400">Balance</h3>
                <p className="text-2xl font-semibold text-green-400">
                    ₹{balance.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </p>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
                <h3 className="text-sm text-gray-400">Portfolio Value</h3>
                <p className="text-2xl font-semibold text-white">
                    ₹{portfolioValue.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </p>
            </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="col-span-1 space-y-6">
            <div className="bg-gray-800 p-4 rounded-lg border border-gray-700 space-y-4">
              <h2 className="text-xl font-bold text-white mb-2">Trading Panel</h2>
              <div>
                <label className="text-sm font-semibold text-gray-400 block mb-1">Stock</label>
                <select value={ticker} onChange={(e) => setTicker(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-600 px-3 py-2 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-none"
                >
                  <option value="None">Select Ticker</option>
                  <option value="Tata Motors">Tata Motors</option>
                </select>
              </div>
              {ticker !== "None" && (
                <>
                  <div className="text-center bg-gray-900/50 p-2 rounded-md">
                    <span className="text-gray-400">Last Price: </span>
                    <span className="font-bold text-lg text-white">₹{lastPrice.toFixed(2)}</span>
                  </div>
                  <div>
                    <label className="text-sm font-semibold text-gray-400 block mb-1">Shares</label>
                    <input type="number" placeholder="0" value={shares} onChange={handleSharesChange}
                      className="w-full bg-gray-900 border border-gray-600 px-3 py-2 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-none"
                    />
                  </div>
                  <div className="flex gap-4">
                    <button onClick={handleBuy} className="flex-1 bg-green-600 text-white px-4 py-2 rounded-md font-semibold shadow-md hover:bg-green-700 transition-colors duration-200">
                      Buy
                    </button>
                    <button onClick={handleSell} className="flex-1 bg-red-600 text-white px-4 py-2 rounded-md font-semibold shadow-md hover:bg-red-700 transition-colors duration-200">
                      Sell
                    </button>
                  </div>
                </>
              )}
            </div>
            {/* <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
                <h2 className="text-xl font-bold text-white mb-3">Portfolio</h2>
                {portfolio.length > 0 ? (
                    <ul className="space-y-2">
                        {portfolio.map((p, index) => (
                            <li key={index} className="flex justify-between items-center bg-gray-900/50 p-2 rounded-md">
                                <div>
                                    <p className="font-semibold text-white">{p.ticker}</p>
                                    <p className="text-xs text-gray-400">Avg. Price: ₹{p.buyPrice.toFixed(2)}</p>
                                </div>
                                <p className="font-mono text-lg">{p.shares}</p>
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p className="text-gray-500 italic text-center py-4">Your portfolio is empty.</p>
                )}
            </div> */}
            {/* MODIFICATION: Portfolio card now uses correct property names */}
            <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
              <h2 className="text-xl font-bold text-white mb-3">Portfolio</h2>
              {portfolio.length > 0 ? (
                <ul className="space-y-2">
                  {/* Use a unique key like p.ticker instead of index */}
                  {portfolio.map((p) => (
                    <li key={p.ticker} className="flex justify-between items-center bg-gray-900/50 p-2 rounded-md">
                      <div>
                        <p className="font-semibold text-white">{p.ticker}</p>
                        {/* FIX: Use 'average_buy_price' */}
                        <p className="text-xs text-gray-400">Avg. Price: ₹{p.average_buy_price.toFixed(2)}</p>
                      </div>
                      {/* FIX: Use 'quantity' */}
                      <p className="font-mono text-lg">{p.quantity}</p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-500 italic text-center py-4">Your portfolio is empty.</p>
              )}
            </div>
            <div className="bg-gray-800 p-4 rounded-lg border border-gray-700 space-y-3">
              <h2 className="text-xl font-bold text-white mb-2">AI Analysis</h2>
              {/* <label className="text-sm font-semibold text-gray-400 block">Username</label>
              <input type="text" placeholder="Enter username" value={username} onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-gray-900 border border-gray-600 px-3 py-2 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-none"
                disabled={isLoading}
              /> */}
              <button onClick={handleStart} disabled={isLoading || !user?.username || ticker === 'None'}
                className="w-full bg-blue-600 text-white px-4 py-2 rounded-md font-semibold shadow-md hover:bg-blue-700 transition-colors duration-200 disabled:bg-gray-600 disabled:cursor-not-allowed"
              >
                {isLoading ? "Analyzing..." : "Start Analysis"}
              </button>
            </div>
          </div>
          
          <div className="col-span-1 lg:col-span-2 bg-gray-800 p-4 rounded-lg border border-gray-700">
            <h2 className="font-bold text-xl text-white mb-4">
              {ticker === 'None' ? 'Stock Chart' : `${ticker} Chart`}
            </h2>
            {ticker !== 'None' ? (
                <StockChart />
            ) : (
                <div className="flex items-center justify-center h-full text-gray-500">
                    <p>Please select a stock to view the chart.</p>
                </div>
            )}
          </div>
        </div>
        
        {/* ============================================= */}
        {/* == NEW REDESIGNED EXECUTION ANALYSIS SECTION == */}
        {/* ============================================= */}
        <div className="mt-6 bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
            <div className="p-4 bg-gray-800/50">
              <h2 className="font-bold text-2xl text-white">📝 Execution Analysis</h2>
            </div>
            <div className="p-6">
              {isLoading && <p className="text-blue-400">Loading analysis from the agentic pipeline...</p>}
              {error && <p className="text-red-400">Error: {error}</p>}
              
              {analysisResult && (
                <div className="space-y-6">
                  {/* Verdict Header */}
                  <div className={`p-4 rounded-md border ${getVerdictStyle(analysisResult.risk_decision.final_verdict)}`}>
                    <h3 className="font-bold text-xl text-white">
                      Final Verdict: {analysisResult.risk_decision.final_verdict}
                    </h3>
                    <p className="mt-1 text-sm italic">{analysisResult.risk_decision.summary_rationale}</p>
                  </div>
                  
                  {/* Pros and Cons */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-semibold text-white mb-3">Key Positive Factors</h4>
                      <ul className="space-y-3">
                        {analysisResult.risk_decision.key_positive_factors.map((factor, i) => (
                          <li key={i} className="flex items-start text-sm">
                            <CheckCircle2 className="text-green-500 mr-3 mt-0.5 flex-shrink-0" size={18} />
                            <span>{factor}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-semibold text-white mb-3">Key Risks & Concerns</h4>
                      <ul className="space-y-3">
                        {analysisResult.risk_decision.key_risks_and_concerns.map((risk, i) => (
                          <li key={i} className="flex items-start text-sm">
                            <XCircle className="text-red-500 mr-3 mt-0.5 flex-shrink-0" size={18} />
                            <span>{risk}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Allocation Proposal */}
                  <div className="pt-4 border-t border-gray-700">
                    <h4 className="font-semibold text-white mb-3">Capital Allocator's Proposal</h4>
                    <div className="text-sm p-4 bg-gray-900/70 rounded-md grid grid-cols-2 gap-4">
                      <div><strong className="text-gray-400 block">Intent:</strong> {analysisResult.allocation.intent}</div>
                      <div><strong className="text-gray-400 block">Side:</strong> <span className={`px-2 py-0.5 rounded-full text-xs ${analysisResult.allocation.side === 'BUY' ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'}`}>{analysisResult.allocation.side}</span></div>
                      <div><strong className="text-gray-400 block">Proposed Allocation:</strong> ₹{analysisResult.allocation.allocation_cash.toFixed(2)}</div>
                      <div><strong className="text-gray-400 block">Stop-Loss:</strong> {analysisResult.allocation.suggested_stop_loss || 'N/A'}</div>
                      <div className="col-span-2"><strong className="text-gray-400 block">Rationale:</strong> {analysisResult.allocation.rationale}</div>
                    </div>
                  </div>
                </div>
              )}
              
              {!isLoading && !analysisResult && !error && (
                <p className="text-gray-500 text-center py-8">Click "Start Analysis" to get the latest trading signal and execution plan.</p>
              )}
            </div>
        </div>

        {/* ================================================== */}
        {/* == NEW REDESIGNED HISTORICAL EXPLANATIONS SECTION == */}
        {/* ================================================== */}
        <div className="mt-6 bg-gray-800 rounded-lg border border-gray-700">
          <div className="flex justify-between items-center p-4 bg-gray-800/50">
            <h2 className="font-bold text-2xl text-white">📚 Historical Explanations</h2>
            <button onClick={handleFetchExplanations} disabled={areExplanationsLoading}
              className="bg-gray-600 text-white px-4 py-2 rounded-md font-semibold shadow-md hover:bg-gray-500 transition-colors duration-200 disabled:bg-gray-700 disabled:cursor-not-allowed">
              {areExplanationsLoading ? "Loading..." : "Fetch History"}
            </button>
          </div>
          <div className="p-6">
            {areExplanationsLoading && <p className="text-blue-400">Loading historical explanations...</p>}
            {explanationsError && <p className="text-red-400">Error: {explanationsError}</p>}
            
            {allExplanations.length > 0 ? (
              <div className="space-y-2">
                {allExplanations.map((exp) => (
                  <div key={exp.run_id} className="border border-gray-700 rounded-md overflow-hidden">
                    <button onClick={() => toggleAccordion(exp.run_id)} className="w-full flex justify-between items-center p-3 bg-gray-900/50 hover:bg-gray-900/80 transition-colors">
                      <div className="flex items-center gap-4">
                        <span className="font-mono text-xs text-gray-400">Run ID: {exp.run_id}</span>
                        <span className="text-xs text-gray-500">{new Date(exp.created_at).toLocaleString()}</span>
                      </div>
                      <ChevronDown className={`transform transition-transform duration-300 ${openAccordion === exp.run_id ? 'rotate-180' : ''}`} size={20} />
                    </button>
                    {openAccordion === exp.run_id && (
                      <div className="p-4 bg-gray-900/30">
                        <p className="text-gray-300 whitespace-pre-wrap text-sm">{exp.explanation}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
                !areExplanationsLoading && !explanationsError && <p className="text-gray-500 text-center py-8">No historical data found. Click "Fetch History" to load.</p>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}

export default Dashboard;



// import React, { useState, useEffect } from "react";
// import StockChart from "./StockChart";

// function Dashboard({ portfolio, setPortfolio, balance, setBalance }) {
//   // --- STATE MANAGEMENT ---
//   const [ticker, setTicker] = useState("None");
//   const [jsonData, setJsonData] = useState([]);
//   const [shares, setShares] = useState(0);
//   const [username, setUsername] = useState("");

//   // --- PIPELINE STATE ---
//   const [isLoading, setIsLoading] = useState(false);
//   const [analysisResult, setAnalysisResult] = useState(null);
//   const [error, setError] = useState("");

//   // --- DETAILED ANALYSIS AGENT ---
//   const [isAnalysisLoading, setIsAnalysisLoading] = useState(false);
//   const [analysisAgentResponse, setAnalysisAgentResponse] = useState(null);
//   const [analysisAgentError, setAnalysisAgentError] = useState("");

//   // --- EXPLAINER AGENT ---
//   const [areExplanationsLoading, setAreExplanationsLoading] = useState(false);
//   const [allExplanations, setAllExplanations] = useState([]);
//   const [explanationsError, setExplanationsError] = useState("");

//   // --- DATA FETCHING WITH AUTO-REFRESH ---
//   useEffect(() => {
//     let interval;

//     if (ticker !== "None") {
//       const fetchData = () => {
//         fetch("/assets/Tata_motors_1_day_data.json")
//           .then((res) => res.json())
//           .then((data) => {
//             if (data.length === 0) return;

//             // ✅ Take day from JSON
//             const firstRowDate = new Date(data[0].date);
//             const jsonDay = firstRowDate.toISOString().split("T")[0];

//             // ✅ Current system time
//             const now = new Date();
//             const hours = now.getHours();
//             const minutes = now.getMinutes();

//             // ✅ Cutoff = JSON’s day + system time
//             const cutoff = new Date(`${jsonDay} ${hours}:${minutes}:00`);

//             // ✅ Only keep rows up to system time
//             const filteredData = data.filter(
//               (row) => new Date(row.date) <= cutoff
//             );

//             setJsonData(filteredData);
//           })
//           .catch((err) => console.error("Error loading JSON:", err));
//       };

//       fetchData(); // run once immediately
//       interval = setInterval(fetchData, 60 * 1000); // refresh every minute
//     } else {
//       setJsonData([]);
//     }

//     return () => clearInterval(interval);
//   }, [ticker]);

//   // ✅ Always use latest CLOSE price
//   const lastPrice =
//     jsonData.length > 0 ? jsonData[jsonData.length - 1].close : 0;

//   // --- HANDLER FUNCTIONS ---
//   const handleSharesChange = (e) => {
//     const value = parseInt(e.target.value);
//     setShares(isNaN(value) || value < 0 ? 0 : value);
//   };

//   const handleBuy = () => {
//     if (ticker === "None") return alert("Select a ticker first!");
//     if (shares <= 0) return alert("Number of shares must be greater than 0");
//     const cost = lastPrice * shares;
//     if (cost > balance) return alert("Not enough balance!");

//     setBalance((prev) => prev - cost);

//     setPortfolio((prev) => {
//       const existing = prev.find((p) => p.ticker === ticker);
//       if (existing) {
//         existing.shares += shares;
//         existing.buyPrice = lastPrice;
//         return [...prev];
//       }
//       return [...prev, { ticker, shares, buyPrice: lastPrice }];
//     });

//     alert(`Bought ${shares} shares at ₹${lastPrice} each for ₹${cost}`);
//     setShares(0);
//   };

//   const handleSell = () => {
//     if (ticker === "None") return alert("Select a ticker first!");
//     if (shares <= 0) return alert("Number of shares must be greater than 0");

//     const existing = portfolio.find((p) => p.ticker === ticker);
//     if (!existing || existing.shares < shares)
//       return alert("Not enough shares to sell!");

//     const revenue = lastPrice * shares;

//     setBalance((prev) => prev + revenue);

//     setPortfolio((prev) =>
//       prev
//         .map((p) =>
//           p.ticker === ticker ? { ...p, shares: p.shares - shares } : p
//         )
//         .filter((p) => p.shares > 0)
//     );

//     alert(`Sold ${shares} shares at ₹${lastPrice} each for ₹${revenue}`);
//     setShares(0);
//   };

//   // --- UI HELPERS ---
//     const getVerdictStyle = (verdict) => {
//     switch (verdict?.toUpperCase()) {
//       case 'PROCEED':
//         return 'text-green-700 bg-green-100';
//       case 'PROCEED WITH CAUTION':
//         return 'text-yellow-700 bg-yellow-100';
//       case 'REJECT':
//         return 'text-red-700 bg-red-100';
//       default:
//         return 'text-gray-700 bg-gray-100';
//     }
//   };

//   // --- PIPELINE START ---
//   const handleStart = async () => {
//     if (ticker === "None" || !username) {
//       alert("Please select a ticker and enter a username.");
//       return;
//     }

//     setIsLoading(true);
//     setError("");
//     setAnalysisResult(null);
//     setAnalysisAgentResponse(null);
//     setAnalysisAgentError("");

//     try {
//       const stockTicker = "TATAMOTORS";
//       const url = `http://localhost:8000/run-pipeline?ticker=${stockTicker}&username=${username}`;

//       const response = await fetch(url, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//       });

//       if (!response.ok) throw new Error(`Error:  ${response.status} ${response.statusText}`);

//       const data = await response.json();
//       setAnalysisResult(data);
//       console.log("Pipeline Response:", data);
//     } catch (err) {
//       setError(err.message);
//       console.error("Failed to run pipeline:", err);
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   // --- FETCH EXPLANATIONS ---
//   const handleFetchExplanations = async () => {
//     setAreExplanationsLoading(true);
//     setExplanationsError("");
//     setAllExplanations([]);

//     try {
//       const response = await fetch("http://localhost:8000/explainer/results");
//       if (!response.ok) throw new Error(`HTTP Error: ${response.statusText}`);
//       const data = await response.json();
//       setAllExplanations(data.explanations.explanations || []);
//     } catch (err) {
//       setExplanationsError(err.message);
//     } finally {
//       setAreExplanationsLoading(false);
//     }
//   };

//   // Dummy signals
//   const signals = [
//     { type: "buy", price: lastPrice - 5 },
//     { type: "sell", price: lastPrice + 5 },
//   ];

//   // --- RENDER ---
//   return (
//     <div className="p-6 bg-gradient-to-br from-gray-50 to-gray-100 min-h-screen">
//       {/* Balance Section */}
//       <div className="mb-6 p-6 bg-white rounded-2xl shadow-md flex justify-between items-center">
//         <span className="font-semibold text-xl text-gray-700">💰 Current Balance</span>
//         <span className="text-green-600 font-bold text-2xl">
//           ₹{balance.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
//         </span>
//       </div>

//       {/* Main Grid */}
//       <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
//         {/* Left Panel */}
//         <div className="col-span-1 space-y-6">
//           <div className="p-6 bg-white rounded-2xl shadow-md">
//             <label className="font-semibold text-gray-700 block mb-2">
//               Select Ticker:
//             </label>
//             <select
//               value={ticker}
//               onChange={(e) => setTicker(e.target.value)}
//               className="w-full border px-3 py-2 rounded-lg focus:ring-2 focus:ring-blue-400"
//             >
//               <option value="None">None</option>
//               <option value="Tata Motors">Tata Motors</option>
//             </select>
//           </div>

//           {/* Risk Filter Analysis */}
//           {/* <div className="p-6 bg-white rounded-2xl shadow-md">
//             <h2 className="font-bold text-lg mb-3 text-gray-700">🛡️ Risk Filter Analysis</h2>
//             {analysisResult && analysisResult.risk_decision ? (
//               <div className="space-y-3">
//                 <p>
//                   <strong>Action:</strong>
//                   <span
//                     className={`ml-2 px-3 py-1 text-sm rounded-full font-semibold ${getDecisionStyle(
//                       analysisResult.risk_decision.decision
//                     )}`}
//                   >
//                     {analysisResult.risk_decision.decision}
//                   </span>
//                 </p>
//                 <p>
//                   <strong>Decision:</strong>
//                   <span
//                     className={`ml-2 px-3 py-1 text-sm rounded-full font-semibold ${getActionStyle(
//                       analysisResult.risk_decision.action
//                     )}`}
//                   >
//                     {analysisResult.risk_decision.action}
//                   </span>
//                 </p>
//                 <strong>Reasons:</strong>
//                 <ul className="list-disc list-inside text-gray-600 mt-1 space-y-1">
//                   {analysisResult.risk_decision.reasons.map((reason, index) => (
//                     <li key={index}>{reason}</li>
//                   ))}
//                 </ul>
//               </div>
//             ) : (
//               <p className="text-gray-500 italic">
//                 You will see the risk analysis results here after running the pipeline.
//               </p>
//             )}
//           </div> */}

//           {/* Buy/Sell Form */}
//           <div className="p-6 bg-white rounded-2xl shadow-md space-y-4">
//             <p className="font-semibold text-gray-700">📊 Last Price: ₹{lastPrice}</p>
//             <input
//               type="number"
//               placeholder="Number of shares"
//               value={shares}
//               onChange={handleSharesChange}
//               className="w-full border px-3 py-2 rounded-lg focus:ring-2 focus:ring-blue-400"
//             />
//             <div className="flex gap-4">
//               <button
//                 onClick={handleBuy}
//                 className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold shadow hover:bg-blue-700 transition"
//               >
//                 Buy
//               </button>
//               <button
//                 onClick={handleSell}
//                 className="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg font-semibold shadow hover:bg-red-700 transition"
//               >
//                 Sell
//               </button>
//             </div>
//           </div>

//           {/* Username Input */}
//           <div className="p-6 bg-white rounded-2xl shadow-md space-y-3">
//             <label className="font-semibold text-gray-700 block">Enter Username:</label>
//             <input
//               type="text"
//               placeholder="Username"
//               value={username}
//               onChange={(e) => setUsername(e.target.value)}
//               className="w-full border px-3 py-2 rounded-lg focus:ring-2 focus:ring-blue-400"
//               disabled={isLoading}
//             />
//             <button
//               onClick={handleStart}
//               className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold shadow hover:bg-blue-700 transition disabled:bg-gray-400"
//               disabled={isLoading}
//             >
//               {isLoading ? "Analyzing..." : "Start Analysis"}
//             </button>
//           </div>
//         </div>

//         {/* Right Panel: Stock Chart */}
//         <div className="col-span-2 p-6 bg-white rounded-2xl shadow-md">
//           <h2 className="font-bold text-lg mb-4 text-gray-700">📉 Stock Chart</h2>
//           <StockChart jsonData={jsonData} />
//         </div>
//       </div>

//       {/* Execution Analysis */}
//       {/* <div className="mt-6 p-6 bg-white rounded-2xl shadow-md">
//         <h2 className="font-bold text-xl mb-4 text-gray-700">📝 Execution Analysis</h2>
//         {isLoading && (
//           <p className="text-blue-600">Loading analysis from the agentic pipeline...</p>
//         )}
//         {error && <p className="text-red-600">Error: {error}</p>}
//         {analysisResult && (
//           <div className="text-gray-700 space-y-2">
//             <p>
//               <strong>Status:</strong>{" "}
//               <span className="font-mono text-green-600">{analysisResult.status}</span>
//             </p>
//             <p>
//               <strong>Trade ID:</strong>{" "}
//               <span className="font-mono">{analysisResult.trade_id}</span>
//             </p>
//             <p>
//               <strong>Allocation Decision:</strong>
//             </p>
//             <pre className="bg-gray-100 p-3 rounded-lg text-sm">
//               {JSON.stringify(analysisResult.allocation, null, 2)}
//             </pre>
//           </div>
//         )}
//       </div> */}
//       {/* MODIFICATION: Completely redesigned Execution Analysis Section */}
//       <div className="mt-6 p-6 bg-white rounded-2xl shadow-md">
//         <h2 className="font-bold text-xl mb-4 text-gray-700">📝 Execution Analysis</h2>
//         {isLoading && <p className="text-blue-600">Loading analysis from the agentic pipeline...</p>}
//         {error && <p className="text-red-600">Error: {error}</p>}
        
//         {analysisResult && (
//           <div className="space-y-6">
//             {/* 1. Final Verdict and Summary */}
//             <div className={`p-4 rounded-lg ${getVerdictStyle(analysisResult.risk_decision.final_verdict)}`}>
//               <h3 className="font-bold text-lg">
//                 Final Verdict: {analysisResult.risk_decision.final_verdict}
//               </h3>
//               <p className="italic mt-1">{analysisResult.risk_decision.summary_rationale}</p>
//             </div>
            
//             {/* 2. Pros and Cons */}
//             <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
//               {/* Positive Factors */}
//               <div>
//                 <h4 className="font-semibold text-gray-800 mb-2">Key Positive Factors</h4>
//                 <ul className="space-y-2">
//                   {analysisResult.risk_decision.key_positive_factors.length > 0 ? (
//                     analysisResult.risk_decision.key_positive_factors.map((factor, i) => (
//                       <li key={i} className="flex items-start">
//                         <span className="text-green-500 mr-2">✔</span>
//                         <span>{factor}</span>
//                       </li>
//                     ))
//                   ) : (<li className="text-gray-500">None identified.</li>)}
//                 </ul>
//               </div>
//               {/* Risks and Concerns */}
//               <div>
//                 <h4 className="font-semibold text-gray-800 mb-2">Key Risks & Concerns</h4>
//                 <ul className="space-y-2">
//                    {analysisResult.risk_decision.key_risks_and_concerns.length > 0 ? (
//                     analysisResult.risk_decision.key_risks_and_concerns.map((risk, i) => (
//                       <li key={i} className="flex items-start">
//                         <span className="text-red-500 mr-2">✖</span>
//                         <span>{risk}</span>
//                       </li>
//                     ))
//                   ) : (<li className="text-gray-500">None identified.</li>)}
//                 </ul>
//               </div>
//             </div>

//             {/* 3. Allocation Details */}
//             <div className="pt-4 border-t">
//               <h4 className="font-semibold text-gray-800 mb-2">Capital Allocator's Proposal</h4>
//               <div className="text-sm p-4 bg-gray-50 rounded-md">
//                 <p><strong>Intent:</strong> {analysisResult.allocation.intent} ({analysisResult.allocation.side})</p>
//                 <p><strong>Proposed Allocation:</strong> ₹{analysisResult.allocation.allocation_cash.toFixed(2)}</p>
//                 <p><strong>Stop-Loss:</strong> {analysisResult.allocation.suggested_stop_loss || 'N/A'}</p>
//                 <p><strong>Rationale:</strong> {analysisResult.allocation.rationale}</p>
//               </div>
//             </div>
//           </div>
//         )}
        
//         {!isLoading && !analysisResult && !error && (
//           <p className="text-gray-500">Click "Start Analysis" to get the latest trading signal and execution plan.</p>
//         )}
//       </div>


//       {/* Historical Explanations */}
//       <div className="mt-6 p-6 bg-white rounded-2xl shadow-md">
//         <div className="flex justify-between items-center mb-4">
//           <h2 className="font-bold text-xl text-gray-700">📚 Historical Explanations</h2>
//           <button
//             onClick={handleFetchExplanations}
//             disabled={areExplanationsLoading}
//             className="bg-gray-700 text-white px-4 py-2 rounded-lg font-semibold shadow hover:bg-gray-800 transition disabled:bg-gray-400"
//           >
//             {areExplanationsLoading ? "Loading..." : "Fetch All"}
//           </button>
//         </div>
//         {areExplanationsLoading && (
//           <p className="text-blue-600">Loading historical explanations...</p>
//         )}
//         {explanationsError && <p className="text-red-600">Error: {explanationsError}</p>}
//         {allExplanations.length > 0 && (
//           <div className="space-y-4 mt-4">
//             {allExplanations.map((exp) => (
//               <div
//                 key={exp.run_id}
//                 className="p-4 bg-gray-50 rounded-lg border border-gray-200"
//               >
//                 <div className="flex justify-between items-center text-sm text-gray-500 mb-2">
//                   <span>Run ID: {exp.run_id}</span>
//                   <span>{new Date(exp.created_at).toLocaleString()}</span>
//                 </div>
//                 <p className="text-gray-800 whitespace-pre-wrap">{exp.explanation}</p>
//               </div>
//             ))}
//           </div>
//         )}
//       </div>
//     </div>
//   );
// }

// export default Dashboard;
