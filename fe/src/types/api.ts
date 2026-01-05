// API Response Types

export interface User {
  _id: string;
  id?: string;  // Alias for _id
  email: string;
  created_at: string;
  updated_at: string;
}

export interface LoginResponse {
  token: string;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface ErrorResponse {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface Application {
  _id: string;
  id?: string;  // Alias for _id
  user_id: string;
  name?: string;
  requirements: string;
  requirements_confirmed: boolean;
  status: ApplicationStatus;
  container_id?: string;
  preview_url?: string;
  port?: number;
  created_at: string;
  updated_at: string;
  last_deployed_at?: string;
}

export type ApplicationStatus =
  | "draft"
  | "requirements_confirmed"
  | "generating"
  | "deploying"
  | "running"
  | "stopped"
  | "error";

export interface Conversation {
  _id: string;
  id?: string;  // Alias for _id
  application_id: string;
  user_id: string;
  messages: Message[];
  status: ConversationStatus;
  created_at: string;
  updated_at: string;
}

export type ConversationStatus = "active" | "paused" | "completed" | "error";

export interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  events?: AgentEvent[];
}

export interface AgentEvent {
  type: "thought" | "tool_call" | "tool_call_result" | "text" | "error";
  data: Record<string, unknown>;
  timestamp: string;
}

export interface ListResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface HealthCheckResponse {
  status: "healthy" | "unhealthy";
  service: string;
  version: string;
  checks?: {
    [key: string]: {
      status: "healthy" | "unhealthy";
      message: string;
    };
  };
}

