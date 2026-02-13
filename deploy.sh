#!/bin/bash
set -e

# Production Deployment Script for Retail Pipeline
# Handles deployment to different environments with proper validation

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="retail-pipeline"
DEFAULT_ENV="development"
DOCKER_REGISTRY=${DOCKER_REGISTRY:-""}
VERSION=${VERSION:-$(date +%Y%m%d-%H%M%S)}

# Help function
show_help() {
    cat << EOF
🚀 Retail Pipeline Deployment Script

USAGE:
    ./deploy.sh [OPTIONS] COMMAND

COMMANDS:
    build           Build Docker images
    deploy          Deploy to environment
    test            Run health checks
    logs            Show service logs
    status          Show deployment status
    cleanup         Clean up resources
    help            Show this help

OPTIONS:
    -e, --env ENV       Target environment (development/staging/production)
    -v, --version VER   Version tag for images
    -r, --registry REG  Docker registry URL
    -f, --file FILE     Docker compose file
    -t, --test         Run tests after deployment
    -d, --detach       Run in detached mode
    -p, --pull         Pull latest images before deployment
    --no-cache         Build without cache
    --dry-run          Show commands without executing

EXAMPLES:
    ./deploy.sh build
    ./deploy.sh -e production deploy
    ./deploy.sh -e staging -t deploy
    ./deploy.sh logs kafka
    ./deploy.sh status

EOF
}

# Logging functions
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Validate requirements
check_requirements() {
    log_info "Checking deployment requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check required files
    local required_files=(
        "docker-compose.yml"
        "Dockerfile"
        "requirements.txt"
        "src/producer.py"
        "src/test_processor.py"
        "src/dashboard.py"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$SCRIPT_DIR/$file" ]]; then
            log_error "Required file missing: $file"
            exit 1
        fi
    done
    
    log_success "All requirements satisfied"
}

# Environment-specific configuration
setup_environment() {
    local env=$1
    
    log_info "Setting up environment: $env"
    
    case $env in
        "development")
            export COMPOSE_FILE="docker-compose.yml"
            export KAFKA_HEAP_OPTS="-Xmx256m -Xms256m"
            export MONGODB_MEMORY_LIMIT="256m"
            ;;
        "staging")
            export COMPOSE_FILE="docker-compose.yml:docker-compose.staging.yml"
            export KAFKA_HEAP_OPTS="-Xmx512m -Xms512m"
            export MONGODB_MEMORY_LIMIT="512m"
            ;;
        "production")
            export COMPOSE_FILE="docker-compose.yml:docker-compose.prod.yml"
            export KAFKA_HEAP_OPTS="-Xmx1g -Xms1g"
            export MONGODB_MEMORY_LIMIT="1g"
            ;;
        *)
            log_error "Unknown environment: $env"
            exit 1
            ;;
    esac
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    cd "$SCRIPT_DIR"
    
    # Build main application image
    local image_tag="${PROJECT_NAME}:${VERSION}"
    if [[ -n "$DOCKER_REGISTRY" ]]; then
        image_tag="${DOCKER_REGISTRY}/${image_tag}"
    fi
    
    if [[ "$NO_CACHE" == "true" ]]; then
        docker build --no-cache -t "$image_tag" .
    else
        docker build -t "$image_tag" .
    fi
    
    # Also tag as latest
    docker tag "$image_tag" "${PROJECT_NAME}:latest"
    if [[ -n "$DOCKER_REGISTRY" ]]; then
        docker tag "$image_tag" "${DOCKER_REGISTRY}/${PROJECT_NAME}:latest"
    fi
    
    log_success "Images built successfully: $image_tag"
}

# Deploy services
deploy_services() {
    log_info "Deploying services to $ENVIRONMENT environment..."
    
    cd "$SCRIPT_DIR"
    
    # Pull images if requested
    if [[ "$PULL_IMAGES" == "true" ]]; then
        log_info "Pulling latest images..."
        docker-compose pull
    fi
    
    # Start services
    if [[ "$DETACH" == "true" ]]; then
        docker-compose up -d
    else
        docker-compose up
    fi
    
    log_success "Services deployed successfully"
}

# Run health checks
run_tests() {
    log_info "Running health checks..."
    
    # Wait for services to be ready
    log_info "Waiting for services to start..."
    sleep 30
    
    # Run health check script
    if [[ -f "$SCRIPT_DIR/health-check.sh" ]]; then
        bash "$SCRIPT_DIR/health-check.sh"
    else
        log_warning "Health check script not found, running basic checks..."
        
        # Basic connectivity tests
        docker-compose exec -T app python -c "
from kafka import KafkaProducer
from pymongo import MongoClient
import sys

try:
    # Test Kafka
    producer = KafkaProducer(bootstrap_servers=['kafka:9092'])
    producer.close()
    print('✅ Kafka connection successful')
    
    # Test MongoDB
    client = MongoClient('mongodb://mongodb:27017')
    client.admin.command('ping')
    client.close()
    print('✅ MongoDB connection successful')
    
    sys.exit(0)
except Exception as e:
    print(f'❌ Health check failed: {e}')
    sys.exit(1)
"
    fi
    
    log_success "Health checks completed"
}

# Show service logs
show_logs() {
    local service=$1
    
    if [[ -n "$service" ]]; then
        log_info "Showing logs for service: $service"
        docker-compose logs -f "$service"
    else
        log_info "Showing logs for all services"
        docker-compose logs -f
    fi
}

# Show deployment status
show_status() {
    log_info "Deployment Status:"
    echo
    
    # Show running containers
    echo "📦 Running Containers:"
    docker-compose ps
    echo
    
    # Show resource usage
    echo "💾 Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
    echo
    
    # Show network info
    echo "🌐 Network Information:"
    docker-compose exec -T app python -c "
import socket
kafka_host = socket.gethostbyname('kafka')
mongo_host = socket.gethostbyname('mongodb')
print(f'Kafka IP: {kafka_host}')
print(f'MongoDB IP: {mongo_host}')
" 2>/dev/null || echo "Network information unavailable"
}

# Cleanup resources
cleanup() {
    log_info "Cleaning up resources..."
    
    # Stop and remove containers
    docker-compose down --volumes --remove-orphans
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes
    docker volume prune -f
    
    log_success "Cleanup completed"
}

# Main execution
main() {
    local command=""
    local service=""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            -r|--registry)
                DOCKER_REGISTRY="$2"
                shift 2
                ;;
            -f|--file)
                COMPOSE_FILE="$2"
                shift 2
                ;;
            -t|--test)
                RUN_TESTS="true"
                shift
                ;;
            -d|--detach)
                DETACH="true"
                shift
                ;;
            -p|--pull)
                PULL_IMAGES="true"
                shift
                ;;
            --no-cache)
                NO_CACHE="true"
                shift
                ;;
            --dry-run)
                DRY_RUN="true"
                shift
                ;;
            help)
                show_help
                exit 0
                ;;
            build|deploy|test|logs|status|cleanup)
                command="$1"
                shift
                ;;
            *)
                if [[ -z "$command" ]]; then
                    command="$1"
                else
                    service="$1"
                fi
                shift
                ;;
        esac
    done
    
    # Set defaults
    ENVIRONMENT=${ENVIRONMENT:-$DEFAULT_ENV}
    RUN_TESTS=${RUN_TESTS:-false}
    DETACH=${DETACH:-false}
    PULL_IMAGES=${PULL_IMAGES:-false}
    NO_CACHE=${NO_CACHE:-false}
    DRY_RUN=${DRY_RUN:-false}
    
    # Show configuration if dry run
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "🔍 Dry Run Configuration:"
        echo "  Environment: $ENVIRONMENT"
        echo "  Version: $VERSION"
        echo "  Registry: ${DOCKER_REGISTRY:-'none'}"
        echo "  Command: $command"
        echo "  Service: ${service:-'all'}"
        echo
        exit 0
    fi
    
    # Validate command
    if [[ -z "$command" ]]; then
        log_error "No command specified"
        show_help
        exit 1
    fi
    
    # Setup environment
    setup_environment "$ENVIRONMENT"
    
    # Execute command
    case $command in
        "build")
            check_requirements
            build_images
            ;;
        "deploy")
            check_requirements
            deploy_services
            if [[ "$RUN_TESTS" == "true" ]]; then
                run_tests
            fi
            ;;
        "test")
            run_tests
            ;;
        "logs")
            show_logs "$service"
            ;;
        "status")
            show_status
            ;;
        "cleanup")
            cleanup
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"