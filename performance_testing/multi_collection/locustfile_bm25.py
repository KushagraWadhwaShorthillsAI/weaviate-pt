"""
Locust performance testing for Weaviate - BM25 Search Only
Tests pure keyword search performance across all collections.

Usage:
    locust -f locustfile_bm25.py --users 100 --spawn-rate 5 --run-time 5m --headless
"""


import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import json
import random
from locust import HttpUser, task, between, events
import config


QUERIES_BM25 = []


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Load BM25 query file when Locust starts"""
    global QUERIES_BM25
    
    print("=" * 70)
    print("Loading BM25 query file...")
    print("=" * 70)
    
    try:
        with open("queries/queries_bm25_200.json", "r") as f:
            QUERIES_BM25 = json.load(f)
        print(f"✓ Loaded query file: {len(QUERIES_BM25)} queries")
        print(f"  Each query searches 9 collections")
        print(f"  Returns 200 results per collection")
        print("=" * 70)
    except Exception as e:
        print(f"❌ Failed to load queries_bm25.json: {e}")
        print("   Run: python ../generate_all_queries.py --type multi --search-types bm25")
        print("=" * 70)


class WeaviateBM25User(HttpUser):
    """Simulates a user performing BM25 searches"""
    
    # wait_time = between(1, 3)  # Removed for max throughput
    host = config.WEAVIATE_URL
    
    def on_start(self):
        """Setup headers"""
        self.headers = {"Content-Type": "application/json"}
        if config.WEAVIATE_API_KEY and config.WEAVIATE_API_KEY != "your-weaviate-api-key":
            self.headers["Authorization"] = f"Bearer {config.WEAVIATE_API_KEY}"
    
    @task
    def search_bm25_all_collections(self):
        """Execute BM25 search across all 9 collections in single request"""
        if not QUERIES_BM25:
            return
        
        # Pick random query from 40 options
        query_data = random.choice(QUERIES_BM25)
        
        # Execute single GraphQL query that searches all collections
        with self.client.post(
            "/v1/graphql?consistency_level=ONE",
            headers=self.headers,
            json={"query": query_data["graphql"]},
            catch_response=True,
            name="BM25_Multi_Collection_Search"
        ) as response:
            if response.status_code == 200:
                result = response.json()
                if "errors" in result:
                    response.failure(f"GraphQL errors: {result['errors']}")
                else:
                    # Success - all 9 collections searched
                    response.success()
            else:
                response.failure(f"HTTP {response.status_code}")

