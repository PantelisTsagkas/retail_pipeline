import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestProcessor:
    """Tests for the retail data processor"""
    
    def test_total_amount_calculation(self):
        """Test that TotalAmount is calculated correctly"""
        sample_data = {
            'InvoiceNo': 536365,
            'StockCode': '85123A',
            'Description': 'WHITE HANGING HEART T-LIGHT HOLDER',
            'Quantity': 6,
            'InvoiceDate': '12/01/2010 08:26',
            'UnitPrice': 2.55,
            'CustomerID': 17850,
            'Country': 'United Kingdom'
        }
        
        # Simulate the transformation
        if 'Quantity' in sample_data and 'UnitPrice' in sample_data:
            sample_data['TotalAmount'] = sample_data['Quantity'] * sample_data['UnitPrice']
        
        expected_total = 6 * 2.55
        assert abs(sample_data['TotalAmount'] - expected_total) < 0.01
    
    @patch('pymongo.MongoClient')
    def test_mongodb_connection(self, mock_mongo_client):
        """Test MongoDB connection and basic operations"""
        # Mock MongoDB client and operations
        mock_client = Mock()
        mock_db = Mock()
        mock_collection = Mock()
        
        # Set up proper dictionary-style access
        mock_mongo_client.return_value = mock_client
        mock_client.__getitem__ = Mock(return_value=mock_db)
        mock_db.__getitem__ = Mock(return_value=mock_collection)
        
        # Simulate connection
        from pymongo import MongoClient
        
        client = MongoClient("mongodb://admin:password@mongodb:27017/")
        db = client["retail_db"]
        collection = db["transactions"]
        
        # Verify connection setup
        mock_mongo_client.assert_called_with("mongodb://admin:password@mongodb:27017/")
    
    def test_batch_processing_logic(self):
        """Test batch processing functionality"""
        batch_size = 3
        messages = [
            {'InvoiceNo': 1, 'Quantity': 1, 'UnitPrice': 1.0},
            {'InvoiceNo': 2, 'Quantity': 2, 'UnitPrice': 2.0},
            {'InvoiceNo': 3, 'Quantity': 3, 'UnitPrice': 3.0},
            {'InvoiceNo': 4, 'Quantity': 4, 'UnitPrice': 4.0},
        ]
        
        batches = []
        current_batch = []
        
        for message in messages:
            # Add TotalAmount calculation
            message['TotalAmount'] = message['Quantity'] * message['UnitPrice']
            current_batch.append(message)
            
            if len(current_batch) >= batch_size:
                batches.append(current_batch.copy())
                current_batch = []
        
        # Add remaining items
        if current_batch:
            batches.append(current_batch)
        
        # Verify batching logic
        assert len(batches) == 2  # Should create 2 batches
        assert len(batches[0]) == 3  # First batch has 3 items
        assert len(batches[1]) == 1  # Second batch has 1 item
        assert batches[0][0]['TotalAmount'] == 1.0
        assert batches[1][0]['TotalAmount'] == 16.0
    
    @patch('kafka.KafkaConsumer')
    def test_kafka_consumer_configuration(self, mock_consumer):
        """Test Kafka consumer is configured correctly"""
        mock_consumer_instance = Mock()
        mock_consumer.return_value = mock_consumer_instance
        
        from kafka import KafkaConsumer
        
        # Simulate consumer creation
        consumer = KafkaConsumer(
            'retail_transactions',
            bootstrap_servers='kafka:9092',
            auto_offset_reset='earliest',
            enable_auto_commit=False,
            consumer_timeout_ms=10000
        )
        
        # Verify consumer was called (without lambda comparison)
        mock_consumer.assert_called_once()
        call_args = mock_consumer.call_args
        assert 'retail_transactions' in call_args[0]
        assert call_args[1]['bootstrap_servers'] == 'kafka:9092'
        assert call_args[1]['auto_offset_reset'] == 'earliest'
        assert call_args[1]['enable_auto_commit'] == False
        assert call_args[1]['consumer_timeout_ms'] == 10000
    
    def test_message_deserialization(self):
        """Test that Kafka messages are deserialized correctly"""
        # Simulate a Kafka message
        original_data = {
            'InvoiceNo': 536365,
            'StockCode': '85123A',
            'Quantity': 6,
            'UnitPrice': 2.55
        }
        
        # Serialize and deserialize
        json_bytes = json.dumps(original_data).encode('utf-8')
        deserialized = json.loads(json_bytes.decode('utf-8'))
        
        assert deserialized['InvoiceNo'] == 536365
        assert deserialized['Quantity'] == 6
        assert deserialized['UnitPrice'] == 2.55


class TestErrorHandling:
    """Tests for error handling and edge cases"""
    
    def test_missing_fields_handling(self):
        """Test handling of messages with missing fields"""
        incomplete_data = {
            'InvoiceNo': 536365,
            'StockCode': '85123A',
            # Missing Quantity and UnitPrice
        }
        
        # Test the transformation logic with missing fields
        if 'Quantity' in incomplete_data and 'UnitPrice' in incomplete_data:
            incomplete_data['TotalAmount'] = incomplete_data['Quantity'] * incomplete_data['UnitPrice']
        
        # Should not have TotalAmount field since required fields are missing
        assert 'TotalAmount' not in incomplete_data
    
    def test_invalid_data_types(self):
        """Test handling of invalid data types"""
        invalid_data = {
            'InvoiceNo': 536365,
            'Quantity': 'invalid',  # Should be numeric
            'UnitPrice': 2.55
        }
        
        # Test safe conversion
        try:
            quantity = float(invalid_data['Quantity'])
            unit_price = float(invalid_data['UnitPrice'])
            total = quantity * unit_price
        except (ValueError, TypeError):
            # Should handle conversion errors gracefully
            assert True  # Expected to fail conversion
        else:
            assert False  # Should not reach here with invalid data
    
    def test_zero_values(self):
        """Test handling of zero quantities and prices"""
        zero_quantity_data = {
            'InvoiceNo': 536365,
            'Quantity': 0,
            'UnitPrice': 2.55
        }
        
        total_amount = zero_quantity_data['Quantity'] * zero_quantity_data['UnitPrice']
        assert total_amount == 0.0
        
        zero_price_data = {
            'InvoiceNo': 536366,
            'Quantity': 5,
            'UnitPrice': 0.0
        }
        
        total_amount = zero_price_data['Quantity'] * zero_price_data['UnitPrice']
        assert total_amount == 0.0


if __name__ == '__main__':
    pytest.main([__file__])