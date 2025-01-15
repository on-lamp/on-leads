from typing import Dict, Any, List, Optional, Union, TypeVar, Generic
import os
import logging
from notion_client import AsyncClient
from notion_client.errors import APIResponseError

from src.constants.schemas import DATABASE_SCHEMAS, get_backend_schema


from ..types.database import BackendType, DatabaseType, LeadRecord, EmailRecord
from ..types.filters import FilterType, FieldFilter, CompositeFilter
from .base import DatabaseIntegration

logger = logging.getLogger(__name__)

T = TypeVar('T', LeadRecord, EmailRecord)

class NotionIntegration(DatabaseIntegration, Generic[T]):
    """
    Notion database integration class that handles CRUD operations with Notion API.
    """
    
    def __init__(self, database_type: DatabaseType):
        super().__init__()
        db_env_name = f'NOTION_{database_type.value.upper()}_DATABASE_ID'
        self.database_id = os.getenv(db_env_name)
        if not self.database_id:
            raise ValueError(f"{db_env_name} environment variable is required")
        self.client: Optional[AsyncClient] = None
        self.schema = DATABASE_SCHEMAS[database_type]
        self.notion_mappings = get_backend_schema(database_type, BackendType.NOTION)

    async def connect(self) -> None:
        """
        Establishes connection to Notion API using environment token.
        
        Raises:
            ValueError: If NOTION_TOKEN environment variable is not set
            APIResponseError: If connection fails
        """
        token = os.getenv('NOTION_TOKEN')
        if not token:
            raise ValueError("NOTION_TOKEN environment variable is required")
        try:
            self.client = AsyncClient(auth=token)
            # Test connection
            await self.client.databases.retrieve(database_id=self.database_id)
            logger.info("Successfully connected to Notion API")
        except APIResponseError as e:
            logger.error(f"Failed to connect to Notion API: {str(e)}")
            raise

    async def insert_record(self, data: T) -> str:
        """
        Insert a single record into Notion database.
        
        Args:
            data: Dictionary containing the record data
            
        Returns:
            str: ID of the created page
            
        Raises:
            APIResponseError: If the API request fails
        """
        if not self.client:
            await self.connect()
        
        try:
            properties = self._format_properties(data)
            response = await self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            logger.info(f"Successfully created page with ID: {response['id']}")
            return response["id"]
        except APIResponseError as e:
            logger.error(f"Failed to insert record: {str(e)}")
            raise

    async def update_record(self, page_id: str, data: T) -> None:
        """
        Update an existing record in Notion database.
        
        Args:
            page_id: ID of the page to update
            data: Dictionary containing the updated data
            
        Raises:
            APIResponseError: If the API request fails
        """
        if not self.client:
            await self.connect()
            
        try:
            properties = self._format_properties(data)
            await self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
            logger.info(f"Successfully updated page: {page_id}")
        except APIResponseError as e:
            logger.error(f"Failed to update record: {str(e)}")
            raise

    async def delete_record(self, page_id: str) -> None:
        """
        Archive a record in Notion database (Notion doesn't support true deletion).
        
        Args:
            page_id: ID of the page to archive
            
        Raises:
            APIResponseError: If the API request fails
        """
        if not self.client:
            await self.connect()
            
        try:
            await self.client.pages.update(
                page_id=page_id,
                archived=True
            )
            logger.info(f"Successfully archived page: {page_id}")
        except APIResponseError as e:
            logger.error(f"Failed to archive record: {str(e)}")
            raise

    def _convert_filter(self, filter_: FilterType) -> Dict[str, Any]:
        """Convert abstract filter to Notion format."""
        if isinstance(filter_, FieldFilter):
            field_type = self.notion_mappings.get(filter_.field)
            if not field_type:
                raise ValueError(f"Unknown field: {filter_.field}")

            return {
                "property": filter_.field,
                field_type: {
                    filter_.operator.value: filter_.value
                }
            }
        elif isinstance(filter_, CompositeFilter):
            return {
                filter_.operator.value: [
                    self._convert_filter(f) for f in filter_.filters
                ]
            }
        raise ValueError(f"Invalid filter type: {type(filter_)}")

    async def get_records(
        self,
        filter_params: Optional[FilterType] = None,
        sort_params: Optional[List[Dict[str, Any]]] = None
    ) -> List[T]:
        if not self.client:
            await self.connect()
        
        try:
            query_params = {"database_id": self.database_id}
            if filter_params:
                query_params["filter"] = self._convert_filter(filter_params)
            if sort_params:
                query_params["sorts"] = sort_params

            response = await self.client.databases.query(**query_params)
            
            records = []
            for page in response["results"]:
                record = {
                    key: self._parse_property(prop)
                    for key, prop in page["properties"].items()
                }
                record["id"] = page["id"]
                records.append(record)
            
            return records
            
        except APIResponseError as e:
            logger.error(f"Failed to fetch records: {str(e)}")
            raise

    def format_field(self, field_name: str, value: Any) -> Dict[str, Any]:
        """
        Format a field value according to its type for Notion API.
        
        Args:
            field_name: Name of the field
            value: Value to format
            
        Returns:
            Formatted value according to Notion API requirements
        """
        # Handle None or empty string values
        if value is None or value == "":
            return {"url": None} if self.notion_mappings.get(field_name) == "url" else None
            
        field_schema = self.schema.get(field_name)
        if not field_schema:
            return None
            
        notion_type = self.notion_mappings[field_name]
        
        if notion_type == "title":
            return {"title": [{"text": {"content": str(value)}}]} if value else None
        elif notion_type == "email":
            return {"email": value if value else None}
        elif notion_type == "rich_text":
            return {"rich_text": [{"text": {"content": str(value)}}]} if value else None
        elif notion_type == "select":
            return {"select": {"name": str(value)}} if value else None
        elif notion_type == "url":
            return {"url": str(value) if value else None}
        elif notion_type == "relation":
            if not value:
                return {"relation": []}
            if isinstance(value, list):
                return {"relation": value}
            return {"relation": [{"id": str(value)}]}
        elif notion_type == "number":
            return {"number": int(value)} if value else None
            
        logger.warning(f"Unsupported type {field_schema.field_type} for field {field_name}")
        return None

    def _format_properties(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert raw data to Notion property format.
        
        Args:
            data: Dictionary containing the raw data
            
        Returns:
            Dictionary formatted for Notion API
        """
        return {
            key: self.format_field(key, value)
            for key, value in data.items()
            if self.format_field(key, value) is not None
        }

    def _parse_property(self, prop: Dict[str, Any]) -> Any:
        """
        Parse a Notion property into a Python native type.
        """
        if "title" in prop:
            return prop["title"][0]["text"]["content"] if prop["title"] else None
        elif "rich_text" in prop:
            return prop["rich_text"][0]["text"]["content"] if prop["rich_text"] else ""
        elif "select" in prop:
            return prop["select"]["name"] if prop["select"] else None
        elif "email" in prop:
            return prop["email"]
        elif "url" in prop:
            return prop["url"]
        elif "relation" in prop:
            return [{"id": item["id"]} for item in prop["relation"]]
        elif "unique_id" in prop:
            return prop["unique_id"]["number"] if prop["unique_id"] else None
        return None
