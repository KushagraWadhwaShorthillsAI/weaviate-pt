"""
Locust test for single collection vector search.
Tests nearVector on SongLyrics (1M objects) only.
"""


import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import json
import random
from locust import HttpUser, task, between, events
import config

QUERIES = []


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    global QUERIES
    filename = "queries/queries_vector_200.json"
    
    print("=" * 70)
    print(f"Loading: {filename}")
    print(f"Testing: Single collection ({config.WEAVIATE_CLASS_NAME}) - Vector")
    print("=" * 70)
    
    try:
        with open(filename, "r") as f:
            QUERIES = json.load(f)
        print(f"✓ Loaded {len(QUERIES)} vector queries")
        print("=" * 70)
    except Exception as e:
        print(f"❌ Failed to load {filename}: {e}")
        print("   Run: python ../generate_all_queries.py --type single --search-types vector")
        print("=" * 70)


class SingleVectorUser(HttpUser):
    # wait_time = between(1, 3)  # Removed to maximize throughput
    host = config.WEAVIATE_URL
    
    def on_start(self):
        self.headers = {"Content-Type": "application/json"}
        if config.WEAVIATE_API_KEY and config.WEAVIATE_API_KEY != "your-weaviate-api-key":
            self.headers["Authorization"] = f"Bearer {config.WEAVIATE_API_KEY}"
    
    @task
    def search_single_vector(self):
        if not QUERIES:
            return
        
        query_data = random.choice(QUERIES)
        
        with self.client.post(
            "/v1/graphql?consistency_level=ONE",
            headers=self.headers,
            json={"query": query_data["graphql"]},
            catch_response=True,
            name="Single_Vector_Search"
        ) as response:
            if response.status_code == 200:
                result = response.json()
                if "errors" not in result:
                    response.success()
                else:
                    response.failure("GraphQL errors")
            else:
                response.failure(f"HTTP {response.status_code}")

