"""
API router for knowledge base management endpoints.
"""
import logging
from typing import List
from fastapi import APIRouter, HTTPException, status, Path
from fastapi.responses import JSONResponse

from app.models.schemas import (
    KnowledgeBase, 
    KnowledgeBaseList, 
    KnowledgeBaseUpdate,
    ErrorResponse
)
from app.services.kb_manager import KnowledgeBaseManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
kb_manager = KnowledgeBaseManager()


@router.get(
    "/kb",
    response_model=KnowledgeBaseList,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def list_knowledge_bases() -> KnowledgeBaseList:
    """
    List all knowledge bases.
    
    Returns:
        List of knowledge bases with metadata
    """
    try:
        logger.info("Listing all knowledge bases")
        
        kb_list = kb_manager.list_knowledge_bases()
        
        # Convert to response format
        knowledge_bases = []
        for kb_info in kb_list:
            knowledge_base = KnowledgeBase(
                kb_id=kb_info["kb_id"],
                name=kb_info.get("name", f"Knowledge Base {kb_info['kb_id'][:8]}"),
                created_at=kb_info.get("created_at", ""),
                file_count=kb_info.get("file_count", 0)
            )
            knowledge_bases.append(knowledge_base)
        
        logger.info(f"Found {len(knowledge_bases)} knowledge bases")
        
        return KnowledgeBaseList(knowledge_bases=knowledge_bases)
        
    except Exception as e:
        logger.error(f"Error listing knowledge bases: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list knowledge bases: {str(e)}"
        )


@router.get(
    "/kb/{kb_id}",
    response_model=KnowledgeBase,
    responses={
        404: {"model": ErrorResponse, "description": "Knowledge base not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_knowledge_base(
    kb_id: str = Path(..., description="Knowledge base ID")
) -> KnowledgeBase:
    """
    Get information about a specific knowledge base.
    
    Args:
        kb_id: Knowledge base identifier
        
    Returns:
        Knowledge base information
    """
    try:
        logger.info(f"Getting knowledge base info for {kb_id}")
        
        kb_info = kb_manager.get_knowledge_base(kb_id)
        
        if not kb_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base {kb_id} not found"
            )
        
        knowledge_base = KnowledgeBase(
            kb_id=kb_info["kb_id"],
            name=kb_info.get("name", f"Knowledge Base {kb_info['kb_id'][:8]}"),
            created_at=kb_info.get("created_at", ""),
            file_count=kb_info.get("file_count", 0)
        )
        
        logger.info(f"Retrieved knowledge base info for {kb_id}")
        
        return knowledge_base
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting knowledge base {kb_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get knowledge base: {str(e)}"
        )


@router.put(
    "/kb/{kb_id}",
    response_model=KnowledgeBase,
    responses={
        404: {"model": ErrorResponse, "description": "Knowledge base not found"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def update_knowledge_base(
    update_data: KnowledgeBaseUpdate,
    kb_id: str = Path(..., description="Knowledge base ID")
) -> KnowledgeBase:
    """
    Update knowledge base information (e.g., rename).
    
    Args:
        kb_id: Knowledge base identifier
        update_data: Update data
        
    Returns:
        Updated knowledge base information
    """
    try:
        logger.info(f"Updating knowledge base {kb_id}")
        
        # Check if knowledge base exists
        if not kb_manager.knowledge_base_exists(kb_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base {kb_id} not found"
            )
        
        # Update the knowledge base
        success = kb_manager.update_knowledge_base(
            kb_id=kb_id,
            name=update_data.name
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update knowledge base"
            )
        
        # Get updated info
        kb_info = kb_manager.get_knowledge_base(kb_id)
        
        knowledge_base = KnowledgeBase(
            kb_id=kb_info["kb_id"],
            name=kb_info.get("name", f"Knowledge Base {kb_info['kb_id'][:8]}"),
            created_at=kb_info.get("created_at", ""),
            file_count=kb_info.get("file_count", 0)
        )
        
        logger.info(f"Successfully updated knowledge base {kb_id}")
        
        return knowledge_base
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating knowledge base {kb_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update knowledge base: {str(e)}"
        )


@router.delete(
    "/kb/{kb_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse, "description": "Knowledge base not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def delete_knowledge_base(
    kb_id: str = Path(..., description="Knowledge base ID")
) -> None:
    """
    Delete a knowledge base and all its data.
    
    Args:
        kb_id: Knowledge base identifier
    """
    try:
        logger.info(f"Deleting knowledge base {kb_id}")
        
        # Check if knowledge base exists
        if not kb_manager.knowledge_base_exists(kb_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge base {kb_id} not found"
            )
        
        # Delete the knowledge base
        success = kb_manager.delete_knowledge_base(kb_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete knowledge base"
            )
        
        logger.info(f"Successfully deleted knowledge base {kb_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting knowledge base {kb_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete knowledge base: {str(e)}"
        )


@router.post(
    "/kb/cleanup",
    responses={
        200: {"description": "Cleanup completed"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def cleanup_orphaned_data() -> JSONResponse:
    """
    Clean up orphaned data (metadata without vector store or vice versa).
    
    Returns:
        Cleanup results
    """
    try:
        logger.info("Starting cleanup of orphaned data")
        
        cleanup_results = kb_manager.cleanup_orphaned_data()
        
        if "error" in cleanup_results:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Cleanup failed: {cleanup_results['error']}"
            )
        
        logger.info(f"Cleanup completed: {cleanup_results}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Cleanup completed successfully",
                "results": cleanup_results
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {str(e)}"
        )

