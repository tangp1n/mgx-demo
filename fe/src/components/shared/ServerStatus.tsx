import React, { useState, useEffect } from "react";
import { checkHealth } from "../../services/api";
import { HealthCheckResponse } from "../../types/api";
import "./ServerStatus.css";

export default function ServerStatus() {
  const [health, setHealth] = useState<HealthCheckResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchHealth = async () => {
    try {
      const healthStatus = await checkHealth();
      setHealth(healthStatus);
    } catch (error) {
      setHealth({
        status: "unhealthy",
        service: "AI-Powered Conversational App Builder Platform",
        version: "1.0.0",
        checks: {
          connection: {
            status: "unhealthy",
            message: "Failed to check server status",
          },
        },
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Check immediately
    fetchHealth();

    // Check every 30 seconds
    const interval = setInterval(fetchHealth, 30000);

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="server-status">
        <span className="server-status-indicator server-status-checking"></span>
        <span className="server-status-text">Checking...</span>
      </div>
    );
  }

  const isHealthy = health?.status === "healthy";

  return (
    <div className="server-status">
      <span
        className={`server-status-indicator ${
          isHealthy ? "server-status-healthy" : "server-status-unhealthy"
        }`}
      ></span>
      <span className="server-status-text">
        Server: {isHealthy ? "Online" : "Offline"}
      </span>
    </div>
  );
}

