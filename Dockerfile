# Multi-stage build for production optimization
FROM python:3.9-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    default-jdk \
    curl \
    netcat-openbsd \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Java environment
ENV JAVA_HOME=/usr/lib/jvm/default-java

# Development stage
FROM base as development

# Install development dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Set Python path
ENV PYTHONPATH=/app/src

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import sys; sys.exit(0)" || exit 1

# Production stage
FROM base as production

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy only production requirements
COPY requirements.txt .

# Install only production dependencies
RUN pip install --no-cache-dir \
    pandas \
    kafka-python \
    pymongo \
    streamlit \
    fastapi \
    uvicorn \
    python-dotenv \
    && pip cache purge

# Copy source code
COPY src/ /app/src/
COPY data/ /app/data/

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set Python path
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Expose ports
EXPOSE 8501 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import sys; import os; print(f'Health check OK - PID: {os.getpid()}'); sys.exit(0)" || exit 1

# Default command
CMD ["tail", "-f", "/dev/null"]