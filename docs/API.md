<!-- omit from toc -->
# API

This document summarizes the API endpoints specific to the Python Cloud Server.

## Base Server Infrastructure

The Python Cloud Server is built from [python-template-server](https://github.com/javidahmed64592/python-template-server), which provides production-ready infrastructure including:

- **API Key Authentication**: All authenticated endpoints require the `X-API-KEY` header with a SHA-256 hashed token
- **Rate Limiting**: Configurable request throttling (default: 10 requests/minute per IP)
- **Security Headers**: Automatic HSTS, CSP, and X-Frame-Options enforcement
- **Request Logging**: Comprehensive logging of all requests/responses with client IP tracking
- **Health Checks**: Standard `/api/health` endpoint for availability monitoring
- **HTTPS Support**: Built-in SSL certificate generation and management

For detailed information about these features, authentication token generation, server middleware, and base configuration, see the [python-template-server README](https://github.com/javidahmed64592/python-template-server/blob/main/README.md).

<!-- omit from toc -->
## Table of Contents
- [Base Server Infrastructure](#base-server-infrastructure)
- [Cloud Server Endpoints](#cloud-server-endpoints)
  - [GET /api/files](#get-apifiles)
  - [GET /api/files/{filepath}](#get-apifilesfilepath)
  - [POST /api/files/{filepath}](#post-apifilesfilepath)
  - [PATCH /api/files/{filepath}](#patch-apifilesfilepath)
  - [DELETE /api/files/{filepath}](#delete-apifilesfilepath)
- [Request and Response Models (Pydantic)](#request-and-response-models-pydantic)
  - [Configuration Models](#configuration-models)
  - [File Metadata Model](#file-metadata-model)
  - [API Response Models](#api-response-models)
  - [API Request Models](#api-request-models)

## Cloud Server Endpoints

The Python Cloud Server adds file storage and management endpoints on top of the base infrastructure provided by the template server. All file endpoints require authentication and are subject to rate limiting.

### GET /api/files

**Purpose**: List files stored on the server with optional filtering by tag and pagination.

**Request**: JSON body with `GetFilesRequest` model
- `tag` (string, optional): Filter files by tag
- `offset` (int, default 0): Pagination offset
- `limit` (int, default 100, max 1000): Number of files to return

**Response Model**: `GetFilesResponse`
- `code` (int): HTTP status code
- `message` (string): Status message
- `timestamp` (string): ISO 8601 timestamp
- `files` (list[FileMetadata]): List of file metadata
- `total` (int): Total number of files matching the filter

**Example Request**:
```bash
curl -k https://localhost:443/api/files \
  -H "X-API-Key: your-api-token-here" \
  -H "Content-Type: application/json" \
  -d '{"tag": "animal", "offset": 0, "limit": 10}'
```

**Example Response** (200 OK):
```json
{
  "code": 200,
  "message": "Files retrieved successfully",
  "timestamp": "2025-12-31T12:00:00.000000Z",
  "files": [
    {
      "filepath": "animals/cat.png",
      "mime_type": "image/png",
      "size": 1024,
      "tags": ["animal", "pet"],
      "uploaded_at": "2025-12-31T10:00:00.000000Z",
      "updated_at": "2025-12-31T11:00:00.000000Z"
    }
  ],
  "total": 1
}
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid API key
- `429 Too Many Requests`: Rate limit exceeded

### GET /api/files/{filepath}

**Purpose**: Download a specific file from the server.

**Request**: None (filepath in URL path)

**Response**: File content with appropriate MIME type and filename

**Example Request**:
```bash
curl -k https://localhost:443/api/files/animals/cat.png \
  -H "X-API-Key: your-api-token-here" \
  -o cat.png
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid API key
- `404 Not Found`: File not found
- `429 Too Many Requests`: Rate limit exceeded

### POST /api/files/{filepath}

**Purpose**: Upload a new file to the server.

**Request**: Multipart form data with file upload
- `file`: The file to upload

**Response Model**: `PostFileResponse`
- `code` (int): HTTP status code
- `message` (string): Status message
- `timestamp` (string): ISO 8601 timestamp
- `filepath` (string): Path where the file was stored
- `size` (int): File size in bytes

**Example Request**:
```bash
curl -k https://localhost:443/api/files/animals/cat.png \
  -H "X-API-Key: your-api-token-here" \
  -F "file=@cat.png"
```

**Example Response** (200 OK):
```json
{
  "code": 200,
  "message": "File uploaded successfully",
  "timestamp": "2025-12-31T12:00:00.000000Z",
  "filepath": "animals/cat.png",
  "size": 1024
}
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid API key
- `409 Conflict`: File already exists
- `413 Payload Too Large`: File exceeds maximum size
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Upload failed

### PATCH /api/files/{filepath}

**Purpose**: Update file metadata (tags) or rename/move the file.

**Request**: JSON body with `PatchFileRequest` model
- `new_filepath` (string, optional): New path for the file (for renaming/moving)
- `add_tags` (list[string]): Tags to add to the file
- `remove_tags` (list[string]): Tags to remove from the file

**Response Model**: `PatchFileResponse`
- `code` (int): HTTP status code
- `message` (string): Status message
- `timestamp` (string): ISO 8601 timestamp
- `success` (bool): Whether the update was successful
- `filepath` (string): Current file path
- `tags` (list[string]): Updated list of tags

**Example Request**:
```bash
curl -k -X PATCH https://localhost:443/api/files/animals/cat.png \
  -H "X-API-Key: your-api-token-here" \
  -H "Content-Type: application/json" \
  -d '{"add_tags": ["cute"], "remove_tags": ["pet"]}'
```

**Example Response** (200 OK):
```json
{
  "code": 200,
  "message": "File updated successfully",
  "timestamp": "2025-12-31T12:00:00.000000Z",
  "success": true,
  "filepath": "animals/cat.png",
  "tags": ["animal", "cute"]
}
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid API key
- `404 Not Found`: File not found
- `400 Bad Request`: Invalid tag length or too many tags
- `429 Too Many Requests`: Rate limit exceeded

### DELETE /api/files/{filepath}

**Purpose**: Delete a file from the server.

**Request**: None

**Response Model**: `DeleteFileResponse`
- `code` (int): HTTP status code
- `message` (string): Status message
- `timestamp` (string): ISO 8601 timestamp
- `success` (bool): Whether the deletion was successful
- `filepath` (string): Path of the deleted file

**Example Request**:
```bash
curl -k -X DELETE https://localhost:443/api/files/animals/cat.png \
  -H "X-API-Key: your-api-token-here"
```

**Example Response** (200 OK):
```json
{
  "code": 200,
  "message": "File deleted successfully",
  "timestamp": "2025-12-31T12:00:00.000000Z",
  "success": true,
  "filepath": "animals/cat.png"
}
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid API key
- `404 Not Found`: File not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Deletion failed

## Request and Response Models (Pydantic)

The Python Cloud Server defines additional Pydantic models for file operations, extending the base models from the template server.

### Configuration Models

- `StorageConfig`: Configuration for storage settings
  - `server_directory` (string): Server directory path
  - `storage_directory` (string): Directory for storing files
  - `metadata_filename` (string): Metadata file name
  - `capacity_gb` (int): Storage capacity in GB
  - `upload_chunk_size_kb` (int): Upload chunk size in KB
  - `max_file_size_mb` (int): Maximum file size in MB
  - `max_tags_per_file` (int): Maximum tags per file
  - `max_tag_length` (int): Maximum tag length

- `CloudServerConfig`: Extends `TemplateServerConfig` with `storage_config`

### File Metadata Model

- `FileMetadata`: Metadata for stored files
  - `filepath` (string): Relative file path
  - `mime_type` (string): MIME type
  - `size` (int): File size in bytes
  - `tags` (list[string]): Associated tags
  - `uploaded_at` (string): Upload timestamp (ISO 8601)
  - `updated_at` (string): Last update timestamp (ISO 8601)

### API Response Models

- `GetFilesResponse`: Extends `BaseResponse`
  - `files` (list[FileMetadata]): List of files
  - `total` (int): Total matching files

- `PostFileResponse`: Extends `BaseResponse`
  - `filepath` (string): Stored file path
  - `size` (int): File size

- `PatchFileResponse`: Extends `BaseResponse`
  - `success` (bool): Update success
  - `filepath` (string): File path
  - `tags` (list[string]): Updated tags

- `DeleteFileResponse`: Extends `BaseResponse`
  - `success` (bool): Deletion success
  - `filepath` (string): Deleted file path

### API Request Models

- `GetFilesRequest`: Request for listing files
  - `tag` (string, optional): Tag filter
  - `offset` (int): Pagination offset
  - `limit` (int): Pagination limit

- `PatchFileRequest`: Request for updating files
  - `new_filepath` (string, optional): New file path
  - `add_tags` (list[string]): Tags to add
  - `remove_tags` (list[string]): Tags to remove
