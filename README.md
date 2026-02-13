# 🛒 Retail Pipeline - Real-time Data Processing System

[![CI/CD Pipeline](https://github.com/PantelisTsagkas/retail_pipeline/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/PantelisTsagkas/retail_pipeline/actions)
[![Code Quality](https://github.com/PantelisTsagkas/retail_pipeline/workflows/Code%20Quality/badge.svg)](https://github.com/PantelisTsagkas/retail_pipeline/actions)
[![Tests](https://img.shields.io/badge/tests-21%2F23%20passing-green.svg)](https://github.com/PantelisTsagkas/retail_pipeline/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready real-time data processing pipeline for retail transaction analysis using Apache Kafka, MongoDB, and Streamlit.

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [Configuration](#-configuration)
- [Development](#-development)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Monitoring](#-monitoring)
- [API Reference](#-api-reference)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

- **Real-time Processing**: Streams retail transactions from CSV to Kafka to MongoDB
- **Interactive Dashboard**: Live Streamlit web interface with real-time analytics
- **Scalable Architecture**: Containerized microservices with Docker Compose
- **Production Ready**: Comprehensive testing (91% pass rate), CI/CD pipeline, and monitoring
- **MongoDB Authentication**: Secure database access with admin credentials
- **Code Quality**: Black formatting, isort imports, comprehensive linting
- **Performance Monitoring**: Built-in metrics collection and health checks
- **Multi-Environment**: Support for development, staging, and production deployments

## 🏗️ Architecture

```mermaid
graph LR
    A[CSV Data] --> B[Producer]
    B --> C[Kafka Topic]
    C --> D[Processor]
    D --> E[MongoDB]
    E --> F[Streamlit Dashboard]
    
    G[Zookeeper] --> C
    H[Health Checks] --> B
    H --> C
    H --> D
    H --> E
    H --> F
```

### Components

- **Producer** (`src/producer.py`): Reads CSV data and publishes to Kafka
- **Processor** (`src/test_processor.py`): Consumes Kafka messages and writes to MongoDB
- **Dashboard** (`src/dashboard.py`): Real-time Streamlit web application
- **Infrastructure**: Kafka, Zookeeper, MongoDB in Docker containers

## 🚀 Quick Start

### Prerequisites

- Docker (20.10+)
- Docker Compose (2.0+)
- Python 3.9+ (for local development)

### 1. Clone Repository

```bash
git clone https://github.com/PantelisTsagkas/retail_pipeline.git
cd retail_pipeline
```

### 2. Start Services

```bash
# Start all services
docker-compose up -d

# Check service health
./health-check.sh
```

### 3. Access Dashboard

Open your browser to [http://localhost:8501](http://localhost:8501) to view the real-time dashboard.

### 4. Process Data

```bash
# Run producer to load data
docker-compose exec app python src/producer.py

# Run processor to consume and store data
docker-compose exec app python src/test_processor.py
```

## 🔧 Components

### Producer (`src/producer.py`)
- Reads CSV data in configurable chunks
- Streams JSON messages to Kafka
- Handles large datasets (500K+ records)

### Processor (`src/test_processor.py`)
- Consumes messages from Kafka
- Applies business logic transformations
- Batch writes to MongoDB for efficiency

### Dashboard (`src/dashboard.py`)
- Real-time Streamlit web application
- Live metrics and visualizations
- MongoDB connection monitoring

## 📈 Performance

- **Throughput**: 1000+ messages/second
- **Latency**: <100ms end-to-end processing
- **Scalability**: Horizontal scaling via Docker replicas
- **Storage**: Handles 500K+ transaction records

## 🐳 Services

| Service | Port | Description |
|---------|------|-------------|
| Kafka | 9092 | Message broker |
| MongoDB | 27017 | Document database |
| Streamlit | 8501 | Analytics dashboard |
| Zookeeper | 2181 | Kafka coordination |
| Spark | 8080 | (Optional) Cluster UI |

## 🧪 Testing

### Test Coverage (21/23 tests passing - 91%)

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test suites
pytest tests/test_producer.py -v      # Producer tests
pytest tests/test_processor.py -v     # Processor tests  
pytest tests/test_integration.py -v   # Integration tests
```

### Test Categories
- **Unit Tests**: Producer, Processor components
- **Integration Tests**: End-to-end pipeline validation
- **Performance Tests**: Throughput and latency benchmarks
- **Docker Tests**: Container health and service connectivity

## 📝 Configuration

### Environment Variables
Create `.env` file with:
```env
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
MONGO_HOST=mongodb:27017
MONGO_DB=retail_db
MONGO_USERNAME=admin
MONGO_PASSWORD=password
KAFKA_TOPIC=retail-transactions
BATCH_SIZE=50
PROCESSING_DELAY=0.5
```

### MongoDB Authentication
- **Username**: `admin`
- **Password**: `password`
- **Connection String**: `mongodb://admin:password@mongodb:27017/`

## 🔍 Monitoring

### Built-in Monitoring Tools

#### Performance Monitor (`monitor.py`)
```bash
# Real-time performance monitoring
python3 monitor.py --duration 300 --interval 10

# Single metrics snapshot
python3 monitor.py --once

# Save metrics to file
python3 monitor.py --save metrics.jsonl
```

#### Health Check (`health-check.sh`)
```bash
# Comprehensive service health validation
./health-check.sh

# Verbose output with detailed diagnostics
./health-check.sh --verbose

# JSON output for monitoring systems
./health-check.sh --json
```

### Monitoring Features
- **System Metrics**: CPU, memory, disk usage
- **Pipeline Metrics**: Message throughput, processing rates
- **Service Health**: Docker containers, Kafka, MongoDB connectivity
- **Real-time Dashboard**: Live transaction analytics

## 🚢 Production Deployment

### Automated Deployment (`deploy.sh`)
```bash
# Deploy to development
./deploy.sh -e development deploy

# Deploy to production with testing
./deploy.sh -e production -t deploy

# Check deployment status
./deploy.sh -e production status

# Rollback if needed
./deploy.sh -e production rollback
```

### CI/CD Pipeline (GitHub Actions)
- **Lint & Format**: Black, isort, flake8, mypy
- **Unit Tests**: 91% pass rate with coverage reports
- **Docker Tests**: Multi-service integration validation
- **Security Scans**: Safety, bandit, Docker Scout
- **Performance Tests**: Automated benchmarking
- **Automated Deployment**: Docker Hub publishing

### Multi-Environment Support
- **Development**: Full debugging, local data
- **Staging**: Production-like testing environment  
- **Production**: Optimized performance, security hardened

## 🛠️ Development

### Local Development Setup
```bash
# Clone repository
git clone https://github.com/PantelisTsagkas/retail_pipeline.git
cd retail_pipeline

# Set up Python environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Code formatting & linting
black src/ tests/
isort src/ tests/
flake8 src/ tests/
```

### Development Workflow
1. **Code**: Write features with comprehensive tests
2. **Format**: Auto-format with Black and isort
3. **Test**: Run pytest suite (aim for >90% pass rate)
4. **Commit**: Use conventional commit messages
5. **Push**: CI/CD pipeline validates automatically

### Data Pipeline Flow
1. **Ingestion**: CSV → Producer → Kafka
2. **Processing**: Kafka → Processor → Transformations
3. **Storage**: Processed data → MongoDB
4. **Analytics**: MongoDB → Dashboard → Insights

## 📚 API Reference

### Producer API
```python
from src.producer import RetailProducer

producer = RetailProducer('data/retail.csv')
producer.stream_data(batch_size=1000)
```

### Processor API  
```python
from src.test_processor import RetailProcessor

processor = RetailProcessor()
processor.start_processing()
```

## 🔒 Security

- Container network isolation
- No exposed credentials in code
- Environment-based configuration
- Health check endpoints only

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 🆘 Troubleshooting

### Common Issues

**Dashboard not loading?**
```bash
docker-compose ps  # Check if all services are running
docker-compose logs app  # Check application logs
```

**No data in dashboard?**
```bash
# Check MongoDB authentication and data
docker-compose exec mongodb mongosh retail_db -u admin -p password
# Then in mongosh: db.transactions.countDocuments({})

# Restart processor if needed
docker-compose restart app
```

**Kafka connection issues?**
```bash
# Restart services
docker-compose restart kafka zookeeper
```

## 📞 Support

- Create an issue for bugs/features
- Check existing issues and discussions
- Update documentation for improvements

---

**Built with ❤️ for real-time analytics**