import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";
import { AuthProvider } from "./hooks/useAuth";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import ProtectedRoute from "./components/shared/ProtectedRoute";
import PublicRoute from "./components/shared/PublicRoute";
import "./App.css";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1";

function App() {
  return (
    <CopilotKit url={API_URL}>
      <AuthProvider>
        <Router>
          <div className="App">
            <Routes>
              <Route
                path="/login"
                element={
                  <PublicRoute>
                    <Login />
                  </PublicRoute>
                }
              />
              <Route
                path="/register"
                element={
                  <PublicRoute>
                    <Register />
                  </PublicRoute>
                }
              />
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                }
              />
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </div>
        </Router>
      </AuthProvider>
    </CopilotKit>
  );
}

export default App;

