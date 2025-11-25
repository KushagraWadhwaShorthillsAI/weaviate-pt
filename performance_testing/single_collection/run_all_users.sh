#!/bin/bash
# Run single-collection tests with 100, 200, 300 users automatically
# Usage: cd single_collection && ./run_all_users.sh

set -e

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║         Single-Collection Testing: 100, 200, 300 Users              ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "This will automatically run tests with:"
echo "  👥 100 users"
echo "  👥 200 users"
echo "  👥 300 users"
echo ""
echo "⏱️  Estimated duration: ~7-8 hours (3 × ~2.5 hours)"
echo ""
echo "🚀 Starting continuous testing..."

USER_COUNTS=(100 200 300)
RF_VALUE=${PT_RF_VALUE:-"current"}

echo ""
echo "Configuration: RF=$RF_VALUE"
echo ""

for USERS in "${USER_COUNTS[@]}"; do
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════╗"
    echo "║                    Testing with $USERS users                            ║"
    echo "╚══════════════════════════════════════════════════════════════════════╝"
    echo ""
    
    export PT_USER_COUNT=$USERS
    export PT_RF_VALUE=$RF_VALUE
    
    python3 run_automated_tests.py
    
    if [ $? -ne 0 ]; then
        echo "⚠️  Tests with $USERS users had errors - continuing anyway..."
        sleep 5
    fi
    
    # Save results
    echo ""
    echo "💾 Saving results for $USERS users..."
    RESULT_DIR="../single_results_RF${RF_VALUE}_Users${USERS}"
    mkdir -p "$RESULT_DIR"
    
    if [ -d "../../single_collection_reports" ]; then
        cp -r ../../single_collection_reports "$RESULT_DIR/"
    fi
    
    if [ -f "../../single_collection_report.html" ]; then
        cp ../../single_collection_report.html "$RESULT_DIR/single_collection_report_RF${RF_VALUE}_Users${USERS}.html"
    fi
    
    echo "✅ Results saved to: $RESULT_DIR"
    
    # Generate HTML report for this user count
    echo ""
    echo "📊 Generating HTML report for $USERS users..."
    cd ../report_generators
    python3 generate_single_report.py
    cd ../single_collection
    
    # Move report to results directory
    if [ -f "../../single_collection_report.html" ]; then
        mv ../../single_collection_report.html "$RESULT_DIR/single_collection_report_RF${RF_VALUE}_Users${USERS}.html"
        echo "✅ HTML report generated and saved!"
    fi
    
    if [ "$USERS" != "${USER_COUNTS[-1]}" ]; then
        echo ""
        echo "⏸️  $USERS users complete. Waiting 15 seconds..."
        sleep 15
    fi
done

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                 🎉 ALL USER COUNT TESTS COMPLETE!                    ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Results saved:"
echo "   ../single_results_RF${RF_VALUE}_Users100/"
echo "   ../single_results_RF${RF_VALUE}_Users200/"
echo "   ../single_results_RF${RF_VALUE}_Users300/"
echo ""
echo "📄 Individual HTML Reports:"
echo "   ../single_results_RF${RF_VALUE}_Users100/single_collection_report_RF${RF_VALUE}_Users100.html"
echo "   ../single_results_RF${RF_VALUE}_Users200/single_collection_report_RF${RF_VALUE}_Users200.html"
echo "   ../single_results_RF${RF_VALUE}_Users300/single_collection_report_RF${RF_VALUE}_Users300.html"
echo ""

