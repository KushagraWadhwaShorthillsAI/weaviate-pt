"""
Delete all SongLyrics collections quickly - no prompts
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests
import config

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


def delete_collection(collection_name):
    """Delete a collection"""
    headers = {"Content-Type": "application/json"}
    if config.WEAVIATE_API_KEY and config.WEAVIATE_API_KEY != "your-weaviate-api-key":
        headers["Authorization"] = f"Bearer {config.WEAVIATE_API_KEY}"
    
    try:
        response = requests.delete(
            f"{config.WEAVIATE_URL}/v1/schema/{collection_name}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"  ✅ {collection_name:25} Deleted")
            return True
        elif response.status_code == 404:
            print(f"  ⏭️  {collection_name:25} Not found (already deleted)")
            return True
        else:
            print(f"  ❌ {collection_name:25} Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ {collection_name:25} Error: {e}")
        return False


def main():
    print("=" * 70)
    print("DELETE ALL SONGLRYICS COLLECTIONS")
    print("=" * 70)
    print(f"\nWeaviate URL: {config.WEAVIATE_URL}")
    print(f"Collections to delete: {len(ALL_COLLECTIONS)}")
    print()
    
    for col in ALL_COLLECTIONS:
        print(f"  • {col}")
    
    print("\n" + "=" * 70)
    print("⚠️  WARNING: This will delete ALL collections and their data!")
    print("=" * 70)
    confirm = input("\nType 'DELETE ALL' to confirm: ").strip()
    
    if confirm != 'DELETE ALL':
        print("❌ Cancelled")
        return 1
    
    print("\n🗑️  Deleting collections...")
    print("-" * 70)
    
    success = 0
    failed = 0
    
    for collection in ALL_COLLECTIONS:
        if delete_collection(collection):
            success += 1
        else:
            failed += 1
    
    print("-" * 70)
    print(f"\n📊 Summary:")
    print(f"   Deleted: {success}/{len(ALL_COLLECTIONS)}")
    print(f"   Failed: {failed}")
    
    if failed == 0:
        print("\n✅ All collections deleted!")
        print("\nNext steps:")
        print("  1. Update schema to use 2 shards")
        print("  2. Run: python3 create_all_schemas.py")
        print("  3. Run restore for each collection")
    else:
        print(f"\n⚠️  {failed} collections failed to delete")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())