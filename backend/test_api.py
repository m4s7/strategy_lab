#!/usr/bin/env python3
"""
Simple test script to verify FastAPI endpoints are working.
"""

import asyncio
import httpx


async def test_endpoints():
    """Test the main API endpoints."""
    base_url = "http://localhost:8000"

    async with httpx.AsyncClient() as client:
        try:
            # Test root endpoint
            print("Testing root endpoint...")
            response = await client.get(f"{base_url}/")
            print(f"Root endpoint: {response.status_code} - {response.json()}")

            # Test health endpoint
            print("\nTesting health endpoint...")
            response = await client.get(f"{base_url}/health")
            print(f"Health endpoint: {response.status_code} - {response.json()}")

            # Test detailed health endpoint
            print("\nTesting detailed health endpoint...")
            response = await client.get(f"{base_url}/api/v1/health/")
            print(f"API Health endpoint: {response.status_code}")
            data = response.json()
            print(f"Status: {data.get('status')}")
            print(f"Version: {data.get('version')}")
            print(f"Environment: {data.get('environment')}")

            # Test API documentation
            print("\nTesting API documentation...")
            response = await client.get(f"{base_url}/docs")
            print(f"API Docs: {response.status_code}")

        except Exception as e:
            print(f"Error testing endpoints: {e}")


if __name__ == "__main__":
    print("FastAPI Backend Test")
    print("=" * 30)
    asyncio.run(test_endpoints())
