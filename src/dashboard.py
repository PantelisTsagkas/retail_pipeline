import time

import pandas as pd
import streamlit as st
from pymongo import MongoClient
import os

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://admin:password@mongodb:27017/")

st.set_page_config(layout="wide")
st.title("Real-Time Retail Dashboard 🛒")

# Connect to Mongo with error handling
try:
    # Use MongoDB credentials from environment or defaults
    client = MongoClient(
        MONGODB_URI, serverSelectionTimeoutMS=5000
    )
    db = client["retail_db"]
    collection = db["transactions"]
    # Test the connection
    client.admin.command("ping")
    st.success("✅ Connected to MongoDB successfully!")
except Exception as e:
    st.error(f"❌ MongoDB Connection Error: {e}")
    st.stop()

placeholder = st.empty()

while True:
    try:
        # Fetch latest 100 transactions
        data = list(collection.find().sort("_id", -1).limit(100))
        doc_count = collection.count_documents({})

        with placeholder.container():
            st.info(f"📊 Total documents in database: {doc_count}")

            if data:
                df = pd.DataFrame(data)

                # KPI Metrics
                total_sales = df["TotalAmount"].sum()
                st.metric(
                    label="Total Sales (Live Batch)", value=f"${total_sales:,.2f}"
                )

                # Charts
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Top Selling Countries")
                    st.bar_chart(df["Country"].value_counts())

                with col2:
                    st.subheader("Recent Transactions")
                    st.dataframe(
                        df[["InvoiceNo", "Description", "TotalAmount", "Country"]]
                    )
            else:
                st.write("Waiting for data...")
                st.write(
                    "Run: `docker-compose exec app python src/producer.py` to generate data"
                )
                st.write(
                    "Then run: `docker-compose exec app python src/test_processor.py` to process it"
                )

    except Exception as e:
        st.error(f"Error fetching data: {e}")

    time.sleep(2)
    st.rerun()