/**
 * Sidebar component for knowledge base management
 */
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Plus, 
  Trash2, 
  Edit3, 
  FileText, 
  Calendar,
  MoreVertical,
  Check,
  X
} from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card } from './ui/card';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from './ui/dropdown-menu';
import { Badge } from './ui/badge';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getKnowledgeBases, deleteKnowledgeBase, updateKnowledgeBase } from '../utils/api';
import { toast } from 'react-hot-toast';

export const Sidebar = ({ selectedKB, onSelectKB, onNewKB }) => {
  const [editingId, setEditingId] = useState(null);
  const [editingName, setEditingName] = useState('');
  const queryClient = useQueryClient();

  // Fetch knowledge bases
  const { data: knowledgeBases = [], isLoading, error } = useQuery({
    queryKey: ['knowledgeBases'],
    queryFn: getKnowledgeBases,
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: deleteKnowledgeBase,
    onSuccess: () => {
      queryClient.invalidateQueries(['knowledgeBases']);
      toast.success('Knowledge base deleted successfully');
      if (selectedKB && knowledgeBases.find(kb => kb.kb_id === selectedKB.kb_id)) {
        onSelectKB(null);
      }
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to delete knowledge base');
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ kbId, name }) => updateKnowledgeBase(kbId, name),
    onSuccess: () => {
      queryClient.invalidateQueries(['knowledgeBases']);
      toast.success('Knowledge base renamed successfully');
      setEditingId(null);
      setEditingName('');
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to rename knowledge base');
    },
  });

  const handleDelete = async (kbId) => {
    if (window.confirm('Are you sure you want to delete this knowledge base? This action cannot be undone.')) {
      deleteMutation.mutate(kbId);
    }
  };

  const startEditing = (kb) => {
    setEditingId(kb.kb_id);
    setEditingName(kb.name);
  };

  const saveEdit = () => {
    if (editingName.trim() && editingName !== knowledgeBases.find(kb => kb.kb_id === editingId)?.name) {
      updateMutation.mutate({ kbId: editingId, name: editingName.trim() });
    } else {
      setEditingId(null);
      setEditingName('');
    }
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditingName('');
  };

  const formatDate = (dateString) => {
    try {
      return new Date(dateString).toLocaleDateString([], {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return 'Unknown';
    }
  };

  if (error) {
    return (
      <div className="w-80 border-r bg-card p-4">
        <div className="text-center text-destructive">
          <p>Failed to load knowledge bases</p>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => queryClient.invalidateQueries(['knowledgeBases'])}
            className="mt-2"
          >
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ x: -300, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="w-80 border-r bg-card flex flex-col h-full"
    >
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Knowledge Bases</h2>
          <Button
            onClick={onNewKB}
            size="sm"
            className="ripple"
          >
            <Plus className="w-4 h-4 mr-2" />
            New
          </Button>
        </div>
        
        {knowledgeBases.length > 0 && (
          <div className="text-sm text-muted-foreground">
            {knowledgeBases.length} knowledge base{knowledgeBases.length !== 1 ? 's' : ''}
          </div>
        )}
      </div>

      {/* Knowledge Base List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {isLoading ? (
          // Loading skeleton
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse">
                <div className="h-20 bg-muted rounded-lg"></div>
              </div>
            ))}
          </div>
        ) : knowledgeBases.length === 0 ? (
          // Empty state
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-8"
          >
            <div className="text-4xl mb-4">📚</div>
            <h3 className="font-semibold mb-2">No Knowledge Bases</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Upload your first documents to get started
            </p>
            <Button onClick={onNewKB} size="sm">
              <Plus className="w-4 h-4 mr-2" />
              Create First KB
            </Button>
          </motion.div>
        ) : (
          // Knowledge base cards
          <AnimatePresence mode="popLayout">
            {knowledgeBases.map((kb, index) => (
              <motion.div
                key={kb.kb_id}
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -20, scale: 0.95 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ y: -2, boxShadow: "0 8px 24px rgba(0,0,0,.1)" }}
                whileTap={{ scale: 0.98 }}
              >
                <Card
                  className={`
                    p-3 cursor-pointer transition-all duration-200 border-2
                    ${selectedKB?.kb_id === kb.kb_id 
                      ? 'border-primary bg-primary/5' 
                      : 'border-transparent hover:border-border'
                    }
                  `}
                  onClick={() => onSelectKB(kb)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      {editingId === kb.kb_id ? (
                        <div className="flex items-center space-x-2 mb-2">
                          <Input
                            value={editingName}
                            onChange={(e) => setEditingName(e.target.value)}
                            onKeyPress={(e) => {
                              if (e.key === 'Enter') saveEdit();
                              if (e.key === 'Escape') cancelEdit();
                            }}
                            className="h-6 text-sm"
                            autoFocus
                            onClick={(e) => e.stopPropagation()}
                          />
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={(e) => {
                              e.stopPropagation();
                              saveEdit();
                            }}
                            className="h-6 w-6 p-0"
                          >
                            <Check className="w-3 h-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={(e) => {
                              e.stopPropagation();
                              cancelEdit();
                            }}
                            className="h-6 w-6 p-0"
                          >
                            <X className="w-3 h-3" />
                          </Button>
                        </div>
                      ) : (
                        <h3 className="font-medium text-sm mb-2 truncate">
                          {kb.name}
                        </h3>
                      )}
                      
                      <div className="flex items-center space-x-3 text-xs text-muted-foreground">
                        <div className="flex items-center space-x-1">
                          <FileText className="w-3 h-3" />
                          <span>{kb.file_count} files</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Calendar className="w-3 h-3" />
                          <span>{formatDate(kb.created_at)}</span>
                        </div>
                      </div>
                    </div>

                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <MoreVertical className="w-3 h-3" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={(e) => {
                            e.stopPropagation();
                            startEditing(kb);
                          }}
                        >
                          <Edit3 className="w-4 h-4 mr-2" />
                          Rename
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(kb.kb_id);
                          }}
                          className="text-destructive focus:text-destructive"
                        >
                          <Trash2 className="w-4 h-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>

                  {selectedKB?.kb_id === kb.kb_id && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="mt-2"
                    >
                      <Badge variant="secondary" className="text-xs">
                        Active
                      </Badge>
                    </motion.div>
                  )}
                </Card>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>
    </motion.div>
  );
};

