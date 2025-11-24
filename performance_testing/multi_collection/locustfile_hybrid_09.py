"""
Locust performance testing for Weaviate - Hybrid Search (alpha=0.9)
Tests vector-focused hybrid search (10% BM25, 90% vector).

Usage:
    locust -f locustfile_hybrid_09.py --users 100 --spawn-rate 5 --run-time 5m --headless
"""


import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import json
import random
from locust import HttpUser, task, between, events
import config


QUERIES_HYBRID_09 = []


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Load Hybrid 0.9 query file when Locust starts"""
    global QUERIES_HYBRID_09
    
    print("=" * 70)
    print("Loading Hybrid (alpha=0.9) query file...")
    print("=" * 70)
    
    try:
        with open("queries/queries_hybrid_09_200.json", "r") as f:
            QUERIES_HYBRID_09 = json.load(f)
        print(f"✓ Loaded query file: {len(QUERIES_HYBRID_09)} queries")
        print(f"  Search type: Hybrid (alpha=0.9 - vector-focused)")
        print(f"  Each query searches 9 collections")
        print(f"  Returns 200 results per collection")
        print("=" * 70)
    except Exception as e:
        print(f"❌ Failed to load queries_hybrid_09.json: {e}")
        print("   Run: python ../generate_all_queries.py --type multi --search-types hybrid_09")
        print("=" * 70)


class WeaviateHybrid09User(HttpUser):
    """Simulates a user performing Hybrid 0.9 searches"""
    
    # wait_time = between(1, 3)  # Removed for max throughput
    host = config.WEAVIATE_URL
    
    def on_start(self):
        """Setup headers"""
        self.headers = {"Content-Type": "application/json"}
        if config.WEAVIATE_API_KEY and config.WEAVIATE_API_KEY != "your-weaviate-api-key":
            self.headers["Authorization"] = f"Bearer {config.WEAVIATE_API_KEY}"
    
    @task
    def search_hybrid_09_all_collections(self):
        """Execute Hybrid (0.9) search across all 9 collections in single request"""
        if not QUERIES_HYBRID_09:
            return
        
        # Pick random query from 40 options
        query_data = random.choice(QUERIES_HYBRID_09)
        
        # Execute single GraphQL query that searches all collections
        with self.client.post(
            "/v1/graphql?consistency_level=ONE",
            headers=self.headers,
            json={"query": query_data["graphql"]},
            catch_response=True,
            name="Hybrid_0.9_Multi_Collection_Search"
        ) as response:
            if response.status_code == 200:
                result = response.json()
                if "errors" in result:
                    response.failure(f"GraphQL errors: {result['errors']}")
                else:
                    response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

