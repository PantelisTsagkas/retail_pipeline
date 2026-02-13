#!/usr/bin/env python3
"""
Performance Monitor for Retail Pipeline
Monitors system metrics, pipeline throughput, and service health
"""

import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import argparse
import sys
import os

try:
    import psutil
    from pymongo import MongoClient
    from kafka import KafkaConsumer, TopicPartition
    from kafka.admin import KafkaAdminClient, NewTopic
except ImportError as e:
    print(f"❌ Missing required dependency: {e}")
    print("💡 Install with: pip install psutil pymongo kafka-python")
    sys.exit(1)

# Configuration
KAFKA_HOST = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost:27017')
MONGO_DB = os.getenv('MONGO_DB', 'retail_db')
TOPIC_NAME = os.getenv('KAFKA_TOPIC', 'retail-transactions')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitors performance metrics for the retail pipeline"""
    
    def __init__(self):
        """Initialize monitoring connections"""
        self.mongo_client = None
        self.kafka_consumer = None
        self.metrics_history = []
        
    def connect_services(self) -> bool:
        """Establish connections to Kafka and MongoDB"""
        try:
            # Connect to MongoDB
            self.mongo_client = MongoClient(f'mongodb://{MONGO_HOST}')
            self.mongo_client.admin.command('ping')
            logger.info("✅ Connected to MongoDB")
            
            # Connect to Kafka
            self.kafka_consumer = KafkaConsumer(
                bootstrap_servers=[KAFKA_HOST],
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                consumer_timeout_ms=1000
            )
            logger.info("✅ Connected to Kafka")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    def get_system_metrics(self) -> Dict:
        """Get system resource usage metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Network I/O
            net_io = psutil.net_io_counters()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3),
                'network_bytes_sent': net_io.bytes_sent,
                'network_bytes_recv': net_io.bytes_recv
            }
            
        except Exception as e:
            logger.error(f"❌ System metrics error: {e}")
            return {}
    
    def get_mongodb_metrics(self) -> Dict:
        """Get MongoDB performance metrics"""
        try:
            db = self.mongo_client[MONGO_DB]
            collection = db.transactions
            
            # Document count and recent activity
            total_docs = collection.estimated_document_count()
            
            # Recent documents (last 5 minutes)
            five_min_ago = datetime.now() - timedelta(minutes=5)
            recent_docs = 0
            
            # Try to count recent documents if possible
            try:
                # This assumes documents have a timestamp field or _id ObjectId
                recent_docs = collection.count_documents({
                    '_id': {'$gte': time.time() - 300}  # Last 5 minutes
                })
            except:
                # If timestamp filtering fails, use estimated count
                recent_docs = 0
            
            # Database stats
            db_stats = db.command("dbStats")
            
            return {
                'total_documents': total_docs,
                'recent_documents_5min': recent_docs,
                'database_size_mb': db_stats.get('dataSize', 0) / (1024**2),
                'index_size_mb': db_stats.get('indexSize', 0) / (1024**2),
                'collections_count': db_stats.get('collections', 0)
            }
            
        except Exception as e:
            logger.error(f"❌ MongoDB metrics error: {e}")
            return {}
    
    def get_kafka_metrics(self) -> Dict:
        """Get Kafka performance metrics"""
        try:
            # Get topic partition info
            admin_client = KafkaAdminClient(bootstrap_servers=[KAFKA_HOST])
            
            # Get consumer group info (if consumer is active)
            partitions = self.kafka_consumer.partitions_for_topic(TOPIC_NAME)
            if not partitions:
                return {'topic_partitions': 0, 'messages_available': 0}
            
            total_messages = 0
            for partition in partitions:
                tp = TopicPartition(TOPIC_NAME, partition)
                try:
                    # Get high watermark (latest offset)
                    high_watermark = self.kafka_consumer.end_offsets([tp])[tp]
                    total_messages += high_watermark
                except:
                    pass
            
            return {
                'topic_partitions': len(partitions) if partitions else 0,
                'total_messages': total_messages,
                'topic_name': TOPIC_NAME
            }
            
        except Exception as e:
            logger.error(f"❌ Kafka metrics error: {e}")
            return {}
    
    def calculate_throughput(self) -> Dict:
        """Calculate pipeline throughput metrics"""
        if len(self.metrics_history) < 2:
            return {'docs_per_second': 0, 'messages_per_second': 0}
        
        current = self.metrics_history[-1]
        previous = self.metrics_history[-2]
        
        time_diff = (
            datetime.fromisoformat(current['timestamp']) - 
            datetime.fromisoformat(previous['timestamp'])
        ).total_seconds()
        
        if time_diff <= 0:
            return {'docs_per_second': 0, 'messages_per_second': 0}
        
        # Calculate rates
        doc_diff = (
            current.get('mongodb', {}).get('total_documents', 0) - 
            previous.get('mongodb', {}).get('total_documents', 0)
        )
        
        msg_diff = (
            current.get('kafka', {}).get('total_messages', 0) - 
            previous.get('kafka', {}).get('total_messages', 0)
        )
        
        return {
            'docs_per_second': doc_diff / time_diff,
            'messages_per_second': msg_diff / time_diff
        }
    
    def collect_metrics(self) -> Dict:
        """Collect all performance metrics"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'system': self.get_system_metrics(),
            'mongodb': self.get_mongodb_metrics(),
            'kafka': self.get_kafka_metrics()
        }
        
        # Add throughput calculations
        metrics['throughput'] = self.calculate_throughput()
        
        # Store in history (keep last 100 entries)
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > 100:
            self.metrics_history.pop(0)
        
        return metrics
    
    def print_metrics(self, metrics: Dict):
        """Print metrics in a formatted way"""
        print("\n" + "="*60)
        print(f"📊 RETAIL PIPELINE PERFORMANCE - {metrics['timestamp']}")
        print("="*60)
        
        # System metrics
        system = metrics.get('system', {})
        if system:
            print(f"\n🖥️  SYSTEM RESOURCES:")
            print(f"   CPU Usage:      {system.get('cpu_percent', 0):.1f}%")
            print(f"   Memory Usage:   {system.get('memory_percent', 0):.1f}%")
            print(f"   Memory Free:    {system.get('memory_available_gb', 0):.2f} GB")
            print(f"   Disk Usage:     {system.get('disk_percent', 0):.1f}%")
            print(f"   Disk Free:      {system.get('disk_free_gb', 0):.2f} GB")
        
        # MongoDB metrics
        mongodb = metrics.get('mongodb', {})
        if mongodb:
            print(f"\n💾 MONGODB:")
            print(f"   Total Documents: {mongodb.get('total_documents', 0):,}")
            print(f"   Recent (5min):   {mongodb.get('recent_documents_5min', 0):,}")
            print(f"   Database Size:   {mongodb.get('database_size_mb', 0):.2f} MB")
            print(f"   Index Size:      {mongodb.get('index_size_mb', 0):.2f} MB")
        
        # Kafka metrics
        kafka = metrics.get('kafka', {})
        if kafka:
            print(f"\n📡 KAFKA:")
            print(f"   Topic:           {kafka.get('topic_name', 'N/A')}")
            print(f"   Partitions:      {kafka.get('topic_partitions', 0)}")
            print(f"   Total Messages:  {kafka.get('total_messages', 0):,}")
        
        # Throughput metrics
        throughput = metrics.get('throughput', {})
        if throughput:
            print(f"\n⚡ THROUGHPUT:")
            print(f"   Docs/Second:     {throughput.get('docs_per_second', 0):.2f}")
            print(f"   Messages/Second: {throughput.get('messages_per_second', 0):.2f}")
        
        print("\n" + "="*60)
    
    def save_metrics(self, metrics: Dict, filename: str):
        """Save metrics to file"""
        try:
            with open(filename, 'a') as f:
                f.write(json.dumps(metrics) + '\n')
        except Exception as e:
            logger.error(f"❌ Failed to save metrics: {e}")
    
    def monitor(self, duration: int = 60, interval: int = 10, save_file: Optional[str] = None):
        """Run continuous monitoring"""
        if not self.connect_services():
            return False
        
        print(f"🚀 Starting performance monitoring...")
        print(f"   Duration: {duration} seconds")
        print(f"   Interval: {interval} seconds")
        if save_file:
            print(f"   Saving to: {save_file}")
        print()
        
        start_time = time.time()
        try:
            while time.time() - start_time < duration:
                metrics = self.collect_metrics()
                self.print_metrics(metrics)
                
                if save_file:
                    self.save_metrics(metrics, save_file)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
        
        finally:
            if self.mongo_client:
                self.mongo_client.close()
            if self.kafka_consumer:
                self.kafka_consumer.close()
        
        return True

def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(description='Monitor Retail Pipeline Performance')
    parser.add_argument('--duration', '-d', type=int, default=60,
                       help='Monitoring duration in seconds (default: 60)')
    parser.add_argument('--interval', '-i', type=int, default=10,
                       help='Metrics collection interval in seconds (default: 10)')
    parser.add_argument('--save', '-s', type=str,
                       help='Save metrics to file (JSONL format)')
    parser.add_argument('--once', action='store_true',
                       help='Collect metrics once and exit')
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor()
    
    if args.once:
        if monitor.connect_services():
            metrics = monitor.collect_metrics()
            monitor.print_metrics(metrics)
            if args.save:
                monitor.save_metrics(metrics, args.save)
    else:
        monitor.monitor(
            duration=args.duration,
            interval=args.interval,
            save_file=args.save
        )

if __name__ == '__main__':
    main()