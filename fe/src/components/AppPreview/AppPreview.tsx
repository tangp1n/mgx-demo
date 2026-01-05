import React, { useState, useEffect } from "react";
import { Application } from "../../types/api";
import "./AppPreview.css";

interface AppPreviewProps {
  application: Application;
}

const AppPreview: React.FC<AppPreviewProps> = ({ application }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const applicationId = application._id || application.id || "";

  useEffect(() => {
    // If application already has a preview URL, use it
    if (application.preview_url) {
      setPreviewUrl(application.preview_url);
      setLoading(false);
      return;
    }

    // If application is running but no preview URL, fetch it
    if (application.status === "running") {
      fetchPreviewInfo();
    } else if (application.status === "error") {
      setError("Application failed to deploy");
      setLoading(false);
    } else {
      setLoading(false);
    }
  }, [application]);

  const fetchPreviewInfo = async () => {
    try {
      const response = await fetch(`/api/v1/applications/${applicationId}/preview`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch preview information");
      }

      const data = await response.json();
      if (data.preview_url) {
        setPreviewUrl(data.preview_url);
      } else {
        setError("Preview URL not available yet");
      }
    } catch (err: any) {
      setError(err.message || "Failed to load preview");
    } finally {
      setLoading(false);
    }
  };

  const handleIframeLoad = () => {
    setLoading(false);
  };

  const handleIframeError = () => {
    setError("Failed to load application preview");
    setLoading(false);
  };

  const getStatusMessage = () => {
    switch (application.status) {
      case "draft":
        return "Application requirements are being discussed";
      case "requirements_confirmed":
        return "Requirements confirmed. Ready to generate code.";
      case "generating":
        return "Generating application code...";
      case "deploying":
        return "Deploying application to container...";
      case "running":
        return previewUrl ? null : "Application is running. Loading preview...";
      case "stopped":
        return "Application has been stopped";
      case "error":
        return "An error occurred during deployment";
      default:
        return "Unknown status";
    }
  };

  const statusMessage = getStatusMessage();

  if (error) {
    return (
      <div className="app-preview">
        <div className="app-preview-error">
          <div className="error-icon">⚠️</div>
          <h3>Preview Error</h3>
          <p>{error}</p>
          {application.status === "error" && (
            <p className="error-hint">
              Check the conversation for error details or try generating the application again.
            </p>
          )}
        </div>
      </div>
    );
  }

  if (statusMessage) {
    return (
      <div className="app-preview">
        <div className="app-preview-status">
          <div className="status-icon">
            {application.status === "generating" || application.status === "deploying" ? (
              <div className="spinner"></div>
            ) : (
              "📋"
            )}
          </div>
          <h3>{statusMessage}</h3>
          {(application.status === "generating" || application.status === "deploying") && (
            <p className="status-hint">
              Follow the progress in the conversation panel →
            </p>
          )}
        </div>
      </div>
    );
  }

  if (!previewUrl) {
    return (
      <div className="app-preview">
        <div className="app-preview-empty">
          <div className="empty-icon">🚀</div>
          <h3>No Preview Available</h3>
          <p>Generate your application to see a live preview here</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-preview">
      <div className="app-preview-header">
        <span className="preview-label">Live Preview</span>
        <a
          href={previewUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="preview-link"
        >
          Open in New Tab ↗
        </a>
      </div>
      {loading && (
        <div className="app-preview-loading">
          <div className="spinner"></div>
          <p>Loading preview...</p>
        </div>
      )}
      <iframe
        src={previewUrl}
        className="app-preview-iframe"
        title="Application Preview"
        onLoad={handleIframeLoad}
        onError={handleIframeError}
        style={{ display: loading ? "none" : "block" }}
      />
    </div>
  );
};

export default AppPreview;
