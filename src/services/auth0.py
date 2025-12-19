"""
Auth0 Management API Service

Handles user creation and soft-deletion in Auth0.
Uses machine-to-machine authentication with client credentials.
"""
import logging
import httpx
from typing import Optional
from datetime import datetime, timedelta

from src.core.config import config

logger = logging.getLogger(__name__)


class Auth0ManagementClient:
    """Client for Auth0 Management API operations."""
    
    def __init__(self):
        self.domain = config.AUTH0_DOMAIN
        self.client_id = config.AUTH0_CLIENT_ID
        self.client_secret = config.AUTH0_CLIENT_SECRET
        self.connection = config.AUTH0_CONNECTION
        self.base_url = f"https://{self.domain}/api/v2"
        self.token_url = f"https://{self.domain}/oauth/token"
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    async def _get_access_token(self) -> str:
        """
        Get a valid access token for the Management API.
        Caches the token and refreshes when expired.
        """
        # Check if we have a valid cached token
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at:
                return self._access_token
        
        # Request new token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                json={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "audience": f"https://{self.domain}/api/v2/",
                    "grant_type": "client_credentials"
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get Auth0 token: {response.text}")
                raise Exception(f"Failed to get Auth0 access token: {response.text}")
            
            data = response.json()
            self._access_token = data["access_token"]
            # Token typically expires in 86400 seconds (24 hours), refresh 5 mins early
            expires_in = data.get("expires_in", 86400)
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
            
            return self._access_token
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[dict] = None
    ) -> dict:
        """Make an authenticated request to the Auth0 Management API."""
        token = await self._get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=f"{self.base_url}{endpoint}",
                json=json_data,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code >= 400:
                logger.error(f"Auth0 API error: {response.status_code} - {response.text}")
                raise Exception(f"Auth0 API error: {response.text}")
            
            if response.status_code == 204:  # No content
                return {}
            
            return response.json()
    
    async def create_user(
        self,
        email: str,
        password: str,
        connection: Optional[str] = None
    ) -> dict:
        """
        Create a new user in Auth0.
        
        Args:
            email: User's email address
            password: User's password
            connection: Auth0 connection name (defaults to config value)
        
        Returns:
            dict: Created user data including user_id
        """
        payload = {
            "email": email,
            "password": password,
            "connection": connection or self.connection,
            "app_metadata": {
                "canLogin": True
            }
        }
        
        logger.info(f"Creating Auth0 user for email: {email}")
        result = await self._make_request("POST", "/users", payload)
        logger.info(f"Auth0 user created: {result.get('user_id')}")
        
        return result
    
    async def soft_delete_user(self, auth0_id: str) -> dict:
        """
        Soft delete a user in Auth0 by setting canLogin to false.
        This doesn't actually delete the user, just blocks login.
        
        Args:
            auth0_id: The Auth0 user ID (e.g., 'auth0|abc123')
        
        Returns:
            dict: Updated user data
        """
        payload = {
            "app_metadata": {
                "canLogin": False
            }
        }
        
        logger.info(f"Soft deleting Auth0 user: {auth0_id}")
        result = await self._make_request("PATCH", f"/users/{auth0_id}", payload)
        logger.info(f"Auth0 user soft deleted: {auth0_id}")
        
        return result
    
    async def restore_user(self, auth0_id: str) -> dict:
        """
        Restore a soft-deleted user by setting canLogin back to true.
        
        Args:
            auth0_id: The Auth0 user ID
        
        Returns:
            dict: Updated user data
        """
        payload = {
            "app_metadata": {
                "canLogin": True
            }
        }
        
        logger.info(f"Restoring Auth0 user: {auth0_id}")
        result = await self._make_request("PATCH", f"/users/{auth0_id}", payload)
        logger.info(f"Auth0 user restored: {auth0_id}")
        
        return result
    
    async def update_user(self, auth0_id: str, updates: dict) -> dict:
        """
        Update user metadata in Auth0.
        
        Args:
            auth0_id: The Auth0 user ID
            updates: Dictionary of fields to update (e.g., name, picture, etc.)
        
        Returns:
            dict: Updated user data
        """
        logger.info(f"Updating Auth0 user: {auth0_id}")
        result = await self._make_request("PATCH", f"/users/{auth0_id}", updates)
        return result
    
    async def get_user(self, auth0_id: str) -> dict:
        """
        Get user details from Auth0.
        
        Args:
            auth0_id: The Auth0 user ID
        
        Returns:
            dict: User data from Auth0
        """
        return await self._make_request("GET", f"/users/{auth0_id}")
    
    async def hard_delete_user(self, auth0_id: str) -> None:
        """
        Permanently delete a user from Auth0.
        Use with caution - this cannot be undone.
        
        Args:
            auth0_id: The Auth0 user ID
        """
        logger.warning(f"Hard deleting Auth0 user: {auth0_id}")
        await self._make_request("DELETE", f"/users/{auth0_id}")
        logger.info(f"Auth0 user permanently deleted: {auth0_id}")


# Global client instance
auth0_client = Auth0ManagementClient()

