#!/bin/bash
# FULLY AUTOMATED Multi-Collection Performance Testing
# Handles everything: query generation, testing, and reporting
# Supports environment variables: PT_USER_COUNT, PT_RF_VALUE

# Set defaults if not provided by wrapper
USER_COUNT=${PT_USER_COUNT:-100}
RF_VALUE=${PT_RF_VALUE:-"current"}

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║   MULTI-COLLECTION PERFORMANCE TESTS - FULLY AUTOMATED               ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Configuration:"
echo "  👥 Users: $USER_COUNT"
echo "  🔄 RF: $RF_VALUE"
echo ""
echo "This script will:"
echo "  1. Check and generate query files if needed"
echo "  2. Run 5 search types × 5 limits = 25 tests"
echo "  3. Generate combined performance report"
echo "  4. Total duration: ~2 hours 15 minutes"
echo ""

# Step 1: Check and generate query files
echo "═══════════════════════════════════════════════════════════════════════"
echo "STEP 1: Checking Query Files"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""

MISSING_QUERIES=false

# Check if query files exist in queries/ folder
if [ ! -f "queries/queries_bm25_200.json" ]; then
    echo "⚠️  Query files not found in queries/ folder"
    MISSING_QUERIES=true
fi

if [ "$MISSING_QUERIES" = true ]; then
    echo ""
    echo "Generating all query files..."
    echo "This will take ~2 minutes (calls Azure OpenAI)"
    echo ""
    
    # Generate all queries using unified generator
    echo "🔄 Generating all multi-collection queries..."
    cd ..
    python3 generate_all_queries.py --type multi
    if [ $? -ne 0 ]; then
        echo "❌ Failed to generate query files"
        exit 1
    fi
    cd multi_collection
    
    echo ""
    echo "✅ All query files generated successfully"
else
    echo "✅ All query files found"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo "STEP 2: Running Performance Tests"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""

# Function to update locustfile with correct query filename
update_locustfile_query() {
    local locustfile=$1
    local new_filename=$2
    
    python3 << PYEOF
import re
with open('$locustfile', 'r') as f:
    content = f.read()

# Replace the query filename
content = re.sub(
    r'(with\s+open\s*\(\s*["\'])queries_[^"\']+\.json',
    r'\1$new_filename',
    content
)

with open('$locustfile', 'w') as f:
    f.write(content)
PYEOF
}

# Update vector locustfile limit
update_vector_limit() {
    local limit=$1
    python3 << PYEOF
import re
with open('locustfile_vector.py', 'r') as f:
    content = f.read()
content = re.sub(r'limit\s*=\s*\d+', f'limit = $limit', content)
with open('locustfile_vector.py', 'w') as f:
    f.write(content)
PYEOF
}

# Array of limits
LIMITS=(10 50 100 150 200)

# Run tests for each limit
for LIMIT in "${LIMITS[@]}"; do
    echo "╔══════════════════════════════════════════════════════════════════════╗"
    echo "║                      TESTING LIMIT $LIMIT                                ║"
    echo "╚══════════════════════════════════════════════════════════════════════╝"
    echo ""
    
    REPORT_DIR="../../multi_collection_reports/reports_${LIMIT}"
    mkdir -p "$REPORT_DIR"
    
    # Test 1/5: BM25
    echo "🔍 Test 1/5: BM25 (limit=$LIMIT, users=$USER_COUNT)"
    echo "────────────────────────────────────────────────────────────────────"
    update_locustfile_query "locustfile_bm25.py" "queries_bm25_${LIMIT}.json"
    locust -f locustfile_bm25.py --users $USER_COUNT --spawn-rate 10 --run-time 5m --headless \
        --html "$REPORT_DIR/bm25_report.html" \
        --csv "$REPORT_DIR/bm25"
    echo "✅ BM25 complete"
    sleep 3
    
    # Test 2/5: Hybrid 0.1
    echo ""
    echo "🔍 Test 2/5: Hybrid α=0.1 (limit=$LIMIT, users=$USER_COUNT)"
    echo "────────────────────────────────────────────────────────────────────"
    update_locustfile_query "locustfile_hybrid_01.py" "queries_hybrid_01_${LIMIT}.json"
    locust -f locustfile_hybrid_01.py --users $USER_COUNT --spawn-rate 10 --run-time 5m --headless \
        --html "$REPORT_DIR/hybrid_01_report.html" \
        --csv "$REPORT_DIR/hybrid_01"
    echo "✅ Hybrid 0.1 complete"
    sleep 3
    
    # Test 3/5: Hybrid 0.9
    echo ""
    echo "🔍 Test 3/5: Hybrid α=0.9 (limit=$LIMIT, users=$USER_COUNT)"
    echo "────────────────────────────────────────────────────────────────────"
    update_locustfile_query "locustfile_hybrid_09.py" "queries_hybrid_09_${LIMIT}.json"
    locust -f locustfile_hybrid_09.py --users $USER_COUNT --spawn-rate 10 --run-time 5m --headless \
        --html "$REPORT_DIR/hybrid_09_report.html" \
        --csv "$REPORT_DIR/hybrid_09"
    echo "✅ Hybrid 0.9 complete"
    sleep 3
    
    # Test 4/5: Vector
    echo ""
    echo "🔍 Test 4/5: Vector (limit=$LIMIT, users=$USER_COUNT)"
    echo "────────────────────────────────────────────────────────────────────"
    update_vector_limit $LIMIT
    locust -f locustfile_vector.py --users $USER_COUNT --spawn-rate 10 --run-time 5m --headless \
        --html "$REPORT_DIR/vector_report.html" \
        --csv "$REPORT_DIR/vector"
    echo "✅ Vector complete"
    sleep 3
    
    # Test 5/5: Mixed
    echo ""
    echo "🔍 Test 5/5: Mixed (limit=$LIMIT, users=$USER_COUNT)"
    echo "────────────────────────────────────────────────────────────────────"
    update_locustfile_query "locustfile_mixed.py" "queries_mixed_${LIMIT}.json"
    locust -f locustfile_mixed.py --users $USER_COUNT --spawn-rate 10 --run-time 5m --headless \
        --html "$REPORT_DIR/mixed_report.html" \
        --csv "$REPORT_DIR/mixed"
    echo "✅ Mixed complete"
    
    if [ "$LIMIT" != "200" ]; then
        echo ""
        echo "⏸️  Limit $LIMIT complete. Waiting 10 seconds before next limit..."
        sleep 10
    fi
    echo ""
done

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║              ✅ ALL MULTI-COLLECTION TESTS COMPLETE!                 ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Results saved to: ../../multi_collection_reports/reports_*/"
echo ""

# Step 3: Generate combined report
echo "═══════════════════════════════════════════════════════════════════════"
echo "STEP 3: Generating Combined Report"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""

cd ../report_generators
python3 generate_combined_report.py
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Combined report generated: ../../multi_collection_report.html"
else
    echo ""
    echo "⚠️  Report generation had warnings (check above)"
fi
cd ../multi_collection

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                    🎉 ALL DONE!                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 View Results:"
echo "   open combined_performance_report_2nd.html"
echo ""
echo "📂 Individual Reports:"
echo "   ../../multi_collection_reports/reports_10/*_report.html"
echo "   ../../multi_collection_reports/reports_50/*_report.html"
echo "   ... (5 limit folders)"
echo ""
echo "📈 What to Check:"
echo "   • Response time increases with limit ✅"
echo "   • Content size grows proportionally ✅"
echo "   • Failure rate = 0% ✅"
echo "   • Vector results show growth (not flat) ✅"
echo ""

