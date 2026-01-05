import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from "axios";
import { HealthCheckResponse, Application, Conversation } from "../types/api";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1";

// Extract base URL from API_URL (remove /api/v1 if present)
const getBaseUrl = (): string => {
  const apiUrl = process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1";
  if (apiUrl.includes("/api/v1")) {
    return apiUrl.replace("/api/v1", "");
  }
  // If no /api/v1, assume it's just the base URL or extract host:port
  if (apiUrl.startsWith("http")) {
    try {
      const url = new URL(apiUrl);
      return `${url.protocol}//${url.host}`;
    } catch {
      return "http://localhost:8000";
    }
  }
  return "http://localhost:8000";
};

const BASE_URL = getBaseUrl();

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("auth_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem("auth_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// Health check function (uses base URL, not API prefix)
export async function checkHealth(): Promise<HealthCheckResponse> {
  try {
    const response = await axios.get<HealthCheckResponse>(`${BASE_URL}/health`);
    return response.data;
  } catch (error: any) {
    // Return unhealthy status if request fails
    return {
      status: "unhealthy",
      service: "AI-Powered Conversational App Builder Platform",
      version: "1.0.0",
      checks: {
        connection: {
          status: "unhealthy",
          message: error.message || "Failed to connect to server",
        },
      },
    };
  }
}

export default apiClient;

// Application API functions
export const applicationAPI = {
  /**
   * Create a new application.
   */
  async create(data: { name?: string; requirements: string }): Promise<Application> {
    const response = await apiClient.post<Application>("/applications", data);
    return response.data;
  },

  /**
   * Get an application by ID.
   */
  async get(applicationId: string): Promise<Application> {
    const response = await apiClient.get<Application>(`/applications/${applicationId}`);
    return response.data;
  },

  /**
   * List all applications for the current user.
   */
  async list(skip: number = 0, limit: number = 100): Promise<Application[]> {
    const response = await apiClient.get<Application[]>("/applications", {
      params: { skip, limit },
    });
    return response.data;
  },

  /**
   * Update an application.
   */
  async update(
    applicationId: string,
    data: Partial<Application>
  ): Promise<Application> {
    const response = await apiClient.put<Application>(
      `/applications/${applicationId}`,
      data
    );
    return response.data;
  },

  /**
   * Confirm requirements for an application.
   */
  async confirmRequirements(applicationId: string): Promise<Application> {
    const response = await apiClient.post<Application>(
      `/applications/${applicationId}/confirm-requirements`
    );
    return response.data;
  },

  /**
   * Delete an application.
   */
  async delete(applicationId: string): Promise<void> {
    await apiClient.delete(`/applications/${applicationId}`);
  },

  /**
   * Get file tree for an application.
   */
  async getFileTree(applicationId: string, path: string = "/app"): Promise<{ files: any[] }> {
    const response = await apiClient.get(`/applications/${applicationId}/files`, {
      params: { path },
    });
    return response.data;
  },

  /**
   * Get file content from an application.
   */
  async getFileContent(applicationId: string, filePath: string): Promise<{ content: string; path: string }> {
    // Remove leading slash if present to avoid double slashes
    const cleanPath = filePath.startsWith('/') ? filePath.substring(1) : filePath;
    const response = await apiClient.get(`/applications/${applicationId}/files/${cleanPath}`);
    return response.data;
  },

  /**
   * Get preview information for an application.
   */
  async getPreview(applicationId: string): Promise<{ preview_url: string | null; port: number | null; status: string; container_id: string | null }> {
    const response = await apiClient.get(`/applications/${applicationId}/preview`);
    return response.data;
  },

  /**
   * Get SSE stream URL for code generation.
   */
  getGenerateStreamUrl(applicationId: string): string {
    const token = localStorage.getItem("auth_token");
    const baseUrl = API_URL.replace("/api/v1", "");
    return `${baseUrl}/api/v1/applications/${applicationId}/generate/stream${
      token ? `?token=${token}` : ""
    }`;
  },
};

// Conversation API functions
export const conversationAPI = {
  /**
   * Get conversation for an application.
   */
  async get(applicationId: string): Promise<Conversation> {
    const response = await apiClient.get<Conversation>(
      `/applications/${applicationId}/conversation`
    );
    return response.data;
  },

  /**
   * Send a message to the conversation.
   */
  async sendMessage(
    applicationId: string,
    content: string
  ): Promise<{ stream_url: string; message: string }> {
    const response = await apiClient.post(
      `/applications/${applicationId}/conversation`,
      { content }
    );
    return response.data;
  },

  /**
   * Get SSE stream URL for conversation.
   */
  getStreamUrl(applicationId: string): string {
    const token = localStorage.getItem("auth_token");
    const baseUrl = API_URL.replace("/api/v1", "");
    return `${baseUrl}/api/v1/applications/${applicationId}/conversation/stream${
      token ? `?token=${token}` : ""
    }`;
  },
};

