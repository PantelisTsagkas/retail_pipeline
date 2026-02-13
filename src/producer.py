import json
import time

import pandas as pd
from kafka import KafkaProducer

# Configuration
KAFKA_TOPIC = "retail_transactions"
KAFKA_SERVER = "kafka:9092"  # 'kafka' matches the service name in docker-compose


def json_serializer(data):
    return json.dumps(data).encode("utf-8")


producer = KafkaProducer(
    bootstrap_servers=[KAFKA_SERVER], value_serializer=json_serializer
)

print("Loading data...")
# Load CSV with proper encoding handling
try:
    df = pd.read_csv("/app/data/Online_Retail.csv", encoding="utf-8")
except UnicodeDecodeError:
    try:
        df = pd.read_csv("/app/data/Online_Retail.csv", encoding="latin-1")
        print("Loaded with latin-1 encoding")
    except UnicodeDecodeError:
        df = pd.read_csv("/app/data/Online_Retail.csv", encoding="iso-8859-1")
        print("Loaded with iso-8859-1 encoding")

df = df.dropna()  # specific cleanup

print(f"Starting stream of {len(df)} records...")

# Better — sleep once per batch
BATCH_SIZE = 50
for i, (index, row) in enumerate(df.iterrows()):
    record = row.to_dict()
    producer.send(KAFKA_TOPIC, record)
    if i % BATCH_SIZE == 0:
        producer.flush()
        time.sleep(0.5)

# Add at the end of producer.py
producer.flush()
producer.close()
print("✅ All records sent successfully")
