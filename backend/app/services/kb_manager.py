"""
Knowledge base manager for handling KB metadata and operations.
"""
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.core.config import settings
from app.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)


class KnowledgeBaseManager:
    """Manager for knowledge base metadata and operations."""
    
    def __init__(self):
        """Initialize the knowledge base manager."""
        self.vector_store = VectorStoreService()
        self.metadata_file = os.path.join(settings.UPLOAD_DIR, "kb_metadata.json")
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load knowledge base metadata from file."""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            return {}
    
    def _save_metadata(self) -> None:
        """Save knowledge base metadata to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.metadata_file), exist_ok=True)
            
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def create_knowledge_base(self, kb_id: str, name: str, file_names: List[str]) -> bool:
        """
        Create a new knowledge base entry in metadata.
        
        Args:
            kb_id: Knowledge base identifier
            name: Human-readable name for the KB
            file_names: List of uploaded file names
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.metadata[kb_id] = {
                "name": name,
                "created_at": datetime.utcnow().isoformat(),
                "file_names": file_names,
                "file_count": len(file_names)
            }
            
            self._save_metadata()
            logger.info(f"Created knowledge base metadata for {kb_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating knowledge base metadata: {e}")
            return False
    
    def update_knowledge_base(self, kb_id: str, name: Optional[str] = None, 
                            additional_files: Optional[List[str]] = None) -> bool:
        """
        Update knowledge base metadata.
        
        Args:
            kb_id: Knowledge base identifier
            name: New name for the KB (optional)
            additional_files: Additional files to add to the list (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if kb_id not in self.metadata:
                logger.error(f"Knowledge base {kb_id} not found in metadata")
                return False
            
            if name:
                self.metadata[kb_id]["name"] = name
            
            if additional_files:
                existing_files = self.metadata[kb_id].get("file_names", [])
                all_files = list(set(existing_files + additional_files))
                self.metadata[kb_id]["file_names"] = all_files
                self.metadata[kb_id]["file_count"] = len(all_files)
            
            self.metadata[kb_id]["updated_at"] = datetime.utcnow().isoformat()
            
            self._save_metadata()
            logger.info(f"Updated knowledge base metadata for {kb_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating knowledge base metadata: {e}")
            return False
    
    def delete_knowledge_base(self, kb_id: str) -> bool:
        """
        Delete a knowledge base and its metadata.
        
        Args:
            kb_id: Knowledge base identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete from vector store
            vector_success = self.vector_store.delete_knowledge_base(kb_id)
            
            # Delete metadata
            if kb_id in self.metadata:
                del self.metadata[kb_id]
                self._save_metadata()
            
            # Delete uploaded files
            kb_upload_dir = os.path.join(settings.UPLOAD_DIR, kb_id)
            if os.path.exists(kb_upload_dir):
                import shutil
                shutil.rmtree(kb_upload_dir)
                logger.info(f"Deleted upload directory for KB {kb_id}")
            
            logger.info(f"Deleted knowledge base {kb_id}")
            return vector_success
            
        except Exception as e:
            logger.error(f"Error deleting knowledge base {kb_id}: {e}")
            return False
    
    def get_knowledge_base(self, kb_id: str) -> Optional[Dict[str, Any]]:
        """
        Get knowledge base information.
        
        Args:
            kb_id: Knowledge base identifier
            
        Returns:
            Knowledge base information or None if not found
        """
        if kb_id in self.metadata:
            kb_info = self.metadata[kb_id].copy()
            kb_info["kb_id"] = kb_id
            
            # Get additional info from vector store
            vector_info = self.vector_store.get_knowledge_base_info(kb_id)
            if vector_info:
                kb_info["document_count"] = vector_info.get("document_count", 0)
            
            return kb_info
        
        return None
    
    def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        """
        List all knowledge bases.
        
        Returns:
            List of knowledge base information
        """
        kb_list = []
        
        for kb_id, metadata in self.metadata.items():
            kb_info = metadata.copy()
            kb_info["kb_id"] = kb_id
            
            # Get additional info from vector store
            vector_info = self.vector_store.get_knowledge_base_info(kb_id)
            if vector_info:
                kb_info["document_count"] = vector_info.get("document_count", 0)
            else:
                kb_info["document_count"] = 0
            
            kb_list.append(kb_info)
        
        # Sort by creation date (newest first)
        kb_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return kb_list
    
    def knowledge_base_exists(self, kb_id: str) -> bool:
        """
        Check if a knowledge base exists.
        
        Args:
            kb_id: Knowledge base identifier
            
        Returns:
            True if exists, False otherwise
        """
        return kb_id in self.metadata
    
    def get_knowledge_base_files(self, kb_id: str) -> List[str]:
        """
        Get list of files in a knowledge base.
        
        Args:
            kb_id: Knowledge base identifier
            
        Returns:
            List of file names
        """
        if kb_id in self.metadata:
            return self.metadata[kb_id].get("file_names", [])
        return []
    
    def cleanup_orphaned_data(self) -> Dict[str, Any]:
        """
        Clean up orphaned data (metadata without vector store or vice versa).
        
        Returns:
            Dictionary with cleanup results
        """
        try:
            # Get KB IDs from vector store
            vector_kb_ids = set(self.vector_store.list_knowledge_bases())
            
            # Get KB IDs from metadata
            metadata_kb_ids = set(self.metadata.keys())
            
            # Find orphaned entries
            orphaned_metadata = metadata_kb_ids - vector_kb_ids
            orphaned_vectors = vector_kb_ids - metadata_kb_ids
            
            cleanup_results = {
                "orphaned_metadata": list(orphaned_metadata),
                "orphaned_vectors": list(orphaned_vectors),
                "cleaned_metadata": [],
                "cleaned_vectors": []
            }
            
            # Clean up orphaned metadata
            for kb_id in orphaned_metadata:
                if kb_id in self.metadata:
                    del self.metadata[kb_id]
                    cleanup_results["cleaned_metadata"].append(kb_id)
            
            # Clean up orphaned vector stores
            for kb_id in orphaned_vectors:
                if self.vector_store.delete_knowledge_base(kb_id):
                    cleanup_results["cleaned_vectors"].append(kb_id)
            
            # Save updated metadata
            if cleanup_results["cleaned_metadata"]:
                self._save_metadata()
            
            logger.info(f"Cleanup completed: {cleanup_results}")
            return cleanup_results
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {"error": str(e)}

