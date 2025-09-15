import React, { useState, useEffect } from "react";
import StockChart from "./StockChart";

function Dashboard({ portfolio, setPortfolio, balance, setBalance }) {
  // --- STATE MANAGEMENT ---
  // Core UI State
  const [ticker, setTicker] = useState("None");
  const [jsonData, setJsonData] = useState([]);
  const [shares, setShares] = useState(0);
  const [username, setUsername] = useState("");

  // State for the Main Pipeline (/run-pipeline)
  const [isLoading, setIsLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState("");

  // State for the Detailed Analysis Agent (/detailed-analysis)
  const [isAnalysisLoading, setIsAnalysisLoading] = useState(false);
  const [analysisAgentResponse, setAnalysisAgentResponse] = useState(null);
  const [analysisAgentError, setAnalysisAgentError] = useState("");

  // State for the Explainer Agent (/explainer/results)
  const [areExplanationsLoading, setAreExplanationsLoading] = useState(false);
  const [allExplanations, setAllExplanations] = useState([]);
  const [explanationsError, setExplanationsError] = useState("");

  // --- DATA FETCHING ---
  // Effect to load static chart data when ticker changes
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

  // --- HANDLER FUNCTIONS ---
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
  // Helper function for styling the risk decision
  const getDecisionStyle = (decision) => {
    switch (decision?.toUpperCase()) {
      case 'PROCEED':
        return 'text-green-600 bg-green-100';
      case 'REJECTED':
      case 'SKIPPED':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };
  const getActionStyle = (action) => {
    switch (action?.toUpperCase()) {
      case 'SELL':
        return 'text-green-600 bg-green-100';
      case 'BUY':
      case 'HOLD':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };
  // MODIFICATION: Update handleStart to call the backend API
  const handleStart = async () => {
    // Basic validation
    if (ticker === "None" || !username) {
      alert("Please select a ticker and enter a username.");
      return;
    }
    
    // Reset previous results and set loading state
    setIsLoading(true);
    setError("");
    setAnalysisResult(null);
        // MODIFICATION: Reset the analysis agent's state on a new run
    setAnalysisAgentResponse(null);
    setAnalysisAgentError("");

    try {
      // Construct the URL with query parameters
      // NOTE: The ticker name might need to be adjusted to match your backend (e.g., "TATAMOTORS")
      const stockTicker = "TATAMOTORS"; // Map "Tata Motors" to the backend-expected ticker
      const url = `http://localhost:8000/run-pipeline?ticker=${stockTicker}&username=${username}`;

      const response = await fetch(url, {
        method: "POST", // Use POST as defined in the backend router
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        // Handle HTTP errors like 404 or 500
        throw new Error(`Error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      setAnalysisResult(data); // Store the successful response
      console.log("Pipeline Response:", data);

    } catch (err) {
      // Handle fetch errors (e.g., network issues)
      setError(err.message);
      console.error("Failed to run pipeline:", err);
    } finally {
      // Reset loading state regardless of success or failure
      setIsLoading(false);
    }
  };

  // MODIFICATION: Correctly access the nested array
  const handleFetchExplanations = async () => {
    setAreExplanationsLoading(true);
    setExplanationsError('');
    setAllExplanations([]);

    try {
      const response = await fetch('http://localhost:8000/explainer/results');
      if (!response.ok) {
        throw new Error(`HTTP Error: ${response.statusText}`);
      }
      const data = await response.json();
      console.log('Data received from /explainer/results:', data);

      // FIX: Access the deeply nested array at data.explanations.explanations
      setAllExplanations(data.explanations.explanations || []);

    } catch (err) {
      setExplanationsError(err.message);
    } finally {
      setAreExplanationsLoading(false);
    }
  };

  const signals = [
    { type: "buy", price: lastPrice - 5 },
    { type: "sell", price: lastPrice + 5 },
  ];

  // --- RENDER ---
  return (
    <div className="p-6 bg-gradient-to-br from-gray-50 to-gray-100 min-h-screen">
      {/* Balance Section */}
      <div className="mb-6 p-6 bg-white rounded-2xl shadow-md flex justify-between items-center">
        <span className="font-semibold text-xl text-gray-700">💰 Current Balance</span>
        <span className="text-green-600 font-bold text-2xl">
          ₹{balance.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
        </span>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Panel: Controls */}
        <div className="col-span-1 space-y-6">
            <div className="p-6 bg-white rounded-2xl shadow-md">
                <label className="font-semibold text-gray-700 block mb-2">Select Ticker:</label>
                <select value={ticker} onChange={(e) => setTicker(e.target.value)} className="w-full border px-3 py-2 rounded-lg focus:ring-2 focus:ring-blue-400">
                    <option value="None">None</option>
                    <option value="Tata Motors">Tata Motors</option>
                </select>
            </div>
              {/* MODIFICATION: New Dynamic Risk Analysis Card */}
          <div className="p-6 bg-white rounded-2xl shadow-md">
            <h2 className="font-bold text-lg mb-3 text-gray-700">🛡️ Risk Filter Analysis</h2>
            
            {/* Show analysis result if available */}
            {analysisResult && analysisResult.risk_decision ? (
              <div className="space-y-3">
                <p>
                  <strong>Action:</strong>
                  <span className={`ml-2 px-3 py-1 text-sm rounded-full font-semibold ${getDecisionStyle(analysisResult.risk_decision.decision)}`}>
                    {analysisResult.risk_decision.decision}
                  </span>
                </p>
                <div>
                {/* <div className="space-y-3"> */}
                <p>
                  <strong>Decision:</strong>
                  <span className={`ml-2 px-3 py-1 text-sm rounded-full font-semibold ${getActionStyle(analysisResult.risk_decision.action)}`}>
                    {analysisResult.risk_decision.action}
                  </span>
                </p>
                {/* <div> */}
                  <strong>Reasons:</strong>
                  <ul className="list-disc list-inside text-gray-600 mt-1 space-y-1">
                    {analysisResult.risk_decision.reasons.map((reason, index) => (
                      <li key={index}>{reason}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              // Show placeholder if no result yet
              <p className="text-gray-500 italic">
                You will see the risk analysis results here after running the pipeline.
              </p>
            )}
          </div>
            <div className="p-6 bg-white rounded-2xl shadow-md space-y-4">
                <p className="font-semibold text-gray-700">📊 Last Price: ₹{lastPrice}</p>
                <input type="number" placeholder="Number of shares" value={shares} onChange={handleSharesChange} className="w-full border px-3 py-2 rounded-lg focus:ring-2 focus:ring-blue-400" />
                <div className="flex gap-4">
                    <button onClick={handleBuy} className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold shadow hover:bg-blue-700 transition">Buy</button>
                    <button onClick={handleSell} className="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg font-semibold shadow hover:bg-red-700 transition">Sell</button>
                </div>
            </div>
            <div className="p-6 bg-white rounded-2xl shadow-md space-y-3">
                <label className="font-semibold text-gray-700 block">Enter Username:</label>
                <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} className="w-full border px-3 py-2 rounded-lg focus:ring-2 focus:ring-blue-400" disabled={isLoading} />
                <button onClick={handleStart} className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold shadow hover:bg-blue-700 transition disabled:bg-gray-400" disabled={isLoading}>
                    {isLoading ? "Analyzing..." : "Start Analysis"}
                </button>
            </div>
        </div>

        {/* Right Panel: Stock Chart */}
        <div className="col-span-2 p-6 bg-white rounded-2xl shadow-md">
          <h2 className="font-bold text-lg mb-4 text-gray-700">📉 Stock Chart</h2>
          <StockChart />
        </div>
      </div>

      {/* Execution Analysis Section */}
      <div className="mt-6 p-6 bg-white rounded-2xl shadow-md">
        <h2 className="font-bold text-xl mb-4 text-gray-700">📝 Execution Analysis</h2>
        {isLoading && <p className="text-blue-600">Loading analysis from the agentic pipeline...</p>}
        {error && <p className="text-red-600">Error: {error}</p>}
        {analysisResult && (
          <div className="text-gray-700 space-y-2">
            <p><strong>Status:</strong> <span className="font-mono text-green-600">{analysisResult.status}</span></p>
            <p><strong>Trade ID:</strong> <span className="font-mono">{analysisResult.trade_id}</span></p>
            <p><strong>Allocation Decision:</strong></p>
            <pre className="bg-gray-100 p-3 rounded-lg text-sm">{JSON.stringify(analysisResult.allocation, null, 2)}</pre>
          </div>
        )}
      </div>

      {/* Historical Explanations Section */}
      <div className="mt-6 p-6 bg-white rounded-2xl shadow-md">
        <div className="flex justify-between items-center mb-4">
          <h2 className="font-bold text-xl text-gray-700">📚 Historical Explanations</h2>
          <button onClick={handleFetchExplanations} disabled={areExplanationsLoading} className="bg-gray-700 text-white px-4 py-2 rounded-lg font-semibold shadow hover:bg-gray-800 transition disabled:bg-gray-400">
            {areExplanationsLoading ? "Loading..." : "Fetch All"}
          </button>
        </div>
        {areExplanationsLoading && <p className="text-blue-600">Loading historical explanations...</p>}
        {explanationsError && <p className="text-red-600">Error: {explanationsError}</p>}
        
        {/* MODIFICATION: Corrected rendering logic */}
        {allExplanations.length > 0 && (
          <div className="space-y-4 mt-4">
            {allExplanations.map((exp) => (
              <div key={exp.run_id} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex justify-between items-center text-sm text-gray-500 mb-2">
                  <span>Run ID: {exp.run_id}</span>
                  <span>{new Date(exp.created_at).toLocaleString()}</span>
                </div>
                {/* We render the specific 'explanation' string, not the whole 'exp' object */}
                <p className="text-gray-800 whitespace-pre-wrap">{exp.explanation}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;