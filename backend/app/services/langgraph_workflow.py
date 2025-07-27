"""
Document processing workflow for document processing pipeline.
"""
import logging
from typing import List, Dict, Any
from langchain.schema import Document

from app.services.document_processor import DocumentProcessor
from app.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)


class DocumentProcessingWorkflow:
    """Workflow for processing documents through the pipeline."""
    
    def __init__(self):
        """Initialize the workflow with required services."""
        self.document_processor = DocumentProcessor()
        self.vector_store = VectorStoreService()
    
    def process_documents(
        self, 
        kb_id: str, 
        file_paths: List[str], 
        file_names: List[str]
    ) -> Dict[str, Any]:
        """
        Process documents through the complete workflow.
        
        Args:
            kb_id: Knowledge base identifier
            file_paths: List of file paths to process
            file_names: List of original file names
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"Starting document processing workflow for KB {kb_id}")
        
        documents = []
        processed_files = []
        errors = []
        
        # Step 1: Load and parse documents
        logger.info(f"Loading documents for KB {kb_id}")
        
        for file_path, file_name in zip(file_paths, file_names):
            try:
                # Process the file
                file_documents = self.document_processor.process_file(file_path, file_name)
                
                if file_documents:
                    documents.extend(file_documents)
                    processed_files.append(file_name)
                    logger.info(f"Successfully loaded {len(file_documents)} chunks from {file_name}")
                else:
                    errors.append(f"No content extracted from {file_name}")
                    logger.warning(f"No content extracted from {file_name}")
                    
            except Exception as e:
                error_msg = f"Error processing {file_name}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        logger.info(f"Loaded {len(documents)} total document chunks from {len(processed_files)} files")
        
        # Step 2: Embed and store documents
        if not documents:
            logger.warning("No documents to embed and store")
            return {
                "kb_id": kb_id,
                "success": False,
                "processed_files": processed_files,
                "total_chunks": 0,
                "errors": errors + ["No documents available for embedding"]
            }
        
        logger.info(f"Embedding and storing documents for KB {kb_id}")
        
        try:
            # Check if knowledge base already exists
            existing_kb_info = self.vector_store.get_knowledge_base_info(kb_id)
            
            if existing_kb_info:
                # Add to existing knowledge base
                success = self.vector_store.add_documents_to_kb(kb_id, documents)
            else:
                # Create new knowledge base
                success = self.vector_store.create_knowledge_base(kb_id, documents)
            
            if success:
                logger.info(f"Successfully stored {len(documents)} documents in KB {kb_id}")
                
                return {
                    "kb_id": kb_id,
                    "success": True,
                    "processed_files": processed_files,
                    "total_chunks": len(documents),
                    "errors": errors
                }
            else:
                error_msg = f"Failed to store documents in vector database for KB {kb_id}"
                errors.append(error_msg)
                logger.error(error_msg)
                
        except Exception as e:
            error_msg = f"Error during embedding and storage: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
        
        return {
            "kb_id": kb_id,
            "success": False,
            "processed_files": processed_files,
            "total_chunks": len(documents),
            "errors": errors
        }

