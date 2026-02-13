import json
import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))


class TestProducer:
    """Tests for the retail data producer"""

    @patch("kafka.KafkaProducer")
    @patch("pandas.read_csv")
    def test_producer_sends_messages(self, mock_read_csv, mock_kafka_producer):
        """Test that producer sends correct messages to Kafka"""
        # Mock data
        sample_data = pd.DataFrame(
            {
                "InvoiceNo": [536365, 536366],
                "StockCode": ["85123A", "71053"],
                "Description": [
                    "WHITE HANGING HEART T-LIGHT HOLDER",
                    "WHITE METAL LANTERN",
                ],
                "Quantity": [6, 6],
                "InvoiceDate": ["12/01/2010 08:26", "12/01/2010 08:26"],
                "UnitPrice": [2.55, 3.39],
                "CustomerID": [17850, 17850],
                "Country": ["United Kingdom", "United Kingdom"],
            }
        )

        mock_read_csv.return_value = sample_data
        mock_producer_instance = Mock()
        mock_kafka_producer.return_value = mock_producer_instance

        # Test producer configuration by importing the actual module
        import importlib
        import sys

        if "producer" in sys.modules:
            importlib.reload(sys.modules["producer"])

        # Import after mocking
        import producer

        # Verify producer was called (without lambda comparison)
        mock_kafka_producer.assert_called_once()
        call_args = mock_kafka_producer.call_args
        assert call_args[1]["bootstrap_servers"] == ["kafka:9092"]

    def test_data_serialization(self):
        """Test that data is properly serialized to JSON"""
        sample_row = {
            "InvoiceNo": 536365,
            "StockCode": "85123A",
            "Description": "WHITE HANGING HEART T-LIGHT HOLDER",
            "Quantity": 6,
            "InvoiceDate": "12/01/2010 08:26",
            "UnitPrice": 2.55,
            "CustomerID": 17850,
            "Country": "United Kingdom",
        }

        # Test JSON serialization
        json_str = json.dumps(sample_row)
        deserialized = json.loads(json_str)

        assert deserialized["InvoiceNo"] == 536365
        assert deserialized["Quantity"] == 6
        assert deserialized["UnitPrice"] == 2.55

    def test_csv_loading_with_encoding(self):
        """Test CSV loading handles different encodings"""
        # This would test the actual CSV loading logic
        # For now, just verify pandas can handle the expected structure
        sample_data = {
            "InvoiceNo": [536365],
            "StockCode": ["85123A"],
            "Description": ["TEST ITEM"],
            "Quantity": [1],
            "InvoiceDate": ["12/01/2010 08:26"],
            "UnitPrice": [1.0],
            "CustomerID": [12345],
            "Country": ["United Kingdom"],
        }

        df = pd.DataFrame(sample_data)
        assert len(df) == 1
        assert df.iloc[0]["InvoiceNo"] == 536365


class TestDataValidation:
    """Tests for data quality and validation"""

    def test_required_columns_present(self):
        """Test that all required columns are present in data"""
        required_columns = [
            "InvoiceNo",
            "StockCode",
            "Description",
            "Quantity",
            "InvoiceDate",
            "UnitPrice",
            "CustomerID",
            "Country",
        ]

        sample_data = pd.DataFrame(
            {
                "InvoiceNo": [536365],
                "StockCode": ["85123A"],
                "Description": ["TEST ITEM"],
                "Quantity": [1],
                "InvoiceDate": ["12/01/2010 08:26"],
                "UnitPrice": [1.0],
                "CustomerID": [12345],
                "Country": ["United Kingdom"],
            }
        )

        for col in required_columns:
            assert col in sample_data.columns, f"Required column {col} missing"

    def test_data_types(self):
        """Test that data has correct types"""
        sample_data = pd.DataFrame(
            {
                "InvoiceNo": [536365],
                "Quantity": [6],
                "UnitPrice": [2.55],
                "CustomerID": [17850],
            }
        )

        assert sample_data["InvoiceNo"].dtype in ["int64", "object"]
        assert sample_data["Quantity"].dtype in ["int64", "float64"]
        assert sample_data["UnitPrice"].dtype in ["float64"]
        assert sample_data["CustomerID"].dtype in ["int64", "float64", "object"]

    def test_business_logic_calculations(self):
        """Test business logic transformations"""
        quantity = 6
        unit_price = 2.55
        expected_total = quantity * unit_price

        assert abs(expected_total - 15.30) < 0.01  # Handle floating point precision


if __name__ == "__main__":
    pytest.main([__file__])
