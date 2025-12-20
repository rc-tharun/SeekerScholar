/**
 * API helper functions for SeekerScholar frontend.
 * Centralizes API base URL configuration and provides reusable fetch helpers.
 */

// Get API base URL from environment variable
// Normalize: remove trailing slash and handle missing env var
const getBaseUrl = (): string => {
  const base = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000'
  // Remove trailing slash if present
  return base.replace(/\/+$/, '')
}

const BASE_URL = getBaseUrl()

/**
 * Build a full URL from a path.
 * @param path - API path (e.g., '/search' or 'search')
 * @returns Full URL
 */
export function buildUrl(path: string): string {
  // Ensure path starts with /
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${BASE_URL}${normalizedPath}`
}

/**
 * Perform a GET request.
 * @param path - API path
 * @param signal - Optional AbortSignal for request cancellation
 * @returns Promise with parsed JSON response
 */
export async function apiGet<T = any>(path: string, signal?: AbortSignal): Promise<T> {
  const url = buildUrl(path)
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    signal,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Perform a POST request with JSON body.
 * @param path - API path
 * @param body - Request body object (will be JSON stringified)
 * @param signal - Optional AbortSignal for request cancellation
 * @returns Promise with parsed JSON response
 */
export async function apiPost<T = any>(path: string, body: any, signal?: AbortSignal): Promise<T> {
  const url = buildUrl(path)
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
    signal,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Perform a POST request with FormData (for file uploads).
 * @param path - API path
 * @param formData - FormData object
 * @param signal - Optional AbortSignal for request cancellation
 * @returns Promise with parsed JSON response
 */
export async function apiPostFormData<T = any>(path: string, formData: FormData, signal?: AbortSignal): Promise<T> {
  const url = buildUrl(path)
  const response = await fetch(url, {
    method: 'POST',
    body: formData,
    signal,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
  }

  return response.json()
}

