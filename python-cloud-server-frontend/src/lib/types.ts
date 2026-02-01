// TypeScript types matching FastAPI Pydantic models

// Base response types
export interface BaseResponse {
  message: string;
  timestamp: string;
}

// Authentication types
export interface AuthContextType {
  apiKey: string | null;
  isAuthenticated: boolean;
  login: (apiKey: string) => Promise<void>;
  logout: () => void;
}

// Metadata types
export interface FileMetadata {
  filepath: string;
  mimeType: string;
  size: number;
  tags: string[];
  uploadedAt: string;
  updatedAt: string;
}

// Response types
export interface HealthResponse extends BaseResponse {}

export interface LoginResponse extends BaseResponse {}

export interface GetFilesResponse extends BaseResponse {
  files: FileMetadata[];
}

export interface PostFileResponse extends BaseResponse {
  filepath: string;
  size: number;
}

export interface PatchFileResponse extends BaseResponse {
  filepath: string;
  tags: string[];
}

export interface DeleteFileResponse extends BaseResponse {
  filepath: string;
}

// Request types
export interface GetFilesRequest {
  tag?: string;
  offset?: number;
  limit?: number;
}

export interface PatchFileRequest {
  newFilepath?: string;
  addTags?: string[];
  removeTags?: string[];
}
