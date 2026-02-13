import json
import time
from kafka import KafkaConsumer
from pymongo import MongoClient
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
try:
    # Use MongoDB credentials from environment or defaults
    mongo_client = MongoClient("mongodb://admin:password@mongodb:27017/")
    db = mongo_client["retail_db"]
    collection = db["transactions"]
    logger.info("Connected to MongoDB successfully")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    exit(1)

# Simple Kafka consumer (no consumer group)
try:
    consumer = KafkaConsumer(
        'retail_transactions',
        bootstrap_servers='kafka:9092',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=False,  # Manually commit
        consumer_timeout_ms=10000  # Timeout after 10 seconds of no messages
    )
    logger.info("Connected to Kafka successfully")
except Exception as e:
    logger.error(f"Failed to connect to Kafka: {e}")
    exit(1)

logger.info("Starting simple processor - consuming ALL messages from beginning...")

message_count = 0
batch = []
batch_size = 10

try:
    for message in consumer:
        try:
            # Get the data
            data = message.value
            
            # Simple transformation: Calculate Total Amount
            if 'Quantity' in data and 'UnitPrice' in data:
                data['TotalAmount'] = data['Quantity'] * data['UnitPrice']
            
            # Add to batch
            batch.append(data)
            message_count += 1
            
            logger.info(f"Received message {message_count}: Invoice {data.get('InvoiceNo', 'Unknown')}")
            
            # Process batch when it reaches batch_size
            if len(batch) >= batch_size:
                # Insert batch to MongoDB
                result = collection.insert_many(batch)
                logger.info(f"✅ Inserted batch of {len(result.inserted_ids)} documents to MongoDB")
                batch = []
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            continue
            
except Exception as e:
    logger.info(f"Consumer finished or timed out: {e}")

# Process any remaining messages in batch
if batch:
    result = collection.insert_many(batch)
    logger.info(f"✅ Inserted final batch of {len(result.inserted_ids)} documents to MongoDB")

logger.info(f"🎉 Processing complete! Total messages processed: {message_count}")

# Check total in MongoDB
total_docs = collection.count_documents({})
logger.info(f"📊 Total documents now in MongoDB: {total_docs}")