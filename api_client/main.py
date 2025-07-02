from api_client import PaginatedAPIClient

# Initialize the client
client = PaginatedAPIClient(
    base_url="https://rickandmortyapi.com",
    rate_limit_per_second=10.0
)

# Fetch paginated data
data = client.get_paginated_data(
    endpoint="/api/character",
)

# Save to JSON file
client.save_to_json(data, "output.json")