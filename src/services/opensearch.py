"""
OpenSearch Service

Handles queries to OpenSearch for attendance logs.
Uses the SQL plugin for querying.
"""
import logging
import httpx
import base64
from typing import List, Dict, Any, Optional
from datetime import date, datetime

from src.core.config import config

logger = logging.getLogger(__name__)


class OpenSearchClient:
    """Client for OpenSearch SQL queries."""
    
    def __init__(self):
        self.base_url = config.OPENSEARCH_URL
        self.username = config.OPENSEARCH_USERNAME
        self.password = config.OPENSEARCH_PASSWORD
        self.verify_ssl = config.OPENSEARCH_VERIFY_SSL
        self.sql_endpoint = f"{self.base_url}/_plugins/_sql"
        
        # Build basic auth header
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.auth_header = f"Basic {encoded_credentials}"
    
    async def execute_sql(self, query: str) -> Dict[str, Any]:
        """
        Execute a SQL query against OpenSearch.
        
        Args:
            query: SQL query string
        
        Returns:
            dict: Query results with schema and datarows
        """
        async with httpx.AsyncClient(verify=self.verify_ssl) as client:
            response = await client.post(
                self.sql_endpoint,
                json={"query": query},
                headers={
                    "Content-Type": "application/json",
                    "Authorization": self.auth_header
                }
            )
            
            if response.status_code != 200:
                # Check if it's an index not found error - return empty results
                try:
                    error_body = response.json()
                    error_type = error_body.get("error", {}).get("type", "")
                    if error_type == "IndexNotFoundException" or response.status_code == 404:
                        logger.warning(f"OpenSearch index not found, returning empty results")
                        return {"schema": [], "datarows": []}
                except Exception:
                    pass
                
                logger.error(f"OpenSearch query failed: {response.text}")
                raise Exception(f"OpenSearch query failed: {response.text}")
            
            return response.json()
    
    def _parse_sql_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse OpenSearch SQL response into list of dictionaries.
        
        Args:
            response: Raw OpenSearch SQL response
        
        Returns:
            List of dictionaries with column names as keys
        """
        schema = response.get("schema", [])
        datarows = response.get("datarows", [])
        
        # Get column names from schema
        columns = [col["name"] for col in schema]
        
        # Convert datarows to list of dicts
        results = []
        for row in datarows:
            row_dict = dict(zip(columns, row))
            results.append(row_dict)
        
        return results
    
    async def get_attendance_logs(
        self,
        target_date: Optional[date] = None,
        card_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get attendance logs from OpenSearch.
        
        Args:
            target_date: Filter by date (defaults to today)
            card_ids: Optional list of card IDs to filter by
        
        Returns:
            List of attendance log records
        """
        if target_date is None:
            target_date = date.today()
        
        # Build the date filter for the target date
        date_str = target_date.strftime("%Y-%m-%d")
        
        # Build SQL query
        query = f"""
            SELECT card_id, event_type, timestamp 
            FROM attendances 
            WHERE timestamp >= '{date_str} 00:00:00' 
            AND timestamp < '{date_str} 23:59:59'
            ORDER BY timestamp ASC
        """
        
        logger.debug(f"Executing OpenSearch query: {query}")
        
        response = await self.execute_sql(query)
        return self._parse_sql_response(response)
    
    async def get_attendance_by_card_id(
        self,
        card_id: str,
        target_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get attendance logs for a specific card ID.
        
        Args:
            card_id: The RFID card ID
            target_date: Filter by date (defaults to today)
        
        Returns:
            List of attendance log records for the card
        """
        if target_date is None:
            target_date = date.today()
        
        date_str = target_date.strftime("%Y-%m-%d")
        
        query = f"""
            SELECT card_id, event_type, timestamp 
            FROM attendances 
            WHERE card_id = '{card_id}'
            AND timestamp >= '{date_str} 00:00:00' 
            AND timestamp < '{date_str} 23:59:59'
            ORDER BY timestamp ASC
        """
        
        response = await self.execute_sql(query)
        return self._parse_sql_response(response)

    async def get_attendance_logs_date_range(
        self,
        start_date: date,
        end_date: date,
        card_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get attendance logs from OpenSearch for a date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            card_ids: Optional list of card IDs to filter by
        
        Returns:
            List of attendance log records
        """
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        # Build SQL query for date range
        query = f"""
            SELECT card_id, event_type, timestamp 
            FROM attendances 
            WHERE timestamp >= '{start_str} 00:00:00' 
            AND timestamp <= '{end_str} 23:59:59'
            ORDER BY timestamp ASC
        """
        
        logger.debug(f"Executing OpenSearch date range query: {query}")
        
        response = await self.execute_sql(query)
        return self._parse_sql_response(response)


# Global client instance
opensearch_client = OpenSearchClient()

