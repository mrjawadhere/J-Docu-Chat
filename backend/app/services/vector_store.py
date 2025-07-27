"""
Vector store service using Chroma for storing and retrieving document embeddings.
"""
import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document

from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing vector storage and retrieval using Chroma."""
    
    def __init__(self):
        """Initialize the vector store service."""
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_MODEL
        )
        
        # Ensure the persist directory exists
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        
        # Initialize Chroma client
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        logger.info(f"Vector store initialized with persist directory: {settings.CHROMA_PERSIST_DIR}")
    
    def create_knowledge_base(self, kb_id: str, documents: List[Document]) -> bool:
        """
        Create a new knowledge base with the given documents.
        
        Args:
            kb_id: Knowledge base identifier
            documents: List of documents to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not documents:
                logger.warning(f"No documents provided for knowledge base {kb_id}")
                return False
            
            # Create or get collection for this knowledge base
            collection_name = f"kb_{kb_id}"
            
            # Check if collection already exists
            try:
                existing_collection = self.client.get_collection(collection_name)
                logger.info(f"Collection {collection_name} already exists, adding documents")
            except Exception:
                # Collection doesn't exist, create it
                logger.info(f"Creating new collection: {collection_name}")
            
            # Create Langchain Chroma vector store
            vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                client=self.client,
                persist_directory=settings.CHROMA_PERSIST_DIR
            )
            
            # Add documents to the vector store
            vector_store.add_documents(documents)
            
            logger.info(f"Successfully added {len(documents)} documents to knowledge base {kb_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating knowledge base {kb_id}: {str(e)}")
            return False
    
    def add_documents_to_kb(self, kb_id: str, documents: List[Document]) -> bool:
        """
        Add documents to an existing knowledge base.
        
        Args:
            kb_id: Knowledge base identifier
            documents: List of documents to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not documents:
                logger.warning(f"No documents provided for knowledge base {kb_id}")
                return False
            
            collection_name = f"kb_{kb_id}"
            
            # Get existing vector store
            vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                client=self.client,
                persist_directory=settings.CHROMA_PERSIST_DIR
            )
            
            # Add new documents
            vector_store.add_documents(documents)
            
            logger.info(f"Successfully added {len(documents)} documents to existing knowledge base {kb_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents to knowledge base {kb_id}: {str(e)}")
            return False
    
    def search_knowledge_base(self, kb_id: str, query: str, k: int = 5) -> List[Document]:
        """
        Search for relevant documents in a knowledge base.
        
        Args:
            kb_id: Knowledge base identifier
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant documents
        """
        try:
            collection_name = f"kb_{kb_id}"
            
            # Get vector store for this knowledge base
            vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                client=self.client,
                persist_directory=settings.CHROMA_PERSIST_DIR
            )
            
            # Perform similarity search
            results = vector_store.similarity_search(query, k=k)
            
            logger.info(f"Found {len(results)} relevant documents for query in KB {kb_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching knowledge base {kb_id}: {str(e)}")
            return []
    
    def search_with_scores(self, kb_id: str, query: str, k: int = 5) -> List[tuple]:
        """
        Search for relevant documents with similarity scores.
        
        Args:
            kb_id: Knowledge base identifier
            query: Search query
            k: Number of results to return
            
        Returns:
            List of (document, score) tuples
        """
        try:
            collection_name = f"kb_{kb_id}"
            
            # Get vector store for this knowledge base
            vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                client=self.client,
                persist_directory=settings.CHROMA_PERSIST_DIR
            )
            
            # Perform similarity search with scores
            results = vector_store.similarity_search_with_score(query, k=k)
            
            logger.info(f"Found {len(results)} relevant documents with scores for query in KB {kb_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching knowledge base {kb_id} with scores: {str(e)}")
            return []
    
    def delete_knowledge_base(self, kb_id: str) -> bool:
        """
        Delete a knowledge base and all its documents.
        
        Args:
            kb_id: Knowledge base identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            collection_name = f"kb_{kb_id}"
            
            # Delete the collection
            self.client.delete_collection(collection_name)
            
            logger.info(f"Successfully deleted knowledge base {kb_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting knowledge base {kb_id}: {str(e)}")
            return False
    
    def get_knowledge_base_info(self, kb_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a knowledge base.
        
        Args:
            kb_id: Knowledge base identifier
            
        Returns:
            Dictionary with knowledge base information or None if not found
        """
        try:
            collection_name = f"kb_{kb_id}"
            
            # Get collection
            collection = self.client.get_collection(collection_name)
            
            # Get collection count
            count = collection.count()
            
            return {
                "kb_id": kb_id,
                "collection_name": collection_name,
                "document_count": count
            }
            
        except Exception as e:
            logger.error(f"Error getting info for knowledge base {kb_id}: {str(e)}")
            return None
    
    def list_knowledge_bases(self) -> List[str]:
        """
        List all available knowledge bases.
        
        Returns:
            List of knowledge base IDs
        """
        try:
            collections = self.client.list_collections()
            kb_ids = []
            
            for collection in collections:
                if collection.name.startswith("kb_"):
                    kb_id = collection.name[3:]  # Remove "kb_" prefix
                    kb_ids.append(kb_id)
            
            logger.info(f"Found {len(kb_ids)} knowledge bases")
            return kb_ids
            
        except Exception as e:
            logger.error(f"Error listing knowledge bases: {str(e)}")
            return []

