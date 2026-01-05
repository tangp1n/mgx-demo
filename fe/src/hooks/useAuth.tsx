import { useState, useEffect, createContext, useContext, ReactNode } from "react";
import apiClient from "../services/api";
import { User, LoginResponse, LoginRequest, RegisterRequest, ErrorResponse } from "../types/api";

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Initialize auth state from localStorage
  useEffect(() => {
    const storedToken = localStorage.getItem("auth_token");
    const storedUser = localStorage.getItem("auth_user");

    if (storedToken && storedUser) {
      setToken(storedToken);
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        // Invalid stored user data, clear it
        localStorage.removeItem("auth_token");
        localStorage.removeItem("auth_user");
      }
    }
    setLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await apiClient.post<LoginResponse>("/auth/login", {
        email,
        password,
      } as LoginRequest);

      const { token: newToken, user: newUser } = response.data;
      setToken(newToken);
      setUser(newUser);
      localStorage.setItem("auth_token", newToken);
      localStorage.setItem("auth_user", JSON.stringify(newUser));
    } catch (error: any) {
      const errorResponse = error.response?.data as ErrorResponse | undefined;
      throw new Error(errorResponse?.message || "Login failed");
    }
  };

  const register = async (email: string, password: string) => {
    try {
      await apiClient.post("/auth/register", {
        email,
        password,
      } as RegisterRequest);
      // After registration, automatically log in
      await login(email, password);
    } catch (error: any) {
      console.error("Registration error:", error);
      const errorResponse = error.response?.data;

      // Handle validation errors with details
      if (error.response?.status === 400 || error.response?.status === 422) {
        if (errorResponse?.details && Array.isArray(errorResponse.details)) {
          // FastAPI validation errors
          const detailMessages = errorResponse.details
            .map((detail: any) => {
              const field = detail.loc?.join(".");
              const msg = detail.msg || "Invalid value";
              return field ? `${field}: ${msg}` : msg;
            })
            .join(", ");
          throw new Error(detailMessages || errorResponse.message || "Validation failed");
        }
      }

      // Handle application errors
      const message = errorResponse?.message || error.message || "Registration failed";
      throw new Error(message);
    }
  };

  const logout = async () => {
    try {
      await apiClient.post("/auth/logout");
    } catch (error) {
      // Even if logout fails on server, clear local state
      console.error("Logout error:", error);
    } finally {
      setToken(null);
      setUser(null);
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_user");
    }
  };

  const isAuthenticated = !!token && !!user;

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        logout,
        isAuthenticated,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

