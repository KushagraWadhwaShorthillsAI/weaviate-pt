"""
Locust performance testing for Weaviate - Pure Vector Search (nearVector)
Tests semantic search performance using only vector similarity (no BM25).

Usage:
    locust -f locustfile_vector.py --users 100 --spawn-rate 5 --run-time 5m --headless
"""


import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import json
import random
from locust import HttpUser, task, between, events
import config


QUERIES_VECTOR = []


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Load vector query file when Locust starts"""
    global QUERIES_VECTOR
    
    filename = "queries/queries_vector_200.json"
    
    print("=" * 70)
    print(f"Loading pure vector search queries: {filename}")
    print("=" * 70)
    
    try:
        with open(filename, "r") as f:
            QUERIES_VECTOR = json.load(f)
        print(f"✓ Loaded {len(QUERIES_VECTOR)} queries")
        print(f"  Search type: nearVector (pure semantic)")
        print(f"  Each query searches 9 collections")
        print(f"  Returns 200 results per collection")
        print("=" * 70)
    except Exception as e:
        print(f"❌ Failed to load {filename}: {e}")
        print("   Run: python ../generate_all_queries.py --type multi --search-types vector")
        print("=" * 70)


class WeaviateVectorUser(HttpUser):
    """Simulates a user performing pure vector searches"""
    
    # wait_time = between(1, 3)  # Removed for max throughput
    host = config.WEAVIATE_URL
    
    def on_start(self):
        """Setup headers"""
        self.headers = {"Content-Type": "application/json"}
        if config.WEAVIATE_API_KEY and config.WEAVIATE_API_KEY != "your-weaviate-api-key":
            self.headers["Authorization"] = f"Bearer {config.WEAVIATE_API_KEY}"
    
    @task
    def search_vector_all_collections(self):
        """Execute pure vector search across all 9 collections in single request"""
        if not QUERIES_VECTOR:
            return
        
        # Pick random query from 40 options
        query_data = random.choice(QUERIES_VECTOR)
        
        # Execute single GraphQL query that searches all collections
        with self.client.post(
            "/v1/graphql?consistency_level=ONE",
            headers=self.headers,
            json={"query": query_data["graphql"]},
            catch_response=True,
            name="Vector_Multi_Collection_Search"
        ) as response:
            if response.status_code == 200:
                result = response.json()
                if "errors" in result:
                    response.failure(f"GraphQL errors: {result['errors']}")
                else:
                    response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

