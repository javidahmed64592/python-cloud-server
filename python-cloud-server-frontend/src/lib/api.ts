import axios from "axios";
import { useEffect, useState } from "react";

import { getApiKey } from "@/lib/auth";
import type {
  DeleteFileResponse,
  GetFilesRequest,
  GetFilesResponse,
  FileMetadata,
  HealthResponse,
  LoginResponse,
  PatchFileRequest,
  PatchFileResponse,
  PostFileResponse,
} from "@/lib/types";

// Determine the base URL based on environment
const getBaseURL = () => {
  if (typeof window === "undefined") return "";

  // In production static build, API is served from same origin
  if (process.env.NODE_ENV === "production") {
    return window.location.origin;
  }

  // In development, proxy to backend (handled by Next.js rewrites)
  return "";
};

// API client configuration
const api = axios.create({
  baseURL: getBaseURL() + "/api", // This will be proxied in dev, direct in production
  timeout: 60000, // 60 seconds timeout for LLM responses
  headers: {
    "Content-Type": "application/json",
  },
});

// Add request interceptor to include API key
api.interceptors.request.use(
  config => {
    const apiKey = getApiKey();
    if (apiKey) {
      config.headers["X-API-KEY"] = apiKey;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Health status type
export type HealthStatus = "online" | "offline" | "checking";

// API response type for file metadata (snake_case from backend)
interface ApiFileMetadata {
  filepath: string;
  mime_type: string;
  size: number;
  tags: string[];
  uploaded_at: string;
  updated_at: string;
}

// Transform snake_case API response to camelCase
const transformFileMetadata = (data: ApiFileMetadata): FileMetadata => ({
  filepath: data.filepath,
  mimeType: data.mime_type,
  size: data.size,
  tags: data.tags,
  uploadedAt: data.uploaded_at,
  updatedAt: data.updated_at,
});

const extractErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    if (error.response) {
      const errorData = error.response.data;

      // Check for BaseResponse format with message field
      if (errorData?.message) {
        return errorData.message;
      }

      // Check for detail field (common in FastAPI errors)
      if (errorData?.detail) {
        return typeof errorData.detail === "string"
          ? errorData.detail
          : JSON.stringify(errorData.detail);
      }

      // Fallback to generic server error
      return `Server error: ${error.response.status} ${error.response.statusText}`;
    } else if (error.request) {
      return "No response from server. Please check if the backend is running.";
    } else {
      return `Request failed: ${error.message}`;
    }
  }
  return "An unexpected error occurred";
};

// API functions
export const getHealth = async (): Promise<HealthResponse> => {
  try {
    const response = await api.get<HealthResponse>("/health");
    return response.data;
  } catch (error) {
    throw new Error(extractErrorMessage(error));
  }
};

export const login = async (apiKey: string): Promise<LoginResponse> => {
  try {
    const response = await api.get<LoginResponse>("/login", {
      headers: {
        "X-API-KEY": apiKey,
      },
    });
    return response.data;
  } catch (error) {
    throw new Error(extractErrorMessage(error));
  }
};

// API response type for getFiles (snake_case from backend)
interface ApiGetFilesResponse {
  message: string;
  timestamp: string;
  files: ApiFileMetadata[];
}

// File operations
export const getFiles = async (
  request: GetFilesRequest = {}
): Promise<GetFilesResponse> => {
  try {
    const response = await api.post<ApiGetFilesResponse>("/files", request);
    return {
      ...response.data,
      files: response.data.files.map(transformFileMetadata),
    };
  } catch (error) {
    throw new Error(extractErrorMessage(error));
  }
};

export const getThumbnail = async (filepath: string): Promise<string> => {
  try {
    const response = await api.get(`/files/${filepath}/thumbnail`, {
      responseType: "blob",
    });
    return URL.createObjectURL(response.data);
  } catch (error) {
    throw new Error(extractErrorMessage(error));
  }
};

export const downloadFile = async (filepath: string): Promise<Blob> => {
  try {
    const response = await api.get(`/files/${filepath}`, {
      responseType: "blob",
    });
    return response.data;
  } catch (error) {
    throw new Error(extractErrorMessage(error));
  }
};

export const uploadFile = async (
  filepath: string,
  file: File
): Promise<PostFileResponse> => {
  try {
    const formData = new FormData();
    formData.append("file", file);

    const response = await api.post<PostFileResponse>(
      `/files/${filepath}`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return response.data;
  } catch (error) {
    throw new Error(extractErrorMessage(error));
  }
};

export const patchFile = async (
  filepath: string,
  request: PatchFileRequest
): Promise<PatchFileResponse> => {
  try {
    const response = await api.patch<PatchFileResponse>(
      `/files/${filepath}`,
      request
    );
    return response.data;
  } catch (error) {
    throw new Error(extractErrorMessage(error));
  }
};

export const deleteFile = async (
  filepath: string
): Promise<DeleteFileResponse> => {
  try {
    const response = await api.delete<DeleteFileResponse>(`/files/${filepath}`);
    return response.data;
  } catch (error) {
    throw new Error(extractErrorMessage(error));
  }
};

// Health status hook
export function useHealthStatus(): HealthStatus {
  const [status, setStatus] = useState<HealthStatus>("checking");

  useEffect(() => {
    let isMounted = true;

    const checkHealth = async () => {
      try {
        await getHealth();
        if (isMounted) {
          setStatus("online");
        }
      } catch {
        if (isMounted) {
          setStatus("offline");
        }
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // every 30s
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return status;
}

export default api;
