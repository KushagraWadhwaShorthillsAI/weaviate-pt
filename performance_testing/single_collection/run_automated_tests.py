"""
Automated performance testing script.
Runs all 5 search types across 5 different limits.
Total: 25 tests (5 search types × 5 limits).
Supports environment variables: PT_USER_COUNT, PT_RF_VALUE
"""


import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import subprocess
import os
import time
import sys

# Read user count from environment variable (default to 100)
DEFAULT_USER_COUNT = int(os.environ.get('PT_USER_COUNT', 100))
RF_VALUE = os.environ.get('PT_RF_VALUE', 'current')


def run_locust_test(locustfile, limit, search_type, users=None, spawn_rate=10, duration='5m'):
    """Run a single Locust test"""
    
    # Use provided users or default from environment
    if users is None:
        users = DEFAULT_USER_COUNT
    
    # Create reports folder for this limit (at project root level)
    reports_dir = f"../../single_collection_reports/reports_{limit}"
    os.makedirs(reports_dir, exist_ok=True)
    
    # Update locustfile to use correct query file
    update_locustfile_for_limit(locustfile, limit)
    
    # Construct Locust command
    cmd = [
        'locust',
        '-f', locustfile,
        '--users', str(users),
        '--spawn-rate', str(spawn_rate),
        '--run-time', duration,
        '--headless',
        '--html', f'{reports_dir}/{search_type}_report.html',
        '--csv', f'{reports_dir}/{search_type}'
    ]
    
    print(f"\n🚀 Running: {search_type.upper()} test (limit={limit}, users={users}, RF={RF_VALUE})")
    print(f"   Command: {' '.join(cmd)}")
    print("-" * 70)
    
    try:
        # Run Locust
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        print(f"✅ {search_type.upper()} test complete (limit={limit})")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {search_type.upper()} test failed (limit={limit}): {e}")
        return False
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False


def update_locustfile_for_limit(locustfile, limit):
    """Update locustfile to load correct query file for this limit"""
    
    # Read file
    with open(locustfile, 'r') as f:
        lines = f.readlines()
    
    # Determine search type from filename
    if 'bm25' in locustfile:
        new_filename = f'queries_bm25_{limit}.json'
    elif 'hybrid_01' in locustfile:
        new_filename = f'queries_hybrid_01_{limit}.json'
    elif 'hybrid_09' in locustfile:
        new_filename = f'queries_hybrid_09_{limit}.json'
    elif 'vector' in locustfile:
        new_filename = f'queries_vector_{limit}.json'
    elif 'mixed' in locustfile:
        new_filename = f'queries_mixed_{limit}.json'
    else:
        return
    
    # Update the line with open("queries/queries_*.json", "r")
    updated_lines = []
    for line in lines:
        if 'with open(' in line and 'queries_' in line and '.json' in line:
            # Replace with correct filename
            import re
            # Match pattern: with open("queries/queries_something.json" or with open('queries_something.json'
            line = re.sub(r'(with\s+open\s*\(\s*["\'])queries_[^"\']+\.json', rf'\1{new_filename}', line)
        updated_lines.append(line)
    
    # Write back
    with open(locustfile, 'w') as f:
        f.writelines(updated_lines)


def main():
    """Main automation function"""
    
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "AUTOMATED PERFORMANCE TEST SUITE" + " " * 21 + "║")
    print("╚" + "=" * 68 + "╝")
    
    # Configuration
    limits = [10, 50, 100, 150, 200]
    collection_name = config.WEAVIATE_CLASS_NAME
    users = DEFAULT_USER_COUNT  # Use environment variable or default 100
    spawn_rate = 10
    duration = '5m'
    
    print(f"\n📊 Test Configuration:")
    print(f"   Collection: {collection_name}")
    print(f"   Limits to test: {limits}")
    print(f"   Users: {users} (RF: {RF_VALUE})")
    print(f"   Spawn rate: {spawn_rate} users/second")
    print(f"   Duration: {duration} per test")
    print(f"   Total tests: {len(limits) * 5} (5 search types × {len(limits)} limits)")
    print(f"   Estimated time: ~{len(limits) * 5 * 5 + len(limits) * 2} minutes")
    print("=" * 70)
    
    # Auto-confirm when running from run_all_users.sh
    print("\n🚀 Starting automated testing...")
    
    # Step 1: Generate queries (one-time)
    print("\n" + "=" * 70)
    print("STEP 1: Generating Queries (One-Time)")
    print("=" * 70)
    subprocess.run(['python', '../generate_all_queries.py', '--type', 'single'], check=True)
    
    # Step 2: Run tests for each limit
    test_results = []
    
    for i, limit in enumerate(limits, 1):
        print("\n" + "╔" + "=" * 68 + "╗")
        print(f"║  LIMIT {limit:3} - Testing {i}/{len(limits)}" + " " * (68 - len(f"  LIMIT {limit:3} - Testing {i}/{len(limits)}")) + "║")
        print("╚" + "=" * 68 + "╝")
        
        # Test 1: BM25
        success = run_locust_test(
            'locustfile_bm25.py',
            limit,
            'bm25',
            users=users,
            spawn_rate=spawn_rate,
            duration=duration
        )
        test_results.append(('BM25', limit, success))
        time.sleep(5)  # Short pause between tests
        
        # Test 2: Hybrid 0.1
        success = run_locust_test(
            'locustfile_hybrid_01.py',
            limit,
            'hybrid_01',
            users=users,
            spawn_rate=spawn_rate,
            duration=duration
        )
        test_results.append(('Hybrid 0.1', limit, success))
        time.sleep(5)
        
        # Test 3: Hybrid 0.9
        success = run_locust_test(
            'locustfile_hybrid_09.py',
            limit,
            'hybrid_09',
            users=users,
            spawn_rate=spawn_rate,
            duration=duration
        )
        test_results.append(('Hybrid 0.9', limit, success))
        time.sleep(5)
        
        # Test 4: Vector
        success = run_locust_test(
            'locustfile_single_vector.py',
            limit,
            'vector',
            users=users,
            spawn_rate=spawn_rate,
            duration=duration
        )
        test_results.append(('Vector', limit, success))
        time.sleep(5)
        
        # Test 5: Mixed
        success = run_locust_test(
            'locustfile_mixed.py',
            limit,
            'mixed',
            users=users,
            spawn_rate=spawn_rate,
            duration=duration
        )
        test_results.append(('Mixed', limit, success))
        
        # Longer pause between limits
        if i < len(limits):
            print(f"\n⏸️  Completed limit {limit}. Waiting 10 seconds before next limit...")
            time.sleep(10)
    
    # Final summary
    print("\n" + "╔" + "=" * 68 + "╗")
    print("║" + " " * 24 + "ALL TESTS COMPLETE!" + " " * 24 + "║")
    print("╚" + "=" * 68 + "╝")
    
    print("\n📊 Test Results:")
    print("-" * 70)
    
    for search_type, limit, success in test_results:
        status = "✅" if success else "❌"
        print(f"{status} {search_type:12} | Limit {limit:3} | {'Success' if success else 'Failed'}")
    
    total_tests = len(test_results)
    successful = sum(1 for _, _, s in test_results if s)
    failed = total_tests - successful
    
    print("-" * 70)
    print(f"Total: {total_tests} tests | ✅ {successful} passed | ❌ {failed} failed")
    print("=" * 70)
    
    print("\n📂 Reports saved in:")
    for limit in limits:
        print(f"   ../../single_collection_reports/reports_{limit}/")
    
    print("\n📊 Generate combined report:")
    print("   cd ../report_generators")
    print("   python3 generate_single_report.py")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    import config
    sys.exit(main())

