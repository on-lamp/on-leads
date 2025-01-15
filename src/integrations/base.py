from abc import ABC, abstractmethod
from typing import Dict, Any
from enum import Enum

class FieldType(Enum):
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    EMAIL = "email"
    URL = "url"
    MULTI_SELECT = "multi_select"
    TITLE = "title"

class DatabaseIntegration(ABC):
    def __init__(self):
        self.field_mappings: Dict[str, FieldType] = {}
    
    def configure_fields(self, mappings: Dict[str, FieldType]) -> None:
        """
        Configure field types for the integration.
        
        Args:
            mappings: Dictionary mapping field names to their types
        """
        self.field_mappings = mappings

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the service"""
        pass

    @abstractmethod
    async def insert_record(self, data: Dict[str, Any]) -> str:
        """Insert a single record into the database"""
        pass

    @abstractmethod
    def format_field(self, field_name: str, value: Any) -> Any:
        """
        Format a field value according to its type and the specific database requirements
        
        Args:
            field_name: Name of the field
            value: Value to format
            
        Returns:
            Formatted value according to the database requirements
        """
        pass