"""User adapter for resolving auth service users and caching"""
from typing import Dict, List, Optional, Any
import asyncio
import time
import httpx
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class UserAdapter:
    """Handles user resolution from auth service with caching"""
    
    def __init__(
        self, 
        auth_service_url: str,
        cache_ttl_seconds: int = 300,  # 5 minutes
        batch_size: int = 50
    ):
        self.auth_service_url = auth_service_url.rstrip('/')
        self.cache_ttl = cache_ttl_seconds
        self.batch_size = batch_size
        self.cache = {}
        self.cache_timestamps = {}
        self.http_client = httpx.AsyncClient(timeout=10.0)
    
    async def resolve_user(self, auth_id: int) -> Optional[dict]:
        """Resolve single user from auth service"""
        users = await self.resolve_users([auth_id])
        return users.get(auth_id)
    
    async def resolve_users(self, auth_ids: List[int]) -> Dict[int, dict]:
        """Resolve multiple users from auth service with caching"""
        if not auth_ids:
            return {}
        
        # Remove duplicates while preserving order
        unique_ids = list(dict.fromkeys(auth_ids))
        
        # Check cache first
        cached_users = {}
        missing_ids = []
        
        current_time = time.time()
        
        for auth_id in unique_ids:
            if auth_id in self.cache:
                cache_age = current_time - self.cache_timestamps.get(auth_id, 0)
                if cache_age < self.cache_ttl:
                    cached_users[auth_id] = self.cache[auth_id]
                else:
                    # Cache expired
                    missing_ids.append(auth_id)
                    self._remove_from_cache(auth_id)
            else:
                missing_ids.append(auth_id)
        
        # Fetch missing users from auth service
        if missing_ids:
            try:
                fetched_users = await self._fetch_users_from_auth_service(missing_ids)
                
                # Update cache
                for auth_id, user_data in fetched_users.items():
                    self.cache[auth_id] = user_data
                    self.cache_timestamps[auth_id] = current_time
                
                # Merge with cached users
                cached_users.update(fetched_users)
                
            except Exception as e:
                logger.error(f"Failed to fetch users from auth service: {e}")
                # Return what we have from cache
        
        return cached_users
    
    async def _fetch_users_from_auth_service(self, auth_ids: List[int]) -> Dict[int, dict]:
        """Fetch users from auth service API"""
        users = {}
        
        # Process in batches to avoid overwhelming the auth service
        for i in range(0, len(auth_ids), self.batch_size):
            batch = auth_ids[i:i + self.batch_size]
            
            try:
                # Attempt batch endpoint first
                batch_users = await self._fetch_users_batch(batch)
                users.update(batch_users)
                
            except Exception as e:
                logger.warning(f"Batch fetch failed, falling back to individual requests: {e}")
                
                # Fallback to individual requests
                individual_users = await self._fetch_users_individually(batch)
                users.update(individual_users)
        
        return users
    
    async def _fetch_users_batch(self, auth_ids: List[int]) -> Dict[int, dict]:
        """Fetch users using batch endpoint"""
        url = f"{self.auth_service_url}/api/v1/users/batch"
        payload = {"user_ids": auth_ids}
        
        response = await self.http_client.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        # Transform response to our expected format
        users = {}
        for user_data in data.get("users", []):
            users[user_data["id"]] = self._transform_user_data(user_data)
        
        return users
    
    async def _fetch_users_individually(self, auth_ids: List[int]) -> Dict[int, dict]:
        """Fetch users individually (fallback method)"""
        users = {}
        
        # Create concurrent requests
        tasks = []
        for auth_id in auth_ids:
            task = self._fetch_single_user(auth_id)
            tasks.append(task)
        
        # Execute with some concurrency limit
        semaphore = asyncio.Semaphore(10)
        
        async def limited_fetch(task):
            async with semaphore:
                return await task
        
        results = await asyncio.gather(
            *[limited_fetch(task) for task in tasks],
            return_exceptions=True
        )
        
        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch user {auth_ids[i]}: {result}")
                continue
            
            if result:
                users[auth_ids[i]] = result
        
        return users
    
    async def _fetch_single_user(self, auth_id: int) -> Optional[dict]:
        """Fetch single user from auth service"""
        try:
            url = f"{self.auth_service_url}/api/v1/users/{auth_id}"
            response = await self.http_client.get(url)
            
            if response.status_code == 404:
                logger.warning(f"User {auth_id} not found in auth service")
                return None
            
            response.raise_for_status()
            user_data = response.json()
            
            return self._transform_user_data(user_data)
            
        except Exception as e:
            logger.error(f"Failed to fetch user {auth_id}: {e}")
            return None
    
    def _transform_user_data(self, user_data: dict) -> dict:
        """Transform auth service user data to our expected format"""
        return {
            "id": user_data["id"],
            "email": user_data.get("email"),
            "full_name": user_data.get("full_name"),
            "role": user_data.get("role"),
            "is_active": user_data.get("is_active", True),
            "last_login": user_data.get("last_login"),
        }
    
    async def enrich_with_users(self, data: dict, user_fields: List[str]) -> dict:
        """Enrich data dictionary with user information"""
        # Collect all auth IDs that need resolution
        auth_ids_to_resolve = set()
        
        for field in user_fields:
            if field in data and data[field] is not None:
                if isinstance(data[field], list):
                    auth_ids_to_resolve.update(data[field])
                else:
                    auth_ids_to_resolve.add(data[field])
        
        # Resolve users
        if auth_ids_to_resolve:
            users = await self.resolve_users(list(auth_ids_to_resolve))
            
            # Enrich the data
            enriched_data = data.copy()
            
            for field in user_fields:
                user_field = f"{field}_user"
                
                if field in data and data[field] is not None:
                    if isinstance(data[field], list):
                        # Handle list of user IDs
                        enriched_data[user_field] = [
                            users.get(auth_id) for auth_id in data[field]
                            if users.get(auth_id) is not None
                        ]
                    else:
                        # Handle single user ID
                        enriched_data[user_field] = users.get(data[field])
            
            return enriched_data
        
        return data
    
    async def get_users_by_role(self, role: str) -> List[dict]:
        """Get all users with a specific role"""
        try:
            url = f"{self.auth_service_url}/api/v1/users/by-role/{role}"
            response = await self.http_client.get(url)
            response.raise_for_status()
            
            data = response.json()
            return [self._transform_user_data(user) for user in data.get("users", [])]
            
        except Exception as e:
            logger.error(f"Failed to fetch users by role {role}: {e}")
            return []
    
    def _remove_from_cache(self, auth_id: int):
        """Remove user from cache"""
        self.cache.pop(auth_id, None)
        self.cache_timestamps.pop(auth_id, None)
    
    def clear_cache(self):
        """Clear all cached user data"""
        self.cache.clear()
        self.cache_timestamps.clear()
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        total_cached = len(self.cache)
        current_time = time.time()
        
        expired_count = sum(
            1 for timestamp in self.cache_timestamps.values()
            if current_time - timestamp >= self.cache_ttl
        )
        
        return {
            "total_cached": total_cached,
            "expired_entries": expired_count,
            "cache_hit_potential": total_cached - expired_count,
            "cache_ttl_seconds": self.cache_ttl
        }
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()