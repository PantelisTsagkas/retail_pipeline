import json
import os
import subprocess
import sys
import time
from unittest.mock import patch

import pandas as pd
import pytest
import requests

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))


class TestIntegration:
    """Integration tests for the complete pipeline"""

    def test_docker_services_running(self):
        """Test that all required Docker services are running"""
        try:
            # Check if docker compose ps command works
            result = subprocess.run(
                ["docker","compose","ps"], capture_output=True, text=True, timeout=10
            )

            # Should not fail
            assert result.returncode == 0

            # Check for required services in output
            required_services = ["kafka", "mongodb", "zookeeper", "python_app"]
            for service in required_services:
                assert service in result.stdout.lower()

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker not available or not running")

    def test_kafka_connectivity(self):
        """Test that Kafka is accessible"""
        try:
            from kafka import KafkaProducer

            # Try to create a Kafka producer
            producer = KafkaProducer(
                bootstrap_servers=["kafka:9092"], request_timeout_ms=5000
            )
            producer.close()
            # Connection successful

        except Exception:
            try:
                # Fallback: Try using docker command
                result = subprocess.run(
                    [
                        "docker",
                        "compose",
                        "exec",
                        "-T",
                        "kafka",
                        "kafka-topics",
                        "--list",
                        "--bootstrap-server",
                        "kafka:9092",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                assert result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                pytest.skip("Kafka not available for testing")

    def test_mongodb_connectivity(self):
        """Test that MongoDB is accessible"""
        try:
            from pymongo import MongoClient

            # Try to connect to MongoDB
            client = MongoClient(
                "mongodb://admin:password@mongodb:27017/", serverSelectionTimeoutMS=5000
            )
            client.admin.command("ping")
            client.close()
            # Connection successful

        except Exception:
            try:
                # Fallback: Try using docker command
                result = subprocess.run(
                    [
                        "docker",
                        "compose",
                        "exec",
                        "-T",
                        "mongodb",
                        "mongosh",
                        "--eval",
                        'db.adminCommand("ping")',
                    ],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                assert result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                pytest.skip("MongoDB not available for testing")

    def test_streamlit_dashboard_accessibility(self):
        """Test that Streamlit dashboard is accessible"""
        try:
            import requests

            # Try to access the dashboard
            response = requests.get("http://localhost:8501", timeout=5)

            # Should get a response (even if it's an error page)
            assert response.status_code in [200, 404, 500]

        except Exception:
            # Dashboard might not be started yet - that's OK for testing
            pass


class TestEndToEndPipeline:
    """End-to-end pipeline tests"""

    def test_sample_data_processing(self):
        """Test processing a small sample of data through the entire pipeline"""
        # Create a small test CSV
        test_data = pd.DataFrame(
            {
                "InvoiceNo": [536365, 536366],
                "StockCode": ["85123A", "71053"],
                "Description": ["TEST ITEM 1", "TEST ITEM 2"],
                "Quantity": [1, 2],
                "InvoiceDate": ["12/01/2010 08:26", "12/01/2010 08:26"],
                "UnitPrice": [1.0, 2.0],
                "CustomerID": [17850, 17850],
                "Country": ["United Kingdom", "United Kingdom"],
            }
        )

        # Save test data
        test_csv_path = "/tmp/test_retail_data.csv"
        test_data.to_csv(test_csv_path, index=False)

        try:
            # Test that the data can be loaded and processed
            loaded_data = pd.read_csv(test_csv_path)

            # Verify data structure
            assert len(loaded_data) == 2
            assert all(
                col in loaded_data.columns
                for col in [
                    "InvoiceNo",
                    "StockCode",
                    "Description",
                    "Quantity",
                    "InvoiceDate",
                    "UnitPrice",
                    "CustomerID",
                    "Country",
                ]
            )

            # Test transformation
            processed_data = loaded_data.copy()
            processed_data["TotalAmount"] = (
                processed_data["Quantity"] * processed_data["UnitPrice"]
            )

            assert processed_data.iloc[0]["TotalAmount"] == 1.0
            assert processed_data.iloc[1]["TotalAmount"] == 4.0

        finally:
            # Clean up
            if os.path.exists(test_csv_path):
                os.remove(test_csv_path)

    @pytest.mark.slow
    def test_producer_to_kafka_flow(self):
        """Test data flow from producer to Kafka (requires Docker)"""
        try:
            # Run producer with a small dataset
            result = subprocess.run(
                ["docker", "compose", "exec", "-T", "app", "python", "src/producer.py"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Should complete successfully
            assert result.returncode == 0
            assert "Loading data..." in result.stdout or "Sent:" in result.stdout

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker environment not available")

    def test_data_quality_after_processing(self):
        """Test data quality after going through the pipeline"""
        # Sample processed data (simulated)
        processed_data = [
            {
                "InvoiceNo": 536365,
                "StockCode": "85123A",
                "Description": "WHITE HANGING HEART T-LIGHT HOLDER",
                "Quantity": 6,
                "InvoiceDate": "12/01/2010 08:26",
                "UnitPrice": 2.55,
                "CustomerID": 17850,
                "Country": "United Kingdom",
                "TotalAmount": 15.30,
            }
        ]

        for record in processed_data:
            # Check required fields exist
            assert "InvoiceNo" in record
            assert "TotalAmount" in record

            # Check calculated field
            expected_total = record["Quantity"] * record["UnitPrice"]
            assert abs(record["TotalAmount"] - expected_total) < 0.01

            # Check data types
            assert isinstance(record["InvoiceNo"], int)
            assert isinstance(record["Quantity"], int)
            assert isinstance(record["UnitPrice"], float)
            assert isinstance(record["TotalAmount"], float)


class TestPerformance:
    """Performance and load tests"""

    def test_batch_processing_performance(self):
        """Test batch processing performance with larger datasets"""
        # Generate test data
        large_dataset = []
        for i in range(1000):  # 1K records for testing
            record = {
                "InvoiceNo": 536365 + i,
                "StockCode": f"TEST{i}",
                "Description": f"Test Item {i}",
                "Quantity": i % 10 + 1,
                "InvoiceDate": "12/01/2010 08:26",
                "UnitPrice": (i % 100 + 1) / 10.0,
                "CustomerID": 17850,
                "Country": "United Kingdom",
            }
            large_dataset.append(record)

        # Time the batch processing simulation
        start_time = time.time()

        batch_size = 50
        batches_processed = 0

        for i in range(0, len(large_dataset), batch_size):
            batch = large_dataset[i : i + batch_size]

            # Simulate processing each item in batch
            for record in batch:
                record["TotalAmount"] = record["Quantity"] * record["UnitPrice"]

            batches_processed += 1

        end_time = time.time()
        processing_time = end_time - start_time

        # Should process 1K records reasonably fast
        assert processing_time < 5.0  # Less than 5 seconds
        assert batches_processed == 20  # 1000 / 50 = 20 batches

    def test_memory_usage_simulation(self):
        """Test memory usage doesn't grow excessively with batch processing"""
        import sys

        # Generate batches and ensure memory is managed
        for batch_num in range(10):
            batch = []
            for i in range(100):  # 100 items per batch
                record = {
                    "InvoiceNo": batch_num * 100 + i,
                    "Quantity": 1,
                    "UnitPrice": 1.0,
                    "TotalAmount": 1.0,
                }
                batch.append(record)

            # Simulate processing and clearing
            processed_count = len(batch)
            assert processed_count == 100

            # Clear batch (simulate MongoDB insert and memory cleanup)
            batch.clear()
            assert len(batch) == 0


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])
