/**
 * Message bubble component for chat interface
 */
import React from 'react';
import { motion } from 'framer-motion';
import { User, Bot, Copy, Check } from 'lucide-react';
import { Button } from './ui/button';
import { useState } from 'react';
import { toast } from 'react-hot-toast';

export const MessageBubble = ({ message, isStreaming = false }) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';
  const isError = message.isError;

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      toast.success('Message copied to clipboard');
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast.error('Failed to copy message');
    }
  };

  const formatContent = (content) => {
    // Simple markdown-like formatting
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code class="bg-muted px-1 py-0.5 rounded text-sm">$1</code>')
      .replace(/\n/g, '<br />');
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={`flex gap-3 p-4 ${isUser ? 'flex-row-reverse' : 'flex-row'} message-bubble`}
    >
      {/* Avatar */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.1, type: 'spring', stiffness: 200 }}
        className={`
          flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
          ${isUser 
            ? 'bg-primary text-primary-foreground' 
            : isError 
              ? 'bg-destructive text-destructive-foreground'
              : 'bg-secondary text-secondary-foreground'
          }
        `}
      >
        {isUser ? (
          <User className="w-4 h-4" />
        ) : (
          <Bot className="w-4 h-4" />
        )}
      </motion.div>

      {/* Message Content */}
      <div className={`flex-1 max-w-[80%] ${isUser ? 'text-right' : 'text-left'}`}>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className={`
            inline-block p-3 rounded-lg relative group
            ${isUser 
              ? 'bg-primary text-primary-foreground ml-auto' 
              : isError
                ? 'bg-destructive/10 text-destructive border border-destructive/20'
                : 'bg-card text-card-foreground border'
            }
          `}
        >
          {/* Message Text */}
          <div 
            className={`text-sm leading-relaxed ${isStreaming ? 'typing-cursor' : ''}`}
            dangerouslySetInnerHTML={{ __html: formatContent(message.content) }}
          />

          {/* Streaming Indicator */}
          {isStreaming && (
            <motion.div
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="inline-block w-2 h-4 bg-current ml-1"
            />
          )}

          {/* Copy Button */}
          {!isStreaming && (
            <Button
              variant="ghost"
              size="sm"
              onClick={copyToClipboard}
              className={`
                absolute top-1 right-1 h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity
                ${isUser ? 'hover:bg-primary-foreground/20' : 'hover:bg-muted'}
              `}
            >
              {copied ? (
                <Check className="w-3 h-3" />
              ) : (
                <Copy className="w-3 h-3" />
              )}
            </Button>
          )}
        </motion.div>

        {/* Timestamp */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className={`text-xs text-muted-foreground mt-1 ${isUser ? 'text-right' : 'text-left'}`}
        >
          {message.timestamp?.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </motion.div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className={`mt-2 text-xs ${isUser ? 'text-right' : 'text-left'}`}
          >
            <div className="text-muted-foreground mb-1">Sources:</div>
            <div className="flex flex-wrap gap-1">
              {message.sources.map((source, index) => (
                <span
                  key={index}
                  className="inline-block px-2 py-1 bg-muted text-muted-foreground rounded text-xs"
                >
                  {source}
                </span>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

