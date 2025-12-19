import os
from supabase import create_client, Client
from src.core.config import config


def get_supabase_client() -> Client:
    """
    Initialize and return a Supabase client using environment variables.
    """
    url: str = config.SUPABASE_URL
    key: str = config.SUPABASE_KEY
    supabase: Client = create_client(url, key)
    return supabase


# Global client instance (optional, for reuse)
supabase_client = get_supabase_client()