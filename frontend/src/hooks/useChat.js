/**
 * Custom hook for chat functionality
 */
import { useState, useCallback, useRef } from 'react';
import { sendChatMessage } from '../utils/api';
import { toast } from 'react-hot-toast';

export const useChat = (kbId) => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  const addMessage = useCallback((message) => {
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      ...message,
      timestamp: new Date()
    }]);
    setTimeout(scrollToBottom, 100);
  }, [scrollToBottom]);

  const sendMessage = useCallback(async (content, temperature = 0.7) => {
    if (!content.trim() || !kbId) return;

    // Add user message
    const userMessage = {
      content: content.trim(),
      role: 'user',
      sources: []
    };
    addMessage(userMessage);

    setIsLoading(true);
    setStreamingMessage('');

    try {
      let assistantContent = '';
      
      // Create assistant message placeholder
      const assistantMessageId = Date.now().toString() + '_assistant';
      
      await sendChatMessage(
        kbId,
        content,
        temperature,
        (chunk) => {
          assistantContent += chunk;
          setStreamingMessage(assistantContent);
        }
      );

      // Add final assistant message
      const assistantMessage = {
        id: assistantMessageId,
        content: assistantContent,
        role: 'assistant',
        sources: [], // Sources are included in the content
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
      setStreamingMessage('');
      
    } catch (error) {
      console.error('Chat error:', error);
      toast.error(error.message || 'Failed to send message');
      
      // Add error message
      const errorMessage = {
        content: 'Sorry, I encountered an error while processing your message. Please try again.',
        role: 'assistant',
        sources: [],
        isError: true
      };
      addMessage(errorMessage);
    } finally {
      setIsLoading(false);
      setTimeout(scrollToBottom, 100);
    }
  }, [kbId, addMessage, scrollToBottom]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setStreamingMessage('');
  }, []);

  return {
    messages,
    isLoading,
    streamingMessage,
    sendMessage,
    clearMessages,
    messagesEndRef,
    scrollToBottom
  };
};

