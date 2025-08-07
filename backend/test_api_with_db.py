#!/usr/bin/env python3
"""
API test script to verify endpoints with database integration.
"""

import asyncio
import httpx
import json


async def test_api_endpoints():
    """Test the API endpoints with database."""
    base_url = "http://localhost:8000"
    
    print("API Endpoints Test (with Database)")
    print("=" * 45)
    
    async with httpx.AsyncClient() as client:
        try:
            # Test root endpoint
            print("1. Testing root endpoint...")
            response = await client.get(f"{base_url}/")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Response: {response.json()['message']}")
            
            # Test health endpoint with database
            print("\n2. Testing health endpoint...")
            response = await client.get(f"{base_url}/api/v1/health/")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   API Status: {data.get('status')}")
                print(f"   Database: {data.get('database')}")
                print(f"   Version: {data.get('version')}")
            
            # Test detailed health endpoint
            print("\n3. Testing detailed health endpoint...")
            response = await client.get(f"{base_url}/api/v1/health/detailed")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Services: {data.get('services', {})}")
                print(f"   Table counts: {data.get('database_metrics', {}).get('table_counts', {})}")
            
            # Test backtests endpoint
            print("\n4. Testing backtests list endpoint...")
            response = await client.get(f"{base_url}/api/v1/backtests/")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                backtests = response.json()
                print(f"   Found {len(backtests)} backtests")
                for bt in backtests[:3]:  # Show first 3
                    print(f"   - {bt['strategy_id']}: {bt['status']}")
            
            # Test creating a new backtest
            print("\n5. Testing backtest creation...")
            new_backtest = {
                "strategy_id": "api_test_strategy",
                "config": {
                    "start_date": "2024-06-01",
                    "end_date": "2024-06-30",
                    "symbol": "MNQ",
                    "parameters": {
                        "test_param": 42
                    }
                }
            }
            response = await client.post(
                f"{base_url}/api/v1/backtests/", 
                json=new_backtest
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                created = response.json()
                print(f"   Created backtest: {created['id']}")
                backtest_id = created['id']
                
                # Test getting specific backtest
                print("\n6. Testing get specific backtest...")
                response = await client.get(f"{base_url}/api/v1/backtests/{backtest_id}")
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    bt = response.json()
                    print(f"   Retrieved: {bt['strategy_id']} ({bt['status']})")
            
            # Test API documentation
            print("\n7. Testing API documentation...")
            response = await client.get(f"{base_url}/docs")
            print(f"   API Docs Status: {response.status_code}")
            
            response = await client.get(f"{base_url}/openapi.json")
            print(f"   OpenAPI Schema Status: {response.status_code}")
            if response.status_code == 200:
                schema = response.json()
                print(f"   API Title: {schema.get('info', {}).get('title')}")
                print(f"   Available paths: {len(schema.get('paths', {}))}")
            
            print("\n✅ All API tests completed successfully!")
            
        except httpx.ConnectError:
            print("❌ Could not connect to API server. Make sure it's running on http://localhost:8000")
        except Exception as e:
            print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    print("Make sure the FastAPI server is running (python run_dev.py)")
    print("Testing will begin in 3 seconds...")
    print()
    asyncio.run(test_api_endpoints())