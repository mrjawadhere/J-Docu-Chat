"""
API router for chat endpoints with streaming support.
"""
import logging
import json
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException, status, Path, Depends
from fastapi.responses import StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.models.schemas import ChatMessage, ChatResponse, ErrorResponse
from app.services.chat_service import ChatService
from app.services.kb_manager import KnowledgeBaseManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
chat_service = ChatService()
kb_manager = KnowledgeBaseManager()

# Rate limiting
limiter = Limiter(key_func=get_remote_address)


async def verify_knowledge_base_exists(kb_id: str) -> None:
    """
    Verify that a knowledge base exists.
    
    Args:
        kb_id: Knowledge base identifier
        
    Raises:
        HTTPException: If knowledge base doesn't exist
    """
    if not kb_manager.knowledge_base_exists(kb_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base {kb_id} not found"
        )


async def format_sse_data(data: str) -> str:
    """
    Format data for Server-Sent Events.
    
    Args:
        data: Data to format
        
    Returns:
        Formatted SSE data
    """
    # Escape newlines and format for SSE
    escaped_data = data.replace('\n', '\\n').replace('\r', '\\r')
    return f"data: {json.dumps({'content': escaped_data})}\n\n"


async def stream_chat_response(
    kb_id: str, 
    message: str, 
    temperature: float
) -> AsyncGenerator[str, None]:
    """
    Stream chat response as Server-Sent Events.
    
    Args:
        kb_id: Knowledge base identifier
        message: User message
        temperature: Model temperature
        
    Yields:
        SSE formatted response chunks
    """
    try:
        # Send start event
        yield "data: {\"type\": \"start\"}\n\n"
        
        # Stream the actual response
        async for chunk in chat_service.chat_stream(kb_id, message, temperature):
            if chunk:
                yield await format_sse_data(chunk)
        
        # Send end event
        yield "data: {\"type\": \"end\"}\n\n"
        
    except Exception as e:
        logger.error(f"Error in streaming chat: {str(e)}")
        error_data = json.dumps({
            "type": "error",
            "content": f"Error: {str(e)}"
        })
        yield f"data: {error_data}\n\n"
    finally:
        # Send final event to close connection
        yield "data: {\"type\": \"done\"}\n\n"


@router.post(
    "/chat/{kb_id}",
    responses={
        200: {"description": "Streaming chat response"},
        404: {"model": ErrorResponse, "description": "Knowledge base not found"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def chat_with_knowledge_base(
    chat_message: ChatMessage,
    request,  # Required for rate limiting
    kb_id: str = Path(..., description="Knowledge base ID")
) -> StreamingResponse:
    """
    Chat with a knowledge base using streaming responses.
    
    Args:
        kb_id: Knowledge base identifier
        chat_message: Chat message with query and temperature
        request: FastAPI request object (for rate limiting)
        
    Returns:
        Streaming response with chat data
    """
    try:
        logger.info(f"Starting chat with KB {kb_id}: {chat_message.message[:100]}...")
        
        # Verify knowledge base exists
        await verify_knowledge_base_exists(kb_id)
        
        # Create streaming response
        return StreamingResponse(
            stream_chat_response(
                kb_id=kb_id,
                message=chat_message.message,
                temperature=chat_message.temperature
            ),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )


@router.post(
    "/chat/{kb_id}/complete",
    response_model=ChatResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Knowledge base not found"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def chat_complete(
    chat_message: ChatMessage,
    request,  # Required for rate limiting
    kb_id: str = Path(..., description="Knowledge base ID")
) -> ChatResponse:
    """
    Chat with a knowledge base and get complete response (non-streaming).
    
    Args:
        kb_id: Knowledge base identifier
        chat_message: Chat message with query and temperature
        request: FastAPI request object (for rate limiting)
        
    Returns:
        Complete chat response
    """
    try:
        logger.info(f"Starting complete chat with KB {kb_id}: {chat_message.message[:100]}...")
        
        # Verify knowledge base exists
        await verify_knowledge_base_exists(kb_id)
        
        # Get complete response
        result = await chat_service.chat_complete(
            kb_id=kb_id,
            message=chat_message.message,
            temperature=chat_message.temperature
        )
        
        return ChatResponse(
            response=result["response"],
            sources=result["sources"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in complete chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )


# Add rate limit exception handler
# router.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

