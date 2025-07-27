/**
 * Dashboard page with file upload and chat interface
 */
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, CheckCircle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Sidebar } from '../components/Sidebar';
import { ChatWindow } from '../components/ChatWindow';
import { FileDropzone } from '../components/FileDropzone';
import { uploadFiles } from '../utils/api';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';

export const Dashboard = ({ onBackToLanding }) => {
  const [selectedKB, setSelectedKB] = useState(null);
  const [showUpload, setShowUpload] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const queryClient = useQueryClient();

  const handleNewKB = () => {
    setShowUpload(true);
    setSelectedKB(null);
  };

  const handleFilesSelected = (files) => {
    setSelectedFiles(files);
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      toast.error('Please select files to upload');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      const result = await uploadFiles(selectedFiles, (progress) => {
        setUploadProgress(progress);
      });

      // Show success state
      setUploadSuccess(true);
      toast.success(result.message);

      // Refresh knowledge bases
      queryClient.invalidateQueries(['knowledgeBases']);

      // Auto-select the new knowledge base after a delay
      setTimeout(() => {
        setShowUpload(false);
        setUploadSuccess(false);
        setSelectedFiles([]);
        setUploadProgress(0);
        
        // Find and select the newly created KB
        queryClient.getQueryData(['knowledgeBases'])?.then?.(kbs => {
          const newKB = kbs?.find(kb => kb.kb_id === result.kb_id);
          if (newKB) {
            setSelectedKB(newKB);
          }
        });
      }, 2000);

    } catch (error) {
      console.error('Upload error:', error);
      toast.error(error.message || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleCancelUpload = () => {
    setShowUpload(false);
    setSelectedFiles([]);
    setUploadProgress(0);
    setUploadSuccess(false);
  };

  return (
    <div className="h-screen flex bg-background">
      {/* Sidebar */}
      <Sidebar
        selectedKB={selectedKB}
        onSelectKB={setSelectedKB}
        onNewKB={handleNewKB}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex-shrink-0 p-4 border-b bg-card"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={onBackToLanding}
                className="text-muted-foreground hover:text-foreground"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Home
              </Button>
              <div className="h-4 w-px bg-border" />
              <h1 className="text-xl font-semibold gradient-text">DocuChat</h1>
            </div>
          </div>
        </motion.div>

        {/* Content Area */}
        <div className="flex-1 relative">
          <AnimatePresence mode="wait">
            {showUpload ? (
              <motion.div
                key="upload"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.3 }}
                className="absolute inset-0 flex items-center justify-center p-8"
              >
                <Card className="w-full max-w-2xl p-8 space-y-6">
                  {uploadSuccess ? (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="text-center space-y-4"
                    >
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
                      >
                        <CheckCircle className="w-16 h-16 text-green-500 mx-auto" />
                      </motion.div>
                      <h3 className="text-xl font-semibold">Upload Successful!</h3>
                      <p className="text-muted-foreground">
                        Your documents have been processed and are ready for chat.
                      </p>
                    </motion.div>
                  ) : (
                    <>
                      <div className="text-center space-y-2">
                        <h2 className="text-2xl font-semibold">Create Knowledge Base</h2>
                        <p className="text-muted-foreground">
                          Upload your documents to create a new knowledge base
                        </p>
                      </div>

                      <FileDropzone
                        onFilesSelected={handleFilesSelected}
                        isUploading={isUploading}
                        uploadProgress={uploadProgress}
                      />

                      <div className="flex justify-end space-x-3">
                        <Button
                          variant="outline"
                          onClick={handleCancelUpload}
                          disabled={isUploading}
                        >
                          Cancel
                        </Button>
                        <Button
                          onClick={handleUpload}
                          disabled={selectedFiles.length === 0 || isUploading}
                          className="ripple"
                        >
                          {isUploading ? 'Uploading...' : 'Create Knowledge Base'}
                        </Button>
                      </div>
                    </>
                  )}
                </Card>
              </motion.div>
            ) : (
              <motion.div
                key="chat"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="h-full"
              >
                <ChatWindow knowledgeBase={selectedKB} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

