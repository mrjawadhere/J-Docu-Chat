/**
 * Chat window component with message list and input
 */
import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, RotateCcw, Settings } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Slider } from './ui/slider';
import { Label } from './ui/label';
import { Card } from './ui/card';
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover';
import { MessageBubble } from './MessageBubble';
import { useChat } from '../hooks/useChat';

export const ChatWindow = ({ knowledgeBase }) => {
  const [inputMessage, setInputMessage] = useState('');
  const [temperature, setTemperature] = useState([0.7]);
  const inputRef = useRef(null);
  
  const {
    messages,
    isLoading,
    streamingMessage,
    sendMessage,
    clearMessages,
    messagesEndRef,
    scrollToBottom
  } = useChat(knowledgeBase?.kb_id);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage, scrollToBottom]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const message = inputMessage.trim();
    setInputMessage('');
    
    await sendMessage(message, temperature[0]);
    
    // Focus back to input
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  if (!knowledgeBase) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="text-6xl">📚</div>
          <h3 className="text-xl font-semibold">Select a Knowledge Base</h3>
          <p className="text-muted-foreground">
            Choose a knowledge base from the sidebar to start chatting
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex-shrink-0 p-4 border-b bg-card"
      >
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">{knowledgeBase.name}</h2>
            <p className="text-sm text-muted-foreground">
              {knowledgeBase.file_count} files • Created {new Date(knowledgeBase.created_at).toLocaleDateString()}
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* Temperature Control */}
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" size="sm">
                  <Settings className="w-4 h-4 mr-2" />
                  Settings
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-80">
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="temperature">
                      Temperature: {temperature[0].toFixed(1)}
                    </Label>
                    <p className="text-xs text-muted-foreground mb-2">
                      Controls randomness. Lower = more focused, Higher = more creative
                    </p>
                    <Slider
                      id="temperature"
                      min={0}
                      max={2}
                      step={0.1}
                      value={temperature}
                      onValueChange={setTemperature}
                      className="w-full"
                    />
                  </div>
                </div>
              </PopoverContent>
            </Popover>

            {/* Clear Chat */}
            <Button
              variant="outline"
              size="sm"
              onClick={clearMessages}
              disabled={messages.length === 0 && !streamingMessage}
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              Clear
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence mode="popLayout">
          {messages.length === 0 && !streamingMessage && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="text-center py-12"
            >
              <div className="text-4xl mb-4">💬</div>
              <h3 className="text-lg font-semibold mb-2">Start a conversation</h3>
              <p className="text-muted-foreground max-w-md mx-auto">
                Ask questions about your uploaded documents. I'll search through them to provide accurate answers.
              </p>
            </motion.div>
          )}

          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}

          {/* Streaming Message */}
          {streamingMessage && (
            <MessageBubble
              message={{
                id: 'streaming',
                content: streamingMessage,
                role: 'assistant',
                timestamp: new Date(),
                sources: []
              }}
              isStreaming={true}
            />
          )}

          {/* Loading Indicator */}
          {isLoading && !streamingMessage && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex gap-3 p-4"
            >
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-secondary flex items-center justify-center">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  className="w-4 h-4 border-2 border-current border-t-transparent rounded-full"
                />
              </div>
              <div className="flex-1">
                <div className="bg-card border rounded-lg p-3">
                  <div className="flex space-x-1">
                    {[0, 1, 2].map((i) => (
                      <motion.div
                        key={i}
                        animate={{ opacity: [0.4, 1, 0.4] }}
                        transition={{
                          duration: 1.5,
                          repeat: Infinity,
                          delay: i * 0.2
                        }}
                        className="w-2 h-2 bg-current rounded-full"
                      />
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex-shrink-0 p-4 border-t bg-card"
      >
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <div className="flex-1 relative">
            <Input
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question about your documents..."
              disabled={isLoading}
              className="pr-12"
            />
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs text-muted-foreground">
              {inputMessage.length}/4000
            </div>
          </div>
          
          <Button
            type="submit"
            disabled={!inputMessage.trim() || isLoading}
            className="ripple"
          >
            <Send className="w-4 h-4" />
          </Button>
        </form>
        
        <div className="text-xs text-muted-foreground mt-2 text-center">
          Press Enter to send, Shift+Enter for new line
        </div>
      </motion.div>
    </div>
  );
};

