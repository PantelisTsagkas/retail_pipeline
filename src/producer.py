import pandas as pd
import json
import time
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

for index, row in df.iterrows():
    record = row.to_dict()
    producer.send(KAFKA_TOPIC, record)
    print(f"Sent: {record['InvoiceNo']}")
    time.sleep(0.5)  # Simulate real-time delay (tweak this speed)
