import React from "react";
import { Application } from "../../types/api";
import "./ApplicationStatus.css";

interface ApplicationStatusProps {
  application: Application;
  showDetailed?: boolean;
}

const ApplicationStatus: React.FC<ApplicationStatusProps> = ({
  application,
  showDetailed = false
}) => {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case "draft":
        return {
          label: "Draft",
          icon: "📝",
          color: "gray",
          description: "Discussing requirements"
        };
      case "requirements_confirmed":
        return {
          label: "Requirements Confirmed",
          icon: "✅",
          color: "green",
          description: "Ready to generate code"
        };
      case "generating":
        return {
          label: "Generating",
          icon: "⚙️",
          color: "blue",
          description: "Creating application code",
          animated: true
        };
      case "deploying":
        return {
          label: "Deploying",
          icon: "🚀",
          color: "purple",
          description: "Setting up container environment",
          animated: true
        };
      case "running":
        return {
          label: "Running",
          icon: "✨",
          color: "success",
          description: "Application is live"
        };
      case "stopped":
        return {
          label: "Stopped",
          icon: "⏸️",
          color: "gray",
          description: "Application stopped"
        };
      case "error":
        return {
          label: "Error",
          icon: "❌",
          color: "error",
          description: "Deployment failed"
        };
      default:
        return {
          label: "Unknown",
          icon: "❓",
          color: "gray",
          description: "Unknown status"
        };
    }
  };

  const config = getStatusConfig(application.status);

  if (!showDetailed) {
    return (
      <span className={`status-badge status-${config.color}`}>
        <span className="status-icon">{config.icon}</span>
        <span className="status-label">{config.label}</span>
      </span>
    );
  }

  return (
    <div className="application-status-detailed">
      <div className={`status-indicator status-${config.color}`}>
        <div className={`status-icon-large ${config.animated ? 'animated' : ''}`}>
          {config.icon}
        </div>
        <div className="status-info">
          <h4 className="status-title">{config.label}</h4>
          <p className="status-description">{config.description}</p>
        </div>
      </div>

      {application.status === "running" && application.preview_url && (
        <div className="status-metadata">
          <div className="metadata-item">
            <span className="metadata-label">Preview URL:</span>
            <a
              href={application.preview_url}
              target="_blank"
              rel="noopener noreferrer"
              className="metadata-value link"
            >
              {application.preview_url}
            </a>
          </div>
          {application.port && (
            <div className="metadata-item">
              <span className="metadata-label">Port:</span>
              <span className="metadata-value">{application.port}</span>
            </div>
          )}
        </div>
      )}

      {application.status === "error" && (
        <div className="status-error-hint">
          <p>Check the conversation panel for error details or try generating again.</p>
        </div>
      )}

      {(application.status === "generating" || application.status === "deploying") && (
        <div className="status-progress-hint">
          <p>Follow real-time progress in the conversation panel →</p>
        </div>
      )}
    </div>
  );
};

export default ApplicationStatus;
