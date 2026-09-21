// API utility functions
import { API_BASE } from "./constants";

export const makeApiCall = async (endpoint, options = {}) => {
  const url = `${API_BASE}${endpoint}`;

  const defaultOptions = {
    headers: {
      "Content-Type": "application/json",
    },
  };

  const finalOptions = { ...defaultOptions, ...options };

  if (finalOptions.params) {
    // Leave out unset values rather than sending the string "null"
    const params = new URLSearchParams(
      Object.entries(finalOptions.params).filter(
        ([, value]) => value !== null && value !== undefined
      )
    );
    const paramString = params.toString();
    const fullUrl = paramString ? `${url}?${paramString}` : url;
    delete finalOptions.params;

    const response = await fetch(fullUrl, finalOptions);
    return await handleResponse(response);
  }

  const response = await fetch(url, finalOptions);
  return await handleResponse(response);
};

const handleResponse = async (response) => {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `HTTP ${response.status}: ${response.statusText}`
    );
  }

  return await response.json();
};