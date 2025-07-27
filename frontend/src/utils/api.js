/**
 * API utility functions for DocuChat
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

/**
 * Upload files to create a new knowledge base
 */
export const uploadFiles = async (files, onProgress) => {
  const formData = new FormData();
  
  files.forEach((file) => {
    formData.append('files', file);
  });

  try {
    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });

    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Upload failed');
  }
};

/**
 * Get list of all knowledge bases
 */
export const getKnowledgeBases = async () => {
  try {
    const response = await api.get('/kb');
    return response.data.knowledge_bases;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to fetch knowledge bases');
  }
};

/**
 * Get specific knowledge base information
 */
export const getKnowledgeBase = async (kbId) => {
  try {
    const response = await api.get(`/kb/${kbId}`);
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to fetch knowledge base');
  }
};

/**
 * Update knowledge base (rename)
 */
export const updateKnowledgeBase = async (kbId, name) => {
  try {
    const response = await api.put(`/kb/${kbId}`, { name });
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to update knowledge base');
  }
};

/**
 * Delete knowledge base
 */
export const deleteKnowledgeBase = async (kbId) => {
  try {
    await api.delete(`/kb/${kbId}`);
    return true;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to delete knowledge base');
  }
};

/**
 * Send chat message and get streaming response
 */
export const sendChatMessage = async (kbId, message, temperature = 0.7, onChunk) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/${kbId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        temperature,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Chat request failed');
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Streaming not supported');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      
      // Keep the last incomplete line in buffer
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          
          if (data.trim() === '') continue;

          try {
            const parsed = JSON.parse(data);
            
            if (parsed.type === 'start') {
              // Chat started
              continue;
            } else if (parsed.type === 'end') {
              // Chat ended
              continue;
            } else if (parsed.type === 'error') {
              throw new Error(parsed.content);
            } else if (parsed.type === 'done') {
              // Stream complete
              return;
            } else if (parsed.content) {
              // Regular content chunk
              onChunk(parsed.content);
            }
          } catch (parseError) {
            console.warn('Failed to parse SSE data:', data);
          }
        }
      }
    }
  } catch (error) {
    throw new Error(error.message || 'Chat failed');
  }
};

/**
 * Send chat message and get complete response (non-streaming)
 */
export const sendChatMessageComplete = async (kbId, message, temperature = 0.7) => {
  try {
    const response = await api.post(`/chat/${kbId}/complete`, {
      message,
      temperature,
    });

    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Chat failed');
  }
};

/**
 * Health check
 */
export const healthCheck = async () => {
  try {
    const response = await api.get('/health');
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Health check failed');
  }
};

export default api;

