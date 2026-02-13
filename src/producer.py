import json
import os
import time

import pandas as pd
from kafka import KafkaProducer

# Configuration
KAFKA_TOPIC = "retail_transactions"
KAFKA_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")


def json_serializer(data):
    return json.dumps(data).encode("utf-8")


def load_data(filepath):
    """Load CSV with fallback encoding handling."""
    for encoding in ("utf-8", "latin-1", "iso-8859-1"):
        try:
            df = pd.read_csv(filepath, encoding=encoding)
            if encoding != "utf-8":
                print(f"Loaded with {encoding} encoding")
            return df
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not read {filepath} with any supported encoding")


def run():
    """Main entry point for the producer."""
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_SERVER], value_serializer=json_serializer
    )

    print("Loading data...")
    df = load_data("/app/data/Online_Retail.csv")
    df = df.dropna()

    print(f"Starting stream of {len(df)} records...")

    BATCH_SIZE = 50
    for i, (index, row) in enumerate(df.iterrows()):
        record = row.to_dict()
        producer.send(KAFKA_TOPIC, record)
        if i % BATCH_SIZE == 0:
            producer.flush()
            time.sleep(0.5)

    producer.flush()
    producer.close()
    print("✅ All records sent successfully")


if __name__ == "__main__":
    run()
