# Paginated REST API Client Documentation

## Overview

This Python API client provides a robust solution for retrieving paginated data from REST APIs with built-in error handling, retry logic, and rate limiting capabilities. The client is designed to be flexible and can work with various pagination schemes commonly used by REST APIs.

## Architecture and Design Approach

### Core Components

1. **PaginatedAPIClient**: The main class that handles API interactions
2. **RateLimiter**: Token bucket implementation for rate limiting
3. **Session Management**: Uses requests.Session with retry adapters
4. **Logging**: Comprehensive logging for debugging and monitoring

### Key Design Decisions

- **Session-based requests**: Reuses TCP connections for better performance
- **Token bucket rate limiting**: Provides smooth, consistent rate limiting
- **Configurable retry strategy**: Uses exponential backoff for transient failures
- **Flexible pagination support**: Handles multiple pagination patterns
- **Type hints**: Improves code readability and IDE support

## Features

### 1. Pagination Support

The client supports four common pagination types:

- **Offset-based**: Uses offset and limit parameters
- **Page-based**: Uses page number and page size
- **Cursor-based**: Uses cursor/token for next page
- **URL-based**: Follows complete URLs with query strings (e.g., `?page=2`)

### 2. Error Handling

- **HTTP errors**: Automatically retries on server errors (5xx) and timeouts
- **Rate limiting**: Handles 429 (Too Many Requests) with backoff
- **Network issues**: Retries on connection errors
- **JSON parsing**: Graceful handling of malformed responses

### 3. Rate Limiting

- **Token bucket algorithm**: Ensures consistent request rate
- **Configurable**: Set requests per second based on API limits
- **Automatic throttling**: Prevents overwhelming the API

### 4. Retry Logic

- **Exponential backoff**: Increasing delays between retries
- **Configurable retries**: Set maximum retry attempts
- **Status-based**: Only retries on specific HTTP status codes

## Usage Examples

### Basic Usage

```python
from api_client import PaginatedAPIClient

# Initialize client
client = PaginatedAPIClient(
    base_url="https://api.example.com",
    rate_limit_per_second=10.0
)

# Fetch paginated data
data = client.get_paginated_data(
    endpoint="/users",
    page_size=100,
    pagination_type="offset"
)

# Save to JSON
client.save_to_json(data, "users.json")
```

### With Authentication

```python
# Bearer token authentication
client = PaginatedAPIClient(
    base_url="https://api.example.com",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

# Basic authentication
client = PaginatedAPIClient(
    base_url="https://api.example.com",
    auth=("username", "password")
)
```

### Custom Pagination Parameters

```python
# For APIs with non-standard parameter names
data = client.get_paginated_data(
    endpoint="/items",
    pagination_type="page",
    page_param="p",           # Instead of "page"
    size_param="per_page",    # Instead of "page_size"
    data_key="results"        # Where to find items in response
)
```

### Query String Pagination

```python
# Method 1: Using pagination_type="page" for ?page=1, ?page=2, etc.
data = client.get_paginated_data(
    endpoint="/api/users",
    pagination_type="page",
    page_param="page",
    size_param="limit",
    page_size=100,
    start_page=1  # Start from page 1
)

# Method 2: Following complete URLs from API responses
# For APIs that return: {"data": [...], "next": "https://api.com/users?page=2"}
data = client.get_paginated_data(
    endpoint="/api/users",
    pagination_type="url",
    next_page_key="next",
    data_key="data"
)

# Method 3: Using dedicated URL pagination method
data = client.get_paginated_data_by_url(
    start_url="https://api.example.com/users?page=1&limit=100",
    data_key="results",
    next_page_key="next_url",
    max_pages=10
)
```

### Stop Conditions

```python
# Stop when a certain condition is met
def should_stop(response_data):
    # Stop if we've reached items from last week
    last_item_date = response_data["items"][-1]["created_at"]
    return last_item_date < "2024-01-01"

data = client.get_paginated_data(
    endpoint="/events",
    stop_condition=should_stop
)
```

## Edge Cases Handled

### 1. Empty Responses
- Detects when no more data is available
- Handles both empty arrays and missing data keys
- Gracefully stops pagination

### 2. Partial Pages
- Recognizes when the last page has fewer items
- Prevents unnecessary additional requests
- Works with APIs that don't provide total counts

### 3. Rate Limit Headers
- Respects Retry-After headers
- Implements backoff strategies
- Prevents ban from aggressive requests

### 4. Connection Issues
- Retries on temporary network failures
- Configurable timeout prevents hanging
- Session reuse for connection pooling

### 5. Large Datasets
- Streams data instead of loading all at once
- Optional max_pages limit prevents runaway requests
- Memory-efficient processing

### 6. API Inconsistencies
- Flexible data extraction (tries common keys)
- Handles both array and object responses
- Robust error messages for debugging
- Supports various URL formats for pagination

### 7. SSL/TLS Issues
- Optional SSL verification for development
- Proper certificate handling
- Security warnings when verification disabled

### 8. Query String Pagination
- Parses page numbers from URLs
- Handles both relative and absolute URLs
- Supports custom query parameter names
- Automatically increments page numbers

## Enhancements and Optimizations

### 1. Performance Optimizations

- **Connection pooling**: Reuses HTTP connections
- **Parallel requests**: Could be extended for concurrent pagination
- **Caching**: Could add response caching for repeated requests
- **Compression**: Supports gzip/deflate automatically

### 2. Monitoring and Observability

- **Structured logging**: Easy to parse and analyze
- **Metrics**: Could add request count, latency tracking
- **Health checks**: Could add endpoint validation
- **Progress tracking**: Logs pagination progress

### 3. Advanced Features

- **Webhook support**: Could add callbacks for each page
- **Streaming**: Could yield items as they arrive
- **Resume capability**: Could save state for interruption recovery
- **Batch operations**: Could support bulk endpoints

### 4. Security Enhancements

- **Token refresh**: Could add OAuth token refresh logic
- **Request signing**: Could add HMAC request signing
- **Certificate pinning**: Could add for extra security
- **Secrets management**: Could integrate with key vaults

## Configuration Best Practices

### 1. Rate Limiting
```python
# Conservative for public APIs
client = PaginatedAPIClient(
    base_url="https://api.github.com",
    rate_limit_per_second=1.0  # GitHub allows 60/hour for unauthenticated
)

# Higher for private/internal APIs
client = PaginatedAPIClient(
    base_url="https://internal-api.company.com",
    rate_limit_per_second=100.0
)
```

### 2. Timeout Settings
```python
# Short timeout for fast APIs
client = PaginatedAPIClient(
    base_url="https://fast-api.com",
    timeout=5
)

# Longer timeout for slow/large responses
client = PaginatedAPIClient(
    base_url="https://reporting-api.com",
    timeout=60
)
```

### 3. Retry Configuration
```python
# Aggressive retries for critical data
client = PaginatedAPIClient(
    base_url="https://critical-api.com",
    max_retries=5,
    backoff_factor=2.0
)

# Minimal retries for optional data
client = PaginatedAPIClient(
    base_url="https://optional-api.com",
    max_retries=1,
    backoff_factor=0.5
)
```

## Real-World API Examples

### 1. RESTful API with Page Numbers
```python
# Many APIs use simple page numbers in query strings
client = PaginatedAPIClient(base_url="https://api.example.com")

# Fetch all users, starting from page 1
users = client.get_paginated_data(
    endpoint="/users",
    pagination_type="page",
    page_param="page",
    size_param="per_page",
    page_size=100,
    start_page=1
)
```

### 2. APIs with Next Page URLs
```python
# Some APIs return the complete URL for the next page
# Response format: {"items": [...], "next": "https://api.com/data?page=2&size=50"}

data = client.get_paginated_data_by_url(
    start_url="https://api.example.com/data?page=1&size=50",
    data_key="items",
    next_page_key="next"
)
```

### 3. Complex Query String Parameters
```python
# For APIs with multiple query parameters
client = PaginatedAPIClient(base_url="https://api.example.com")

data = client.get_paginated_data(
    endpoint="/search",
    pagination_type="page",
    custom_params={
        "q": "python",
        "sort": "relevance",
        "order": "desc",
        "category": "software"
    },
    page_param="p",
    size_param="count",
    start_page=0  # Some APIs start from page 0
)
```

### 4. Handling Different Response Formats
```python
# API returns: {"success": true, "data": {"users": [...], "pagination": {"next": "..."}}}

def extract_next_url(response_data):
    return response_data.get("data", {}).get("pagination", {}).get("next")

data = client.get_paginated_data(
    endpoint="/api/v2/users",
    pagination_type="url",
    data_key="data.users",  # Nested data key
    next_page_key="data.pagination.next"
)
```

## Error Handling Patterns

### 1. Graceful Degradation
```python
try:
    data = client.get_paginated_data(endpoint="/users")
except requests.RequestException as e:
    logger.error(f"Failed to fetch users: {e}")
    # Use cached data or defaults
    data = load_cached_users()
```

### 2. Partial Data Recovery
```python
all_data = []
for endpoint in endpoints:
    try:
        data = client.get_paginated_data(endpoint=endpoint)
        all_data.extend(data)
    except Exception as e:
        logger.warning(f"Skipping {endpoint}: {e}")
        continue
```

### 3. Circuit Breaker Pattern
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.is_open = False
        
    def call(self, func, *args, **kwargs):
        if self.is_open:
            raise Exception("Circuit breaker is open")
            
        try:
            result = func(*args, **kwargs)
            self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.is_open = True
            raise
```

## Testing Strategies

### 1. Unit Tests
- Mock requests.Session for isolated testing
- Test pagination logic with various response formats
- Verify rate limiting behavior
- Test error handling paths

### 2. Integration Tests
- Use mock servers (e.g., httpbin.org)
- Test against real APIs with test data
- Verify SSL/TLS handling
- Test timeout behavior

### 3. Load Testing
- Verify rate limiting under load
- Test connection pooling efficiency
- Monitor memory usage with large datasets
- Measure performance metrics

## Future Enhancements

1. **Async Support**: Add asyncio/aiohttp for concurrent requests
2. **GraphQL Support**: Extend to handle GraphQL pagination
3. **WebSocket Support**: For real-time data streams
4. **Data Transformation**: Add ETL pipeline capabilities
5. **Schema Validation**: Validate response data against schemas
6. **Distributed Tracing**: Add OpenTelemetry support
7. **Queue Integration**: Support for message queues
8. **Database Integration**: Direct database writes
9. **API Documentation**: Auto-generate from OpenAPI specs
10. **CLI Interface**: Command-line tool for ad-hoc queries

## Conclusion

This API client provides a solid foundation for interacting with paginated REST APIs. Its modular design allows for easy extension and customization while handling common edge cases and failure scenarios. The implementation prioritizes reliability, performance, and ease of use, making it suitable for both simple scripts and production applications.
