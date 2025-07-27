/**
 * Type definitions for DocuChat application
 */

export const KnowledgeBase = {
  kb_id: '',
  name: '',
  created_at: '',
  file_count: 0
};

export const ChatMessage = {
  message: '',
  temperature: 0.7
};

export const ChatResponse = {
  response: '',
  sources: []
};

export const FileUploadResponse = {
  kb_id: '',
  file_names: [],
  message: ''
};

export const Message = {
  id: '',
  content: '',
  role: 'user', // 'user' | 'assistant'
  timestamp: new Date(),
  sources: []
};

export const UploadProgress = {
  fileName: '',
  progress: 0,
  status: 'uploading' // 'uploading' | 'processing' | 'completed' | 'error'
};

