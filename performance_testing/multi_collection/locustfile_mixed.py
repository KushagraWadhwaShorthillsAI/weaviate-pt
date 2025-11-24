"""
Locust performance testing for Weaviate - Mixed Search Types
Tests realistic workload with BM25, Hybrid 0.1, Hybrid 0.9, and Vector.

Usage:
    locust -f locustfile_mixed.py --users 100 --spawn-rate 5 --run-time 5m --headless
"""


import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import json
import random
from locust import HttpUser, task, between, events
import config


QUERIES_MIXED = []


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Load Mixed query file when Locust starts"""
    global QUERIES_MIXED
    
    print("=" * 70)
    print("Loading Mixed query file...")
    print("=" * 70)
    
    try:
        with open("queries/queries_mixed_200.json", "r") as f:
            QUERIES_MIXED = json.load(f)
        print(f"✓ Loaded query file: {len(QUERIES_MIXED)} queries")
        print(f"  Search types: 10 BM25 + 10 Hybrid 0.1 + 10 Hybrid 0.9 + 10 Vector")
        print(f"  Each query searches 9 collections")
        print(f"  Returns 200 results per collection")
        print("=" * 70)
    except Exception as e:
        print(f"❌ Failed to load queries_mixed.json: {e}")
        print("   Run: python ../generate_all_queries.py --type multi --search-types mixed")
        print("=" * 70)


class WeaviateMixedUser(HttpUser):
    """Simulates a user performing mixed search types"""
    
    # wait_time = between(1, 3)  # Removed for max throughput
    host = config.WEAVIATE_URL
    
    def on_start(self):
        """Setup headers"""
        self.headers = {"Content-Type": "application/json"}
        if config.WEAVIATE_API_KEY and config.WEAVIATE_API_KEY != "your-weaviate-api-key":
            self.headers["Authorization"] = f"Bearer {config.WEAVIATE_API_KEY}"
    
    @task
    def search_mixed_all_collections(self):
        """Execute mixed search types across all 9 collections in single request"""
        if not QUERIES_MIXED:
            return
        
        # Pick random query from 40 options (mix of BM25, Hybrid 0.1, Hybrid 0.9, Vector)
        query_data = random.choice(QUERIES_MIXED)
        search_type = query_data["search_type"]
        
        # Execute single GraphQL query that searches all collections
        with self.client.post(
            "/v1/graphql?consistency_level=ONE",
            headers=self.headers,
            json={"query": query_data["graphql"]},
            catch_response=True,
            name=f"Mixed_{search_type}_Multi_Collection"
        ) as response:
            if response.status_code == 200:
                result = response.json()
                if "errors" in result:
                    response.failure(f"GraphQL errors: {result['errors']}")
                else:
                    response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

