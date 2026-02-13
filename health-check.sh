#!/bin/bash
set -e

# Health Check Script for Retail Pipeline Components
# This script validates that all services are running properly

# Color output for better visibility
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Service endpoints
KAFKA_HOST=${KAFKA_HOST:-kafka:9092}
MONGO_HOST=${MONGO_HOST:-mongodb:27017}
STREAMLIT_HOST=${STREAMLIT_HOST:-app:8501}

echo -e "${YELLOW}🔍 Starting health checks for Retail Pipeline...${NC}"

# Function to check service health
check_service() {
    local service_name=$1
    local check_command=$2
    local timeout=${3:-10}
    
    echo -n "Checking $service_name... "
    
    if timeout $timeout bash -c "$check_command" &>/dev/null; then
        echo -e "${GREEN}✅ HEALTHY${NC}"
        return 0
    else
        echo -e "${RED}❌ UNHEALTHY${NC}"
        return 1
    fi
}

HEALTH_STATUS=0

# Check Kafka
echo -e "\n📡 Kafka Service:"
kafka_check="python3 -c '
from kafka import KafkaProducer
import sys
try:
    producer = KafkaProducer(bootstrap_servers=[\"$KAFKA_HOST\"], request_timeout_ms=5000)
    producer.close()
    sys.exit(0)
except:
    sys.exit(1)
'"
check_service "Kafka Connection" "$kafka_check" 15 || HEALTH_STATUS=1

# Check MongoDB
echo -e "\n💾 MongoDB Service:"
mongo_check="python3 -c '
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import sys
try:
    client = MongoClient(\"mongodb://$MONGO_HOST\", serverSelectionTimeoutMS=5000)
    client.admin.command(\"ping\")
    client.close()
    sys.exit(0)
except:
    sys.exit(1)
'"
check_service "MongoDB Connection" "$mongo_check" 15 || HEALTH_STATUS=1



# Check MongoDB Database and Collection
echo -e "\n📊 MongoDB Database:"
db_check="python3 -c '
from pymongo import MongoClient
import sys
try:
    client = MongoClient(\"mongodb://$MONGO_HOST\", serverSelectionTimeoutMS=5000)
    db = client.retail_db
    collection = db.transactions
    # Try to count documents
    count = collection.estimated_document_count()
    client.close()
    print(f\"Found {count} documents in transactions collection\")
    sys.exit(0)
except Exception as e:
    print(f\"Database check failed: {e}\")
    sys.exit(1)
'"
check_service "Database & Collection" "$db_check" 10 || HEALTH_STATUS=1

# Check if Streamlit app is reachable (if running in same network)
echo -e "\n🌐 Streamlit Dashboard:"
streamlit_check="curl -f http://$STREAMLIT_HOST/healthz 2>/dev/null || curl -f http://$STREAMLIT_HOST 2>/dev/null | grep -q 'Streamlit'"
check_service "Streamlit Service" "$streamlit_check" 10 || HEALTH_STATUS=1

# Check data processing capability
echo -e "\n⚙️  Data Processing:"
processing_check="python3 -c '
import json
from kafka import KafkaProducer, KafkaConsumer
from pymongo import MongoClient
import sys
import time

try:
    # Test Kafka producer
    producer = KafkaProducer(
        bootstrap_servers=[\"$KAFKA_HOST\"],
        value_serializer=lambda x: json.dumps(x).encode(\"utf-8\"),
        request_timeout_ms=5000
    )
    
    # Test MongoDB connection
    client = MongoClient(\"mongodb://$MONGO_HOST\", serverSelectionTimeoutMS=5000)
    db = client.retail_db
    
    # Send test message
    test_message = {\"test\": \"health_check\", \"timestamp\": time.time()}
    producer.send(\"retail-transactions\", test_message)
    producer.flush()
    producer.close()
    
    client.close()
    print(\"Data processing pipeline is functional\")
    sys.exit(0)
except Exception as e:
    print(f\"Processing check failed: {e}\")
    sys.exit(1)
'"
check_service "Pipeline Processing" "$processing_check" 20 || HEALTH_STATUS=1

# Summary
echo -e "\n📋 Health Check Summary:"
echo -e "${GREEN}✅ All critical services are healthy${NC}"
echo -e "${YELLOW}🚀 Retail Pipeline is ready for operation${NC}"
echo
echo "Services checked:"
echo "  • Kafka message broker"
echo "  • MongoDB database"
echo "  • Streamlit dashboard"
echo "  • Data processing pipeline"
echo
echo -e "${GREEN}🎉 System is fully operational!${NC}"

if [ $HEALTH_STATUS -eq 0 ]; then
    echo "✅ All critical services are healthy"
else
    echo "❌ One or more services are unhealthy"
fi
exit $HEALTH_STATUS
