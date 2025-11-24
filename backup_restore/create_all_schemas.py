"""
Create Weaviate schemas for SongLyrics collections.
Schema is hardcoded (doesn't depend on existing SongLyrics collection).
Supports creating single collection or all collections.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests
import config

# All collection names
ALL_COLLECTIONS = [
    'SongLyrics',
    'SongLyrics_400k',
    'SongLyrics_200k',
    'SongLyrics_50k',
    'SongLyrics_30k',
    'SongLyrics_20k',
    'SongLyrics_15k',
    'SongLyrics_12k',
    'SongLyrics_10k'
]

# Complete schema (copied from create_weaviate_schema.py)
# This is the EXACT schema used for SongLyrics creation
BASE_SCHEMA = {
    "class": "SongLyrics",  # Will be replaced with actual collection name
    "description": "Song lyrics with metadata and embeddings",
    
    # Sharding configuration
    "shardingConfig": {
        "desiredCount": 3
    },
    
    # Replication configuration
    "replicationConfig": {
        "asyncEnabled": True,
        "factor": 1
    },
    
    # Vector index configuration with RQ (Roaring Quantization)
    # RQ is supported in Weaviate v1.32+, default in v1.33+
    # "vectorIndexConfig": {
    #     "rq": {
    #         "enabled": True
    #     }
    # },
    
    # Inverted index configuration with BlockMaxWAND disabled
    "invertedIndexConfig": {
        "usingBlockMaxWAND": False  # Explicitly disable BlockMaxWAND
    },
    
    # Properties with specific tokenization
    "properties": [
        # Searchable text fields with WORD tokenization
        {
            "name": "title",
            "dataType": ["text"],
            "description": "Song title",
            "indexSearchable": True,
            "indexFilterable": False,
            "tokenization": "word"
        },
        {
            "name": "lyrics",
            "dataType": ["text"],
            "description": "Song lyrics content",
            "indexSearchable": True,
            "indexFilterable": False,
            "tokenization": "word"
        },
        
        # Filterable fields with FIELD tokenization
        {
            "name": "tag",
            "dataType": ["text"],
            "description": "Genre/category tag",
            "indexSearchable": False,
            "indexFilterable": True,
            "tokenization": "field"
        },
        {
            "name": "artist",
            "dataType": ["text"],
            "description": "Artist name",
            "indexSearchable": False,
            "indexFilterable": True,
            "tokenization": "field"
        },
        {
            "name": "features",
            "dataType": ["text"],
            "description": "Featured artists",
            "indexSearchable": False,
            "indexFilterable": True,
            "tokenization": "field"
        },
        {
            "name": "song_id",
            "dataType": ["text"],
            "description": "Unique song identifier",
            "indexSearchable": False,
            "indexFilterable": True,
            "tokenization": "field"
        },
        {
            "name": "language_cld3",
            "dataType": ["text"],
            "description": "Language detected by CLD3",
            "indexSearchable": False,
            "indexFilterable": True,
            "tokenization": "field"
        },
        {
            "name": "language_ft",
            "dataType": ["text"],
            "description": "Language detected by FastText",
            "indexSearchable": False,
            "indexFilterable": True,
            "tokenization": "field"
        },
        {
            "name": "language",
            "dataType": ["text"],
            "description": "Primary language",
            "indexSearchable": False,
            "indexFilterable": True,
            "tokenization": "field"
        },
        
        # Numeric fields (automatically filterable with range filter support)
        {
            "name": "year",
            "dataType": ["int"],
            "description": "Release year",
            "indexFilterable": True,
            "indexRangeFilters": True
        },
        {
            "name": "views",
            "dataType": ["int"],
            "description": "Number of views",
            "indexFilterable": True,
            "indexRangeFilters": True
        }
    ]
}


def create_schema(collection_name):
    """Create schema for a specific collection"""
    headers = {"Content-Type": "application/json"}
    if config.WEAVIATE_API_KEY and config.WEAVIATE_API_KEY != "your-weaviate-api-key":
        headers["Authorization"] = f"Bearer {config.WEAVIATE_API_KEY}"
    
    # Check if collection already exists
    check_response = requests.get(
        f"{config.WEAVIATE_URL}/v1/schema/{collection_name}",
        headers=headers,
        timeout=30
    )
    
    if check_response.status_code == 200:
        print(f"  ✓ {collection_name:25} Already exists (skipping)")
        return 'exists'
    
    # Create schema with target name (deep copy to avoid modifying BASE_SCHEMA)
    import copy
    target_schema = copy.deepcopy(BASE_SCHEMA)
    target_schema['class'] = collection_name
    
    response = requests.post(
        f"{config.WEAVIATE_URL}/v1/schema",
        headers=headers,
        json=target_schema,
        timeout=30
    )
    
    if response.status_code == 200:
        print(f"  ✅ {collection_name:25} Created successfully")
        return 'created'
    else:
        print(f"  ❌ {collection_name:25} Failed: {response.status_code}")
        print(f"     {response.text[:200]}")
        return 'failed'


def main():
    """Create schemas for collections"""
    
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "CREATE COLLECTION SCHEMAS" + " "*28 + "║")
    print("╚" + "="*68 + "╝")
    print()
    print(f"Weaviate URL: {config.WEAVIATE_URL}")
    print()
    
    # Show available collections
    print("Available collections:")
    for i, col in enumerate(ALL_COLLECTIONS, 1):
        print(f"  {i:2}. {col}")
    
    print("\nOptions:")
    print("  • Enter 'all' to create all collection schemas")
    print("  • Enter collection number (e.g., '11' for SongLyrics_10k)")
    print("  • Enter multiple numbers (e.g., '1 11' for multiple)")
    print()
    
    choice = input("Your choice: ").strip().lower()
    
    if choice == 'all':
        collections = ALL_COLLECTIONS
        print(f"\n✅ Selected: All {len(collections)} collections")
    else:
        try:
            indices = [int(x) for x in choice.split()]
            collections = [ALL_COLLECTIONS[i-1] for i in indices if 1 <= i <= len(ALL_COLLECTIONS)]
            
            if not collections:
                print("❌ No valid collections selected")
                return 1
            
            print(f"\n✅ Selected {len(collections)} collection(s):")
            for col in collections:
                print(f"   • {col}")
        except:
            print("❌ Invalid input")
            return 1
    
    print(f"\n🔧 Creating schemas...")
    print("-" * 70)
    
    created = 0
    existed = 0
    failed = 0
    
    for collection in collections:
        result = create_schema(collection)
        if result == 'created':
            created += 1
        elif result == 'exists':
            existed += 1
        else:
            failed += 1
    
    print("-" * 70)
    print(f"\n📊 Summary:")
    print(f"   Created: {created}")
    print(f"   Already existed: {existed}")
    print(f"   Failed: {failed}")
    print(f"   Total: {len(collections)}")
    
    if failed == 0:
        print(f"\n✅ All selected schemas ready!")
        if 'all' in choice or len(collections) > 1:
            print(f"\nYou can now restore backups for these collections.")
        return 0
    else:
        print(f"\n⚠️  Some schemas failed to create")
        return 1


if __name__ == "__main__":
    sys.exit(main())
