"""
Security utilities for the DocuChat application.
"""
import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, status


def validate_file_path(file_path: str, base_dir: str) -> bool:
    """
    Validate that a file path is within the allowed base directory.
    Prevents path traversal attacks.
    
    Args:
        file_path: The file path to validate
        base_dir: The base directory that files must be within
        
    Returns:
        True if the path is safe, False otherwise
    """
    try:
        # Resolve both paths to absolute paths
        abs_file_path = Path(file_path).resolve()
        abs_base_dir = Path(base_dir).resolve()
        
        # Check if the file path is within the base directory
        return abs_base_dir in abs_file_path.parents or abs_base_dir == abs_file_path
    except (OSError, ValueError):
        return False


def generate_kb_id() -> str:
    """Generate a unique knowledge base ID."""
    return str(uuid.uuid4())


def validate_file_extension(filename: str, allowed_extensions: list) -> bool:
    """
    Validate that a file has an allowed extension.
    
    Args:
        filename: The filename to check
        allowed_extensions: List of allowed file extensions (with dots)
        
    Returns:
        True if the extension is allowed, False otherwise
    """
    file_ext = Path(filename).suffix.lower()
    return file_ext in [ext.lower() for ext in allowed_extensions]


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing potentially dangerous characters.
    
    Args:
        filename: The original filename
        
    Returns:
        A sanitized filename
    """
    # Remove path separators and other dangerous characters
    dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
    sanitized = filename
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Limit filename length
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:255-len(ext)] + ext
    
    return sanitized


def create_secure_upload_path(upload_dir: str, kb_id: str, filename: str) -> str:
    """
    Create a secure upload path for a file.
    
    Args:
        upload_dir: Base upload directory
        kb_id: Knowledge base ID
        filename: Original filename
        
    Returns:
        Secure file path
    """
    sanitized_filename = sanitize_filename(filename)
    kb_dir = os.path.join(upload_dir, kb_id)
    
    # Create directory if it doesn't exist
    os.makedirs(kb_dir, exist_ok=True)
    
    return os.path.join(kb_dir, sanitized_filename)

