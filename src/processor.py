import json
import logging
import os

from kafka import KafkaConsumer
from pymongo import MongoClient

# Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://admin:password@mongodb:27017/")
KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run():
    """Main entry point for the processor."""

    # MongoDB connection
    try:
        mongo_client = MongoClient(MONGODB_URI)
        db = mongo_client["retail_db"]
        collection = db["transactions"]
        logger.info("Connected to MongoDB successfully")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return

    # Kafka consumer
    try:
        consumer = KafkaConsumer(
            "retail_transactions",
            bootstrap_servers=KAFKA_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            consumer_timeout_ms=10000,
        )
        logger.info("Connected to Kafka successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Kafka: {e}")
        return

    logger.info("Starting processor - consuming all messages from beginning...")

    message_count = 0
    batch = []
    batch_size = 10

    try:
        for message in consumer:
            try:
                data = message.value

                # Transform: calculate TotalAmount
                if "Quantity" in data and "UnitPrice" in data:
                    data["TotalAmount"] = data["Quantity"] * data["UnitPrice"]

                batch.append(data)
                message_count += 1
                logger.info(
                    f"Received message {message_count}: "
                    f"Invoice {data.get('InvoiceNo', 'Unknown')}"
                )

                if len(batch) >= batch_size:
                    result = collection.insert_many(batch)
                    logger.info(
                        f"✅ Inserted batch of {len(result.inserted_ids)} documents"
                    )
                    batch = []

            except Exception as e:
                logger.error(f"Error processing message: {e}")
                continue

    except Exception as e:
        logger.info(f"Consumer finished or timed out: {e}")

    # Flush any remaining messages now
    if batch:
        result = collection.insert_many(batch)
        logger.info(
            f"✅ Inserted final batch of {len(result.inserted_ids)} documents"
        )

    logger.info(f"🎉 Processing complete! Total messages processed: {message_count}")

    total_docs = collection.count_documents({})
    logger.info(f"📊 Total documents now in MongoDB: {total_docs}")

    mongo_client.close()
    consumer.close()


if __name__ == "__main__":
    run()