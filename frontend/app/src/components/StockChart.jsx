// import React, { useState, useEffect } from "react";
// import Chart from "react-apexcharts";

// function StockChart() {
//   const [chartType, setChartType] = useState("candlestick");
//   const [jsonData, setJsonData] = useState([]);

//   // ✅ Function to fetch & filter JSON till current time
//   const loadData = () => {
//     fetch("/assets/Tata_motors_1_day_data.json")
//       .then((res) => res.json())
//       .then((data) => {
//         if (data.length === 0) return;

//         // Get the "date part" from the first row of JSON
//         const firstRowDate = new Date(data[0].date);
//         const jsonDay = firstRowDate.toISOString().split("T")[0]; // e.g. "2025-07-21"

//         // Get current system time (hours + minutes)
//         const now = new Date();
//         const hours = now.getHours();
//         const minutes = now.getMinutes();

//         // Build cutoff = same JSON day but current system time
//         const cutoff = new Date(`${jsonDay} ${hours}:${minutes}:00`);

//         // Keep only rows up to cutoff
//         const filteredData = data.filter((row) => {
//           const rowTime = new Date(row.date);
//           return rowTime <= cutoff;
//         });

//         setJsonData(filteredData);
//       })
//       .catch((err) => console.error("Error loading JSON:", err));
//   };

//   // ✅ Initial load + refresh every 60s
//   useEffect(() => {
//     loadData(); // first run
//     const interval = setInterval(loadData, 60 * 1000); // refresh every 1 min
//     return () => clearInterval(interval); // cleanup
//   }, []);

//   if (jsonData.length === 0) return <p>Loading...</p>;

//   // ✅ Prepare OHLC data for candlestick
//   const ohlc = jsonData.map((row) => ({
//     x: new Date(row.date).getTime(),
//     y: [+row.open, +row.high, +row.low, +row.close],
//   }));

//   // ✅ Prepare line chart data (closing prices)
//   const lineData = jsonData.map((row) => ({
//     x: new Date(row.date).getTime(),
//     y: +row.close,
//   }));

//   // ✅ Example buy/sell signals
//   const signals = [
//     { type: "buy", time: "7/21/2025 10:16", price: 675.8 },
//     { type: "sell", time: "7/21/2025 14:19", price: 677 },
//   ];

//   // ✅ Add annotations for buy/sell
//   const annotations = {
//     points: signals.map((s) => ({
//       x: new Date(s.time).getTime(),
//       y: s.price,
//       marker: {
//         size: 8,
//         shape: "circle",
//         fillColor: s.type === "buy" ? "#00e676" : "#ff1744",
//         strokeColor: "#000",
//         strokeWidth: 1,
//       },
//       label: {
//         text: s.type.toUpperCase(),
//         borderColor: s.type === "buy" ? "#00e676" : "#ff1744",
//         offsetY: -10,
//         style: {
//           background: s.type === "buy" ? "#00e676" : "#ff1744",
//           color: "#fff",
//           fontWeight: 600,
//         },
//       },
//     })),
//   };

//   // ✅ Common options for both chart types
//   const commonOptions = {
//     chart: {
//       type: chartType,
//       height: "100%",
//       width: "100%",
//       animations: { enabled: false },
//       toolbar: { show: false },
//     },
//     xaxis: {
//       type: "datetime",
//       labels: { datetimeUTC: false, datetimeFormatter: { hour: "hh:mm TT" } },
//     },
//     tooltip: { enabled: true, x: { format: "dd MMM yyyy hh:mm TT" } },
//     annotations,
//   };

//   // ✅ Candlestick options
//   const candleOptions = {
//     ...commonOptions,
//     title: {
//       text: "📊 Tata Motors Candlestick with Buy/Sell Signals",
//       align: "left",
//     },
//   };

//   // ✅ Line chart options
//   const lineOptions = {
//     ...commonOptions,
//     title: {
//       text: "📈 Tata Motors Line Chart with Buy/Sell Signals",
//       align: "left",
//     },
//     stroke: { curve: "smooth", width: 2 },
//     markers: { size: 0 },
//   };

//   return (
//     <div className="w-full p-4 bg-white rounded shadow">
//       {/* Chart */}
//       <div className="w-full h-[500px]">
//         <Chart
//           options={chartType === "candlestick" ? candleOptions : lineOptions}
//           series={
//             chartType === "candlestick"
//               ? [{ data: ohlc }]
//               : [{ name: "Close Price", data: lineData }]
//           }
//           type={chartType}
//           height="100%"
//           width="100%"
//         />
//       </div>

//       {/* Buttons to switch chart type */}
//       <div className="mt-4 flex gap-2 justify-center">
//         <button
//           className={`px-4 py-2 rounded ${
//             chartType === "line" ? "bg-blue-600 text-white" : "bg-gray-200"
//           }`}
//           onClick={() => setChartType("line")}
//         >
//           Line Chart
//         </button>
//         <button
//           className={`px-4 py-2 rounded ${
//             chartType === "candlestick" ? "bg-blue-600 text-white" : "bg-gray-200"
//           }`}
//           onClick={() => setChartType("candlestick")}
//         >
//           Candlestick Chart
//         </button>
//       </div>
//     </div>
//   );
// }

// export default StockChart;

import React, { useState, useEffect } from "react";
import Chart from "react-apexcharts";
import { CandlestickChart, LineChart, BarChart2 } from 'lucide-react'; // For icons

// A helper component for the toolbar buttons
const ToolbarButton = ({ children, onClick, isActive }) => (
  <button
    onClick={onClick}
    className={`p-2 rounded-md transition-colors duration-200 ${
      isActive ? 'bg-blue-600 text-white' : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
    }`}
  >
    {children}
  </button>
);

function StockChart() {
  const [chartType, setChartType] = useState("candlestick");
  const [jsonData, setJsonData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // ✅ Kept data loading internal as requested
  useEffect(() => {
    const loadData = () => {
      fetch("/assets/Tata_motors_1_day_data.json")
        .then((res) => res.json())
        .then((data) => {
          if (data.length === 0) {
            setJsonData([]);
            return;
          }
          const firstRowDate = new Date(data[0].date);
          const jsonDay = firstRowDate.toISOString().split("T")[0];
          const now = new Date();
          const hours = now.getHours();
          const minutes = now.getMinutes();
          const cutoff = new Date(`${jsonDay} ${hours}:${minutes}:00`);
          const filteredData = data.filter((row) => new Date(row.date) <= cutoff);
          setJsonData(filteredData);
        })
        .catch((err) => {
          console.error("Error loading JSON:", err);
          setJsonData([]);
        })
        .finally(() => setIsLoading(false));
    };

    loadData(); // first run
    const interval = setInterval(loadData, 60 * 1000); // refresh every 1 min
    return () => clearInterval(interval); // cleanup
  }, []);

  if (isLoading) {
    return <div className="h-full flex items-center justify-center text-gray-400">Loading Chart Data...</div>;
  }
  if (jsonData.length === 0) {
    return <div className="h-full flex items-center justify-center text-gray-500">No data available to display.</div>;
  }

  // --- Data Preparation ---
  const ohlc = jsonData.map((row) => ({
    x: new Date(row.date).getTime(),
    y: [+row.open, +row.high, +row.low, +row.close],
  }));

  const lineData = jsonData.map((row) => ({
    x: new Date(row.date).getTime(),
    y: +row.close,
  }));

  const volumeData = jsonData.map((row) => ({
    x: new Date(row.date).getTime(),
    y: +row.volume,
    // Optional: color volume bars based on price change
    fillColor: (+row.close >= +row.open) ? '#00A746' : '#EF4444',
  }));

  // --- Annotations for Signals ---
  const signals = [
    { type: "buy", time: "7/21/2025 10:16", price: 675.8 },
    { type: "sell", time: "7/21/2025 14:19", price: 677 },
  ];

  const annotations = {
    points: signals.map((s) => ({
      x: new Date(s.time).getTime(),
      y: s.price,
      marker: { size: 6, fillColor: s.type === "buy" ? "#00e676" : "#ff1744", strokeColor: "#fff", strokeWidth: 2, shape: 'circle' },
      label: { text: s.type.toUpperCase(), borderColor: 'transparent', offsetY: -15, style: { background: s.type === "buy" ? "#00e676" : "#ff1744", color: "#fff", fontWeight: 600, fontSize: '11px', padding: { left: 5, right: 5, top: 2, bottom: 2 } } },
    })),
  };

  // --- Chart Options ---
  const commonOptions = {
    chart: { id: "stock-chart", animations: { enabled: false }, toolbar: { show: true, tools: { download: true, selection: true, zoom: true, zoomin: true, zoomout: true, pan: true, reset: true }, autoSelected: 'zoom' }, background: 'transparent', },
    xaxis: { type: "datetime", labels: { datetimeUTC: false, style: { colors: '#9CA3AF' } }, axisBorder: { color: '#4B5563' }, axisTicks: { color: '#4B5563' } },
    yaxis: { labels: { formatter: (val) => val.toFixed(2), style: { colors: '#9CA3AF' } }, opposite: true },
    grid: { borderColor: '#374151', strokeDashArray: 3 },
    tooltip: { theme: 'dark', x: { format: "dd MMM yyyy - HH:mm" } },
    annotations,
  };

  const candleOptions = { ...commonOptions, plotOptions: { candlestick: { colors: { upward: '#00A746', downward: '#EF4444' }, wick: { useFillColor: true } } } };
  const lineOptions = { ...commonOptions, stroke: { curve: "smooth", width: 2, colors: ['#3B82F6'] }, fill: { type: 'gradient', gradient: { shade: 'dark', type: "vertical", opacityFrom: 0.7, opacityTo: 0.1 } }, markers: { size: 0 } };
  
  const volumeOptions = {
    chart: {
      id: 'volume-chart',
      height: 160,
      type: 'bar',
      toolbar: { show: false },
      zoom: { enabled: false },
      background: 'transparent',
      // REMOVED: brush and selection properties to remove the bottom navigator
      // brush: {
      //   enabled: true,
      //   target: 'stock-chart'
      // },
      // selection: {
      //   enabled: true,
      //   xaxis: {
      //     min: ohlc.length > 0 ? ohlc[0].x : undefined,
      //     max: ohlc.length > 0 ? ohlc[ohlc.length - 1].x : undefined
      //   },
      //   fill: { color: '#ccc', opacity: 0.4 },
      //   stroke: { color: '#0D47A1' }
      // },
    },
    plotOptions: { bar: { columnWidth: '80%', distributed: true } },
    xaxis: { type: 'datetime', labels: { show: false }, axisTicks: { show: false }, axisBorder: { show: false } },
    yaxis: { labels: { show: false }, axisTicks: { show: false }, axisBorder: { show: false } },
    grid: { show: false },
    tooltip: { enabled: true, theme: 'dark', y: { formatter: (val) => `Vol: ${val.toLocaleString()} `} },
  };

  const chartSeries = chartType === 'candlestick' ? [{ name: 'Price', data: ohlc }] : [{ name: 'Price', data: lineData }];
  const chartOptions = chartType === 'candlestick' ? candleOptions : lineOptions;

  return (
    <div className="w-full h-full flex flex-col p-2">
      {/* Custom Toolbar */}
      <div className="flex items-center gap-4 mb-2">
        <h3 className="text-lg font-bold text-white">Tata Motors</h3>
        <div className="flex gap-1">
          <ToolbarButton onClick={() => setChartType('candlestick')} isActive={chartType === 'candlestick'}><CandlestickChart size={18} /></ToolbarButton>
          <ToolbarButton onClick={() => setChartType('line')} isActive={chartType === 'line'}><LineChart size={18} /></ToolbarButton>
        </div>
      </div>

      {/* Main Chart */}
      <div className="flex-grow">
        <Chart options={chartOptions} series={chartSeries} type={chartType} height="100%" width="100%" />
      </div>
      
      {/* Volume Chart */}
      <div className="w-full">
        <Chart options={volumeOptions} series={[{ name: 'Volume', data: volumeData }]} type="bar" height={160} width="100%" />
      </div>
    </div>
  );
}

export default StockChart;