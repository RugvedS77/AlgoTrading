import React, { useState, useEffect } from "react";
import Chart from "react-apexcharts";

function StockChart() {
  const [chartType, setChartType] = useState("candlestick");
  const [jsonData, setJsonData] = useState([]);

  useEffect(() => {
    fetch("/assets/Tata_motors_1_day_data.json")
      .then((res) => res.json())
      .then((data) => setJsonData(data))
      .catch((err) => console.error("Error loading JSON:", err));
  }, []);

  if (jsonData.length === 0) return <p>Loading...</p>;

  const ohlc = jsonData.map((row) => ({
    x: new Date(row.date).getTime(),
    y: [+row.open, +row.high, +row.low, +row.close],
  }));

  const lineData = jsonData.map((row) => ({
    x: new Date(row.date).getTime(),
    y: +row.close,
  }));

  const signals = [
    { type: "buy", time: "7/21/2025 10:16", price: 675.8 },
    { type: "sell", time: "7/21/2025 14:19", price: 677 },
  ];

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

  const candleOptions = {
    ...commonOptions,
    title: { text: "📊 Tata Motors Candlestick with Buy/Sell Signals", align: "left" },
  };

  const lineOptions = {
    ...commonOptions,
    title: { text: "📈 Tata Motors Line Chart with Buy/Sell Signals", align: "left" },
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

      {/* Chart Type Buttons below */}
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
