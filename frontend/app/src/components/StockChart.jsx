import React, { useState, useEffect } from "react";
import Chart from "react-apexcharts";

function StockChart() {
  const [chartType, setChartType] = useState("candlestick");
  const [jsonData, setJsonData] = useState([]);

  // ✅ Function to fetch & filter JSON till current time
  const loadData = () => {
    fetch("/assets/Tata_motors_1_day_data.json")
      .then((res) => res.json())
      .then((data) => {
        if (data.length === 0) return;

        // Get the "date part" from the first row of JSON
        const firstRowDate = new Date(data[0].date);
        const jsonDay = firstRowDate.toISOString().split("T")[0]; // e.g. "2025-07-21"

        // Get current system time (hours + minutes)
        const now = new Date();
        const hours = now.getHours();
        const minutes = now.getMinutes();

        // Build cutoff = same JSON day but current system time
        const cutoff = new Date(`${jsonDay} ${hours}:${minutes}:00`);

        // Keep only rows up to cutoff
        const filteredData = data.filter((row) => {
          const rowTime = new Date(row.date);
          return rowTime <= cutoff;
        });

        setJsonData(filteredData);
      })
      .catch((err) => console.error("Error loading JSON:", err));
  };

  // ✅ Initial load + refresh every 60s
  useEffect(() => {
    loadData(); // first run
    const interval = setInterval(loadData, 60 * 1000); // refresh every 1 min
    return () => clearInterval(interval); // cleanup
  }, []);

  if (jsonData.length === 0) return <p>Loading...</p>;

  // ✅ Prepare OHLC data for candlestick
  const ohlc = jsonData.map((row) => ({
    x: new Date(row.date).getTime(),
    y: [+row.open, +row.high, +row.low, +row.close],
  }));

  // ✅ Prepare line chart data (closing prices)
  const lineData = jsonData.map((row) => ({
    x: new Date(row.date).getTime(),
    y: +row.close,
  }));

  // ✅ Example buy/sell signals
  const signals = [
    { type: "buy", time: "7/21/2025 10:16", price: 675.8 },
    { type: "sell", time: "7/21/2025 14:19", price: 677 },
  ];

  // ✅ Add annotations for buy/sell
  const annotations = {
    points: signals.map((s) => ({
      x: new Date(s.time).getTime(),
      y: s.price,
      marker: {
        size: 8,
        shape: "circle",
        fillColor: s.type === "buy" ? "#00e676" : "#ff1744",
        strokeColor: "#000",
        strokeWidth: 1,
      },
      label: {
        text: s.type.toUpperCase(),
        borderColor: s.type === "buy" ? "#00e676" : "#ff1744",
        offsetY: -10,
        style: {
          background: s.type === "buy" ? "#00e676" : "#ff1744",
          color: "#fff",
          fontWeight: 600,
        },
      },
    })),
  };

  // ✅ Common options for both chart types
  const commonOptions = {
    chart: {
      type: chartType,
      height: "100%",
      width: "100%",
      animations: { enabled: false },
      toolbar: { show: false },
    },
    xaxis: {
      type: "datetime",
      labels: { datetimeUTC: false, datetimeFormatter: { hour: "hh:mm TT" } },
    },
    tooltip: { enabled: true, x: { format: "dd MMM yyyy hh:mm TT" } },
    annotations,
  };

  // ✅ Candlestick options
  const candleOptions = {
    ...commonOptions,
    title: {
      text: "📊 Tata Motors Candlestick with Buy/Sell Signals",
      align: "left",
    },
  };

  // ✅ Line chart options
  const lineOptions = {
    ...commonOptions,
    title: {
      text: "📈 Tata Motors Line Chart with Buy/Sell Signals",
      align: "left",
    },
    stroke: { curve: "smooth", width: 2 },
    markers: { size: 0 },
  };

  return (
    <div className="w-full p-4 bg-white rounded shadow">
      {/* Chart */}
      <div className="w-full h-[500px]">
        <Chart
          options={chartType === "candlestick" ? candleOptions : lineOptions}
          series={
            chartType === "candlestick"
              ? [{ data: ohlc }]
              : [{ name: "Close Price", data: lineData }]
          }
          type={chartType}
          height="100%"
          width="100%"
        />
      </div>

      {/* Buttons to switch chart type */}
      <div className="mt-4 flex gap-2 justify-center">
        <button
          className={`px-4 py-2 rounded ${
            chartType === "line" ? "bg-blue-600 text-white" : "bg-gray-200"
          }`}
          onClick={() => setChartType("line")}
        >
          Line Chart
        </button>
        <button
          className={`px-4 py-2 rounded ${
            chartType === "candlestick" ? "bg-blue-600 text-white" : "bg-gray-200"
          }`}
          onClick={() => setChartType("candlestick")}
        >
          Candlestick Chart
        </button>
      </div>
    </div>
  );
}

export default StockChart;
