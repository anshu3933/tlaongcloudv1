#!/bin/bash

echo "🚀 Starting Comprehensive Assessment Pipeline Test"
echo "================================================="

# Check if backend is running
echo "🔍 Checking if backend is running..."
if curl -s http://localhost:8005/health > /dev/null; then
    echo "✅ Backend is running on port 8005"
else
    echo "❌ Backend is not running. Please start it first:"
    echo "   python start_test_service.py"
    exit 1
fi

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Run the comprehensive test
echo ""
echo "🧪 Running comprehensive pipeline test..."
echo "📝 Detailed logs will be saved to pipeline_test_*.log"
echo ""

python test_comprehensive_pipeline.py

echo ""
echo "📊 Test completed. Check the logs above for detailed results."
echo "📁 Log file saved for further analysis."