#!/usr/bin/env python3
"""
Paginated REST API Client with Error Handling, Retries, and Rate Limiting

This module provides a robust API client for retrieving paginated data from REST APIs
with built-in error handling, retry logic, and rate limiting capabilities.
"""

import json
import time
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


class RateLimiter:
    """Token bucket rate limiter implementation."""
    
    def __init__(self, calls_per_second: float = 10.0):
        """
        Initialize rate limiter.
        
        Args:
            calls_per_second: Maximum number of API calls allowed per second
        """
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call_time = 0.0
        
    def wait_if_needed(self):
        """Wait if necessary to respect rate limit."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        
        if time_since_last_call < self.min_interval:
            sleep_time = self.min_interval - time_since_last_call
            logging.debug(f"Rate limiting: sleeping for {sleep_time:.3f} seconds")
            time.sleep(sleep_time)
            
        self.last_call_time = time.time()


class PaginatedAPIClient:
    """A robust API client for retrieving paginated data from REST APIs."""
    
    def __init__(
        self,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
        auth: Optional[tuple] = None,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        rate_limit_per_second: float = 10.0,
        verify_ssl: bool = True
    ):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the API
            headers: Optional headers to include in requests
            auth: Optional authentication tuple (username, password)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for retries
            rate_limit_per_second: Maximum API calls per second
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip('/')
        self.headers = headers or {}
        self.auth = auth
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.rate_limiter = RateLimiter(rate_limit_per_second)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[408, 429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        if headers:
            self.session.headers.update(headers)
        if auth:
            self.session.auth = auth
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """
        Make an HTTP request with rate limiting.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (relative to base_url)
            params: Query parameters
            json_data: JSON data for POST/PUT requests
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: If request fails after all retries
        """
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()
        
        # Construct full URL
        url = urljoin(self.base_url, endpoint)
        
        try:
            self.logger.debug(f"Making {method} request to {url}")
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {str(e)}")
            raise
    
    def get_paginated_data(
        self,
        endpoint: str,
        page_size: int = 100,
        max_pages: Optional[int] = None,
        pagination_type: str = "offset",
        page_param: str = "page",
        size_param: str = "page_size",
        offset_param: str = "offset",
        data_key: Optional[str] = None,
        next_page_key: Optional[str] = "next",
        total_key: Optional[str] = "total",
        custom_params: Optional[Dict[str, Any]] = None,
        stop_condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
        start_page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all paginated data from an API endpoint.
        
        Args:
            endpoint: API endpoint to query
            page_size: Number of items per page
            max_pages: Maximum number of pages to retrieve (None for all)
            pagination_type: Type of pagination ("offset", "page", "cursor", "url")
            page_param: Parameter name for page number
            size_param: Parameter name for page size
            offset_param: Parameter name for offset
            data_key: Key in response containing the data array
            next_page_key: Key in response containing next page URL/cursor
            total_key: Key in response containing total item count
            custom_params: Additional parameters to include in requests
            stop_condition: Function to determine when to stop pagination
            start_page: Starting page number (default: 1)
            
        Returns:
            List of all retrieved data items
        """
        all_data = []
        page = start_page if pagination_type in ["page", "url"] else 0
        offset = 0
        cursor = None
        next_url = None
        total_items = None
        pages_retrieved = 0
        
        while True:
            # Build request parameters
            params = custom_params.copy() if custom_params else {}
            
            # Handle URL-based pagination
            if pagination_type == "url" and next_url:
                # Parse the next URL and extract endpoint and params
                parsed_url = urlparse(next_url)
                endpoint = parsed_url.path
                # Parse query parameters from the URL
                url_params = parse_qs(parsed_url.query)
                # Convert from lists to single values
                params = {k: v[0] if len(v) == 1 else v for k, v in url_params.items()}
                # Override with custom params if provided
                if custom_params:
                    params.update(custom_params)
            elif pagination_type == "page":
                params[page_param] = page
                params[size_param] = page_size
            elif pagination_type == "offset":
                params[offset_param] = offset
                params[size_param] = page_size
            elif pagination_type == "cursor" and cursor:
                params["cursor"] = cursor
                params[size_param] = page_size
            elif pagination_type == "cursor" and not cursor:
                # First request for cursor pagination
                params[size_param] = page_size
            elif pagination_type == "url":
                # First request for URL pagination
                params[page_param] = page
                params[size_param] = page_size
            
            try:
                # Make API request
                response = self._make_request("GET", endpoint, params=params)
                data = response.json()
                
                # Extract items from response
                if data_key:
                    items = data.get(data_key, [])
                elif isinstance(data, list):
                    items = data
                else:
                    # Try to find the data array in the response
                    items = self._find_data_array(data)
                
                if not items:
                    self.logger.info("No more items found, stopping pagination")
                    break
                
                # Add items to result
                all_data.extend(items)
                pages_retrieved += 1
                
                self.logger.info(
                    f"Retrieved page {pages_retrieved}: {len(items)} items "
                    f"(total: {len(all_data)})"
                )
                
                # Get total count if available
                if total_key and total_items is None:
                    total_items = data.get(total_key)
                    if total_items:
                        self.logger.info(f"Total items available: {total_items}")
                
                # Check stop conditions
                if max_pages and pages_retrieved >= max_pages:
                    self.logger.info(f"Reached maximum pages limit ({max_pages})")
                    break
                
                if stop_condition and stop_condition(data):
                    self.logger.info("Stop condition met")
                    break
                
                # Prepare for next iteration based on pagination type
                if pagination_type == "url":
                    # Check for next page URL in response
                    if next_page_key in data and data[next_page_key]:
                        next_url = data[next_page_key]
                        # Handle relative URLs
                        if not next_url.startswith(('http://', 'https://')):
                            next_url = urljoin(self.base_url, next_url)
                    else:
                        # If no next URL, try incrementing page number
                        if len(items) < page_size:
                            self.logger.info("Received partial page, assuming last page")
                            break
                        page += 1
                        
                elif pagination_type == "cursor":
                    # Check for next page cursor
                    if next_page_key in data and data[next_page_key]:
                        cursor = data[next_page_key]
                    else:
                        self.logger.info("No next cursor found, stopping")
                        break
                        
                elif pagination_type == "page":
                    # Check if we have more pages
                    if len(items) < page_size:
                        self.logger.info("Received partial page, assuming last page")
                        break
                    page += 1
                    
                elif pagination_type == "offset":
                    # Check if we have more items
                    if len(items) < page_size:
                        self.logger.info("Received partial page, assuming last page")
                        break
                    offset += len(items)
                    
                    # Check against total if known
                    if total_items and offset >= total_items:
                        self.logger.info("Retrieved all available items")
                        break
                
            except requests.RequestException as e:
                self.logger.error(f"Failed to retrieve page: {str(e)}")
                raise
            except (KeyError, ValueError) as e:
                self.logger.error(f"Failed to parse response: {str(e)}")
                raise
        
        self.logger.info(f"Pagination complete. Total items retrieved: {len(all_data)}")
        return all_data
    
    def _find_data_array(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Attempt to find the data array in a response dictionary.
        
        Args:
            response_data: Response data dictionary
            
        Returns:
            List of data items
        """
        # Common keys that might contain the data array
        common_keys = ['results', 'data', 'items', 'records', 'rows', 'entries']
        
        for key in common_keys:
            if key in response_data and isinstance(response_data[key], list):
                return response_data[key]
        
        # If not found, look for the first list value
        for value in response_data.values():
            if isinstance(value, list):
                return value
        
        # No list found
        return []
    
    def get_paginated_data_by_url(
        self,
        start_url: str,
        data_key: Optional[str] = None,
        next_page_key: Optional[str] = "next",
        max_pages: Optional[int] = None,
        stop_condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve paginated data by following URL links.
        
        This method is useful for APIs that provide complete URLs for pagination,
        such as: https://api.example.com/data?page=2&size=100
        
        Args:
            start_url: Initial URL to begin pagination
            data_key: Key in response containing the data array
            next_page_key: Key in response containing next page URL
            max_pages: Maximum number of pages to retrieve
            stop_condition: Function to determine when to stop
            
        Returns:
            List of all retrieved data items
        """
        all_data = []
        current_url = start_url
        pages_retrieved = 0
        
        while current_url and (max_pages is None or pages_retrieved < max_pages):
            try:
                # Parse URL to separate endpoint and parameters
                parsed = urlparse(current_url)
                
                # If it's a full URL, extract the path
                if parsed.netloc:
                    endpoint = parsed.path
                    # Parse query parameters
                    params = parse_qs(parsed.query)
                    # Convert lists to single values
                    params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}
                else:
                    # Relative URL
                    endpoint = current_url.split('?')[0]
                    if '?' in current_url:
                        params = parse_qs(current_url.split('?')[1])
                        params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}
                    else:
                        params = {}
                
                # Make request
                response = self._make_request("GET", endpoint, params=params)
                data = response.json()
                
                # Extract items
                if data_key:
                    items = data.get(data_key, [])
                elif isinstance(data, list):
                    items = data
                else:
                    items = self._find_data_array(data)
                
                if not items:
                    self.logger.info("No items found in response, stopping")
                    break
                
                all_data.extend(items)
                pages_retrieved += 1
                
                self.logger.info(
                    f"Retrieved page from {current_url}: {len(items)} items "
                    f"(total: {len(all_data)})"
                )
                
                # Check stop condition
                if stop_condition and stop_condition(data):
                    self.logger.info("Stop condition met")
                    break
                
                # Get next URL
                current_url = data.get(next_page_key)
                if current_url and not current_url.startswith(('http://', 'https://')):
                    # Handle relative URLs
                    current_url = urljoin(self.base_url, current_url)
                    
            except Exception as e:
                self.logger.error(f"Failed to retrieve page from {current_url}: {str(e)}")
                raise
        
        self.logger.info(f"URL pagination complete. Total items: {len(all_data)}")
        return all_data
    
    def save_to_json(self, data: List[Dict[str, Any]], filename: str):
        """
        Save data to a JSON file.
        
        Args:
            data: Data to save
            filename: Output filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Data saved to {filename}")
        except IOError as e:
            self.logger.error(f"Failed to save data: {str(e)}")
            raise


def main():
    """Example usage of the PaginatedAPIClient."""
    
    # Example 1: JSONPlaceholder API (offset-based pagination)
    print("Example 1: Fetching posts from JSONPlaceholder...")
    client = PaginatedAPIClient(
        base_url="https://jsonplaceholder.typicode.com",
        rate_limit_per_second=5.0
    )
    
    posts = client.get_paginated_data(
        endpoint="/posts",
        page_size=10,
        max_pages=3,
        pagination_type="offset",
        offset_param="_start",
        size_param="_limit"
    )
    
    client.save_to_json(posts, "posts.json")
    print(f"Retrieved {len(posts)} posts\n")
    
    # Example 2: Query string pagination (page=1, page=2, etc.)
    print("Example 2: Fetching data with query string pagination...")
    
    # Method 1: Using pagination_type="page"
    data = client.get_paginated_data(
        endpoint="/api/items",
        pagination_type="page",
        page_param="page",
        size_param="per_page",
        page_size=50,
        start_page=1  # Start from page 1
    )
    
    # Method 2: Using pagination_type="url" for APIs that return next URLs
    data = client.get_paginated_data(
        endpoint="/api/items",
        pagination_type="url",
        next_page_key="next_page_url",
        data_key="results"
    )
    
    # Method 3: Using the dedicated URL method
    data = client.get_paginated_data_by_url(
        start_url="https://api.example.com/data?page=1&size=100",
        data_key="items",
        next_page_key="next"
    )
    
    print(f"Retrieved {len(data)} items\n")
    
    # Example 3: GitHub API (page-based pagination with authentication)
    print("Example 3: Fetching GitHub repositories...")
    
    # Note: Replace with your GitHub token for authenticated requests
    github_token = "your_github_token_here"
    
    github_client = PaginatedAPIClient(
        base_url="https://api.github.com",
        headers={
            "Accept": "application/vnd.github.v3+json",
            # "Authorization": f"token {github_token}"  # Uncomment with valid token
        },
        rate_limit_per_second=1.0  # GitHub has strict rate limits
    )
    
    # Example: Get Python repositories
    repos = github_client.get_paginated_data(
        endpoint="/search/repositories",
        page_size=30,
        max_pages=2,
        pagination_type="page",
        data_key="items",
        custom_params={"q": "language:python stars:>1000", "sort": "stars"}
    )
    
    github_client.save_to_json(repos, "github_repos.json")
    print(f"Retrieved {len(repos)} repositories\n")
    
    # Example 4: Following pagination URLs directly
    print("Example 4: Following pagination URLs...")
    
    # For APIs that provide full URLs like:
    # Response: {"data": [...], "next": "https://api.example.com/items?page=2&size=100"}
    paginated_client = PaginatedAPIClient(
        base_url="https://api.example.com",
        rate_limit_per_second=10.0
    )
    
    # Start with the first page URL
    all_items = paginated_client.get_paginated_data_by_url(
        start_url="https://api.example.com/items?page=1&size=100",
        data_key="data",
        next_page_key="next",
        max_pages=10  # Limit to 10 pages
    )
    
    print(f"Retrieved {len(all_items)} total items")


if __name__ == "__main__":
    main()
