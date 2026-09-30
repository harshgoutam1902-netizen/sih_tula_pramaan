/**
 * API client for TulaPramaan backend.
 * 
 * Uses axios for HTTP requests with automatic error handling.
 */

import axios, { AxiosError } from 'axios';
import type { ApiError } from '@/types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens
apiClient.interceptors.request.use(
  (config) => {
    // TODO: Add JWT token from auth store
    // const token = useAuthStore.getState().token;
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.detail || 'An error occurred';
      
      // Log error (could integrate with error tracking service)
      console.error('API Error:', {
        status: error.response.status,
        message,
        endpoint: error.config?.url,
      });
      
      // Handle specific status codes
      switch (error.response.status) {
        case 401:
          // Unauthorized - redirect to login
          // TODO: Integrate with auth system
          break;
        case 403:
          // Forbidden
          console.error('Access forbidden');
          break;
        case 404:
          // Not found
          console.error('Resource not found');
          break;
        case 500:
          // Server error
          console.error('Server error');
          break;
      }
    } else if (error.request) {
      // Request made but no response
      console.error('Network error: No response received');
    } else {
      // Request setup error
      console.error('Request error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
