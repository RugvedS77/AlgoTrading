import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

function Signup() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSignup = async (e) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      alert("Passwords do not match!");
      return;
    }

    setLoading(true);

    try {
      // -------------------- 1️⃣ Create User --------------------
      const userResponse = await fetch("http://localhost:8000/user", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: 15, // placeholder, backend will assign actual id
          username: username,
          email: email,
          password: password,
          created_at: new Date().toISOString(),
        }),
      });

      if (!userResponse.ok) {
        const errData = await userResponse.json();
        throw new Error(errData.detail || JSON.stringify(errData));
      }

      const userData = await userResponse.json();
      console.log("✅ User created:", userData);

      // -------------------- 2️⃣ Create Trading Account --------------------
      const accountResponse = await fetch("http://localhost:8000/account", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_name: username,
          total_equity: 100000,
          cash_available: 100000,
          risk_limits: {
            max_drawdown: 0.2,
            max_position_size: 0.1,
          },
        }),
      });

      if (!accountResponse.ok) {
        const errData = await accountResponse.json();
        throw new Error(errData.detail || JSON.stringify(errData));
      }

      const accountData = await accountResponse.json();
      console.log("✅ Trading account created:", accountData);

      alert("Signup successful! You can now login.");
      navigate("/login");
    } catch (error) {
      console.error("❌ Signup error:", error);
      alert(error.message || "Error creating account. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-green-50 to-green-100">
      <div className="bg-white p-8 rounded-2xl shadow-lg w-full max-w-md">
        <h2 className="text-2xl font-bold text-center mb-6 text-gray-700">
          📝 Sign Up
        </h2>
        <form onSubmit={handleSignup} className="space-y-4">
          <div>
            <label className="block text-gray-600 font-medium mb-1">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="w-full border px-3 py-2 rounded-lg focus:ring-2 focus:ring-green-400"
              placeholder="Enter your username"
            />
          </div>
          <div>
            <label className="block text-gray-600 font-medium mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full border px-3 py-2 rounded-lg focus:ring-2 focus:ring-green-400"
              placeholder="Enter your email"
            />
          </div>
          <div>
            <label className="block text-gray-600 font-medium mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full border px-3 py-2 rounded-lg focus:ring-2 focus:ring-green-400"
              placeholder="Enter your password"
            />
          </div>
          <div>
            <label className="block text-gray-600 font-medium mb-1">Confirm Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              className="w-full border px-3 py-2 rounded-lg focus:ring-2 focus:ring-green-400"
              placeholder="Confirm your password"
            />
          </div>
          <button
            type="submit"
            className={`w-full bg-green-600 text-white font-semibold py-2 rounded-lg shadow hover:bg-green-700 transition ${
              loading ? "opacity-70 cursor-not-allowed" : ""
            }`}
            disabled={loading}
          >
            {loading ? "Creating account..." : "Sign Up"}
          </button>
        </form>
        <p className="text-center text-gray-600 mt-4">
          Already have an account?{" "}
          <Link to="/login" className="text-green-600 font-semibold hover:underline">
            Login
          </Link>
        </p>
      </div>
    </div>
  );
}

export default Signup;
