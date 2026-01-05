import React, { useState } from "react";
import { applicationAPI } from "../../services/api";
import { Application } from "../../types/api";

interface CreateApplicationProps {
  onApplicationCreated: (application: Application) => void;
  onClose: () => void;
}

const CreateApplication: React.FC<CreateApplicationProps> = ({ onApplicationCreated, onClose }) => {
  const [name, setName] = useState("");
  const [requirements, setRequirements] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const application = await applicationAPI.create({
        name: name || undefined,
        requirements,
      });

      onApplicationCreated(application);

      // Reset form
      setName("");
      setRequirements("");
    } catch (err: any) {
      setError(err.response?.data?.message || "Failed to create application");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="create-application-modal">
      <div className="modal-header">
        <h2>Create New Application</h2>
        <button type="button" className="close-button" onClick={onClose}>
          ×
        </button>
      </div>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="name">Application Name (Optional)</label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="My Awesome App"
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="requirements">Requirements *</label>
          <textarea
            id="requirements"
            value={requirements}
            onChange={(e) => setRequirements(e.target.value)}
            placeholder="Describe what you want to build..."
            rows={6}
            required
            disabled={loading}
          />
        </div>

        {error && <div className="error-message">{error}</div>}

        <div className="form-actions">
          <button type="button" onClick={onClose} className="cancel-button" disabled={loading}>
            Cancel
          </button>
          <button type="submit" disabled={loading || !requirements.trim()} className="submit-button">
            {loading ? "Creating..." : "Create Application"}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateApplication;
