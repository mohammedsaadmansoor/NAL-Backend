"""
Utility functions for handling collection names and null checks.
"""
from src.utils.logging import get_logger

logger = get_logger(__name__)

def is_collection_name_valid(collection_name: str, collection_type: str = "collection") -> bool:
    """
    Check if a collection name is valid (not null, empty, or "null").
    
    Args:
        collection_name: The collection name to validate
        collection_type: The type of collection for logging purposes
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not collection_name or collection_name == "null":
        logger.warning(f"{collection_type} is null/empty: {collection_name}")
        return False
    return True

def get_safe_collection_name(collection_name: str, collection_type: str = "collection") -> str:
    """
    Get a safe collection name, returning empty string if invalid.
    
    Args:
        collection_name: The collection name to validate
        collection_type: The type of collection for logging purposes
        
    Returns:
        str: The collection name if valid, empty string otherwise
    """
    if is_collection_name_valid(collection_name, collection_type):
        return collection_name
    return ""

def log_collection_status(predefined: str = None, structured: str = None, unstructured: str = None, usecase_id: str = None):
    """
    Log the status of all collection names for a usecase.
    
    Args:
        predefined: Predefined collection name
        structured: Structured collection name  
        unstructured: Unstructured collection name
        usecase_id: The usecase ID for logging context
    """
    context = f"usecase_id: {usecase_id}" if usecase_id else ""
    
    if not is_collection_name_valid(predefined, "predefined_collection_name"):
        logger.warning(f"predefined_collection_name is null/empty for {context}")
    
    if not is_collection_name_valid(structured, "structured_collection_name"):
        logger.warning(f"structured_collection_name is null/empty for {context}")
        
    if not is_collection_name_valid(unstructured, "unstructured_collection_name"):
        logger.warning(f"unstructured_collection_name is null/empty for {context}")
