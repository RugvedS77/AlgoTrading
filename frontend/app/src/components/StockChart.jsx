import React, { useState } from "react";
import Chart from "react-apexcharts";
import jsonData from "../assets/Tata_motors_1_day_data.json";

function StockChart() {
  const [chartType, setChartType] = useState("candlestick");

  // ✅ Candlestick data
  const ohlc = jsonData.map((row) => ({
    x: new Date(row.date).getTime(),
    y: [+row.open, +row.high, +row.low, +row.close],
  }));

  // ✅ Line chart data
  const lineData = jsonData.map((row) => ({
    x: new Date(row.date).getTime(),
    y: +row.close,
  }));

  // ✅ Example Buy/Sell points
  const signals = [
    { type: "buy", time: "7/21/2025 10:16", price: 675.8 },
    { type: "sell", time: "7/21/2025 14:19", price: 677 },
  ];

  // ✅ Map them into ApexCharts annotation objects
  const annotations = {
    points: signals.map((s) => ({
      x: new Date(s.time).getTime(),
      y: s.price,
      marker: {
        size: 8,
        shape: "circle",
        fillColor: s.type === "buy" ? "#00e676" : "#ff1744", // green = buy, red = sell
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
      height: 500,
      animations: { enabled: false },
      toolbar: { show: false }, // ✅ Hide zoom/pan/reset toolbar
    },
    xaxis: {
      type: "datetime",
      labels: {
        datetimeUTC: false,
        datetimeFormatter: {
          hour: "hh:mm TT", // ✅ 12-hour format with AM/PM
        },
      },
    },
    tooltip: {
      enabled: true,
      x: {
        format: "dd MMM yyyy hh:mm TT", // ✅ Tooltip also in 12-hour format
      },
    },
    annotations, // ✅ add buy/sell markers
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

  const candleSeries = [{ data: ohlc }];
  const lineSeries = [{ name: "Close Price", data: lineData }];

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">📊 Tata Motors Stock Chart</h2>
      <div className="flex gap-2 mb-6">
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

      {chartType === "candlestick" ? (
        <Chart
          options={candleOptions}
          series={candleSeries}
          type="candlestick"
          height={500}
        />
      ) : (
        <Chart
          options={lineOptions}
          series={lineSeries}
          type="line"
          height={500}
        />
      )}
    </div>
  );
}

export default StockChart;
