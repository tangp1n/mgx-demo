import React from "react";
import ReactMarkdown from "react-markdown";
import { Application } from "../../types/api";

interface ApplicationListProps {
  applications: Application[];
  onSelectApplication: (application: Application) => void;
  selectedApplicationId?: string;
}

const ApplicationList: React.FC<ApplicationListProps> = ({
  applications,
  onSelectApplication,
  selectedApplicationId,
}) => {
  const getApplicationId = (app: Application) => app._id || app.id || "";

  const getStatusBadge = (status: string) => {
    const statusClasses: Record<string, string> = {
      draft: "status-draft",
      requirements_confirmed: "status-confirmed",
      generating: "status-generating",
      deploying: "status-deploying",
      running: "status-running",
      stopped: "status-stopped",
      error: "status-error",
    };

    return (
      <span className={`status-badge ${statusClasses[status] || ""}`}>
        {status.replace(/_/g, " ")}
      </span>
    );
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + " " + date.toLocaleTimeString();
  };

  if (applications.length === 0) {
    return (
      <div className="application-list-empty">
        <p>No applications yet. Create your first one above!</p>
      </div>
    );
  }

  return (
    <div className="application-list">
      <h3>Your Applications</h3>
      <div className="application-items">
        {applications.map((app) => (
          <div
            key={getApplicationId(app)}
            className={`application-item ${
              selectedApplicationId === getApplicationId(app) ? "selected" : ""
            }`}
            onClick={() => onSelectApplication(app)}
          >
            <div className="application-header">
              <h4>{app.name || "Untitled Application"}</h4>
              {getStatusBadge(app.status)}
            </div>
            <div className="application-requirements">
              <ReactMarkdown>
                {app.requirements.length > 200
                  ? app.requirements.substring(0, 200) + "..."
                  : app.requirements}
              </ReactMarkdown>
            </div>
            <div className="application-meta">
              <span>Created: {formatDate(app.created_at)}</span>
              {app.last_deployed_at && (
                <span>Deployed: {formatDate(app.last_deployed_at)}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ApplicationList;
