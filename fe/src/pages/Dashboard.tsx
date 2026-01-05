import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import CreateApplication from "../components/Application/CreateApplication";
import ApplicationList from "../components/Application/ApplicationList";
import Conversation from "../components/Conversation/Conversation";
import CodeEditor from "../components/CodeEditor/CodeEditor";
import AppPreview from "../components/AppPreview/AppPreview";
import { Application } from "../types/api";
import { applicationAPI } from "../services/api";
import "./Dashboard.css";

export default function Dashboard() {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [applications, setApplications] = useState<Application[]>([]);
  const [selectedApplication, setSelectedApplication] = useState<Application | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"preview" | "code">("preview");

  useEffect(() => {
    if (isAuthenticated) {
      loadApplications();
    }
  }, [isAuthenticated]);

  // Poll selected application status for real-time updates
  useEffect(() => {
    if (!selectedApplication) return;

    const applicationId = getApplicationId(selectedApplication);
    if (!applicationId) return;

    // Poll every 2 seconds when application is in transitional states or draft
    // We poll draft status to detect when it changes to requirements_confirmed
    const shouldPoll = [
      "draft",
      "requirements_confirmed",
      "generating",
      "deploying"
    ].includes(selectedApplication.status);

    if (!shouldPoll) return;

    const pollInterval = setInterval(async () => {
      try {
        const updatedApp = await applicationAPI.get(applicationId);
        setSelectedApplication(updatedApp);

        // Update in applications list as well
        setApplications(prev =>
          prev.map(app =>
            getApplicationId(app) === applicationId ? updatedApp : app
          )
        );
      } catch (err) {
        console.error("Failed to poll application status:", err);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [selectedApplication?.status, selectedApplication?.id, selectedApplication?._id]);

  const loadApplications = async () => {
    setLoading(true);
    setError(null);
    try {
      const apps = await applicationAPI.list();
      setApplications(apps);
    } catch (err: any) {
      setError(err.response?.data?.message || "Failed to load applications");
    } finally {
      setLoading(false);
    }
  };

  const handleApplicationCreated = (application: Application) => {
    setApplications((prev) => [application, ...prev]);
    setShowCreateModal(false);
    setSelectedApplication(application);
  };

  const handleSelectApplication = (application: Application) => {
    setSelectedApplication(application);
  };

  const handleBackToList = () => {
    setSelectedApplication(null);
  };

  const getApplicationId = (app: Application) => app._id || app.id || "";

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  if (!isAuthenticated) {
    return (
      <div className="dashboard-container">
        <div className="dashboard-card">
          <p>Please log in to access the dashboard.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>AI App Builder</h1>
        <div className="dashboard-user-info">
          <span>Welcome, {user?.email}</span>
          <button onClick={handleLogout} className="logout-button">
            Logout
          </button>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="dashboard-content">
        {selectedApplication ? (
          <div className="dashboard-conversation-view">
            <div className="conversation-header-bar">
              <button onClick={handleBackToList} className="back-button">
                ← Back to Apps
              </button>
              <h2>{selectedApplication.name || "Untitled Application"}</h2>
            </div>
            <div className="dashboard-split-view">
              <div className="dashboard-conversation-panel">
                <Conversation
                  application={selectedApplication}
                  onApplicationUpdate={(updatedApp) => {
                    setSelectedApplication(updatedApp);
                    // Also update in applications list
                    setApplications(prev =>
                      prev.map(app => {
                        const appId = getApplicationId(app);
                        const updatedAppId = getApplicationId(updatedApp);
                        return appId === updatedAppId ? updatedApp : app;
                      })
                    );
                  }}
                />
              </div>
              <div className="dashboard-workspace">
                <div className="workspace-tabs">
                  <button
                    className={`tab-button ${activeTab === "preview" ? "active" : ""}`}
                    onClick={() => setActiveTab("preview")}
                  >
                    Preview
                  </button>
                  <button
                    className={`tab-button ${activeTab === "code" ? "active" : ""}`}
                    onClick={() => setActiveTab("code")}
                  >
                    Code
                  </button>
                </div>
                <div className="workspace-content">
                  {activeTab === "preview" ? (
                    <div className="workspace-panel">
                      <AppPreview application={selectedApplication} />
                    </div>
                  ) : (
                    <div className="workspace-panel">
                      {selectedApplication.container_id ? (
                        <CodeEditor application={selectedApplication} />
                      ) : (
                        <div className="workspace-empty">
                          <p>容器尚未创建。请先确认需求以生成代码。</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="dashboard-list-view">
            <div className="app-list-header">
              <h2>Your Applications</h2>
              <button
                onClick={() => setShowCreateModal(true)}
                className="create-app-button"
              >
                + Create New App
              </button>
            </div>
            {loading ? (
              <div className="loading-state">
                <p>Loading applications...</p>
              </div>
            ) : (
              <ApplicationList
                applications={applications}
                onSelectApplication={handleSelectApplication}
                selectedApplicationId={undefined}
              />
            )}
          </div>
        )}
      </div>

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <CreateApplication
              onApplicationCreated={handleApplicationCreated}
              onClose={() => setShowCreateModal(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
}

