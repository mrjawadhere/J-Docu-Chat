"""
Chat service for handling RAG-based conversations with document knowledge bases.
"""
import logging
from typing import List, Dict, Any, AsyncGenerator
import json
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import LLMResult

from app.core.config import settings
from app.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)


class StreamingCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming responses."""
    
    def __init__(self):
        self.tokens = []
    
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Handle new token from LLM."""
        self.tokens.append(token)


class ChatService:
    """Service for handling chat interactions with document knowledge bases."""
    
    def __init__(self):
        """Initialize the chat service."""
        self.vector_store = VectorStoreService()
        self.llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model_name=settings.OPENAI_MODEL,
            streaming=True,
            temperature=0.7
        )
        
        # System prompt for RAG
        self.system_prompt = """You are a helpful AI assistant that answers questions based on the provided document context. 

Instructions:
1. Use the provided context to answer the user's question accurately and comprehensively.
2. If the context doesn't contain enough information to answer the question, say so clearly.
3. Always cite which documents or sources you're referencing when possible.
4. Provide detailed, well-structured responses when the context supports it.
5. If asked about something not in the context, politely explain that you can only answer based on the uploaded documents.

Context from documents:
{context}

Please answer the following question based on the above context."""
    
    def _format_context(self, documents: List[Any]) -> str:
        """
        Format retrieved documents into context string.
        
        Args:
            documents: List of retrieved documents
            
        Returns:
            Formatted context string
        """
        if not documents:
            return "No relevant documents found."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get('source', 'Unknown source')
            content = doc.page_content.strip()
            
            context_parts.append(f"Document {i} (Source: {source}):\n{content}")
        
        return "\n\n".join(context_parts)
    
    def _extract_sources(self, documents: List[Any]) -> List[str]:
        """
        Extract unique source filenames from documents.
        
        Args:
            documents: List of retrieved documents
            
        Returns:
            List of unique source filenames
        """
        sources = set()
        for doc in documents:
            source = doc.metadata.get('source', 'Unknown source')
            sources.add(source)
        
        return list(sources)
    
    async def chat_stream(
        self, 
        kb_id: str, 
        message: str, 
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response for a given message and knowledge base.
        
        Args:
            kb_id: Knowledge base identifier
            message: User message
            temperature: Model temperature
            
        Yields:
            Streaming response tokens
        """
        try:
            # Retrieve relevant documents
            logger.info(f"Searching for relevant documents in KB {kb_id} for query: {message[:100]}...")
            
            relevant_docs = self.vector_store.search_knowledge_base(
                kb_id=kb_id,
                query=message,
                k=5
            )
            
            if not relevant_docs:
                yield "I couldn't find any relevant information in the uploaded documents to answer your question. Please make sure you've uploaded documents related to your query."
                return
            
            # Format context
            context = self._format_context(relevant_docs)
            sources = self._extract_sources(relevant_docs)
            
            logger.info(f"Found {len(relevant_docs)} relevant documents from sources: {sources}")
            
            # Create messages
            system_message = SystemMessage(content=self.system_prompt.format(context=context))
            human_message = HumanMessage(content=message)
            
            # Update LLM temperature
            self.llm.temperature = temperature
            
            # Stream response
            callback_handler = StreamingCallbackHandler()
            
            # Use the streaming method
            async for chunk in self.llm.astream([system_message, human_message]):
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content
            
            # Send sources information at the end
            if sources:
                sources_text = f"\n\n**Sources:** {', '.join(sources)}"
                yield sources_text
                
        except Exception as e:
            error_msg = f"Error during chat: {str(e)}"
            logger.error(error_msg)
            yield f"I apologize, but I encountered an error while processing your request: {error_msg}"
    
    async def chat_complete(
        self, 
        kb_id: str, 
        message: str, 
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Get complete chat response (non-streaming) for a given message and knowledge base.
        
        Args:
            kb_id: Knowledge base identifier
            message: User message
            temperature: Model temperature
            
        Returns:
            Dictionary with response and sources
        """
        try:
            # Retrieve relevant documents
            logger.info(f"Searching for relevant documents in KB {kb_id} for query: {message[:100]}...")
            
            relevant_docs = self.vector_store.search_knowledge_base(
                kb_id=kb_id,
                query=message,
                k=5
            )
            
            if not relevant_docs:
                return {
                    "response": "I couldn't find any relevant information in the uploaded documents to answer your question. Please make sure you've uploaded documents related to your query.",
                    "sources": []
                }
            
            # Format context
            context = self._format_context(relevant_docs)
            sources = self._extract_sources(relevant_docs)
            
            logger.info(f"Found {len(relevant_docs)} relevant documents from sources: {sources}")
            
            # Create messages
            system_message = SystemMessage(content=self.system_prompt.format(context=context))
            human_message = HumanMessage(content=message)
            
            # Update LLM temperature
            self.llm.temperature = temperature
            
            # Get response
            response = await self.llm.apredict_messages([system_message, human_message])
            
            return {
                "response": response.content,
                "sources": sources
            }
                
        except Exception as e:
            error_msg = f"Error during chat: {str(e)}"
            logger.error(error_msg)
            return {
                "response": f"I apologize, but I encountered an error while processing your request: {error_msg}",
                "sources": []
            }

