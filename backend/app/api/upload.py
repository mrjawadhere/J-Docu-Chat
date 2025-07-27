"""
API router for file upload endpoints.
"""
import os
import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.security import (
    generate_kb_id, 
    validate_file_extension, 
    create_secure_upload_path,
    validate_file_path
)
from app.models.schemas import FileUploadResponse, ErrorResponse
from app.services.langgraph_workflow import DocumentProcessingWorkflow
from app.services.kb_manager import KnowledgeBaseManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
workflow = DocumentProcessingWorkflow()
kb_manager = KnowledgeBaseManager()


async def validate_upload_files(files: List[UploadFile]) -> None:
    """
    Validate uploaded files.
    
    Args:
        files: List of uploaded files
        
    Raises:
        HTTPException: If validation fails
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )
    
    max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    
    for file in files:
        # Check file extension
        if not validate_file_extension(file.filename, settings.ALLOWED_EXTENSIONS):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not supported: {file.filename}. "
                       f"Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size (if available)
        if hasattr(file, 'size') and file.size and file.size > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File {file.filename} is too large. "
                       f"Maximum size: {settings.MAX_FILE_SIZE_MB}MB"
            )


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        413: {"model": ErrorResponse, "description": "File too large"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def upload_files(
    files: List[UploadFile] = File(..., description="Files to upload")
) -> FileUploadResponse:
    """
    Upload files and process them into a knowledge base.
    
    Args:
        files: List of files to upload
        
    Returns:
        Upload response with knowledge base ID and file names
    """
    try:
        # Validate files
        await validate_upload_files(files)
        
        # Generate knowledge base ID
        kb_id = generate_kb_id()
        
        logger.info(f"Starting file upload for KB {kb_id} with {len(files)} files")
        
        # Create upload directory
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        uploaded_files = []
        file_paths = []
        file_names = []
        
        # Save uploaded files
        for file in files:
            try:
                # Create secure file path
                file_path = create_secure_upload_path(
                    settings.UPLOAD_DIR, 
                    kb_id, 
                    file.filename
                )
                
                # Validate the path is secure
                if not validate_file_path(file_path, settings.UPLOAD_DIR):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid file path for {file.filename}"
                    )
                
                # Save file
                with open(file_path, "wb") as buffer:
                    content = await file.read()
                    
                    # Additional size check
                    if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File {file.filename} is too large"
                        )
                    
                    buffer.write(content)
                
                uploaded_files.append(file.filename)
                file_paths.append(file_path)
                file_names.append(file.filename)
                
                logger.info(f"Saved file: {file.filename} -> {file_path}")
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error saving file {file.filename}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error saving file {file.filename}: {str(e)}"
                )
        
        # Process documents through LangGraph workflow
        logger.info(f"Processing {len(file_paths)} files through workflow")
        
        try:
            workflow_results = workflow.process_documents(
                kb_id=kb_id,
                file_paths=file_paths,
                file_names=file_names
            )
            
            if not workflow_results["success"]:
                # Clean up uploaded files on workflow failure
                for file_path in file_paths:
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to cleanup file {file_path}: {cleanup_error}")
                
                error_details = "; ".join(workflow_results.get("errors", ["Unknown error"]))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Document processing failed: {error_details}"
                )
            
            # Create knowledge base metadata
            kb_name = f"Knowledge Base {kb_id[:8]}"  # Default name
            kb_manager.create_knowledge_base(
                kb_id=kb_id,
                name=kb_name,
                file_names=workflow_results["processed_files"]
            )
            
            logger.info(f"Successfully created knowledge base {kb_id} with {len(workflow_results['processed_files'])} files")
            
            return FileUploadResponse(
                kb_id=kb_id,
                file_names=workflow_results["processed_files"],
                message=f"Successfully uploaded and processed {len(workflow_results['processed_files'])} files"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in document processing workflow: {str(e)}")
            
            # Clean up uploaded files on error
            for file_path in file_paths:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup file {file_path}: {cleanup_error}")
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Document processing failed: {str(e)}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in file upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

