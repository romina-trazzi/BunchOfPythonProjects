#!/bin/bash

# Deploy script for LangChain RAG Engine
# Usage: ./deploy.sh [environment]
# Environment: dev, staging, prod (default: dev)

set -e

ENVIRONMENT=${1:-dev}
PROJECT_NAME="langchain-rag"

echo "🚀 Deploying LangChain RAG Engine to $ENVIRONMENT environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    if [ -f ".env.${ENVIRONMENT}" ]; then
        print_status "Copying .env.${ENVIRONMENT} to .env"
        cp ".env.${ENVIRONMENT}" .env
    else
        print_error ".env file not found. Please create one from .env.production template."
        exit 1
    fi
fi

# Validate required environment variables
print_status "Validating environment variables..."
source .env

if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your_production_anthropic_api_key_here" ]; then
    print_error "ANTHROPIC_API_KEY is not set or using default value. Please configure it in .env file."
    exit 1
fi

print_status "Environment variables validated ✅"

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p data/production
mkdir -p logs
mkdir -p ssl

# Set proper permissions
chmod 755 data/production
chmod 755 logs

# Build and start services
print_status "Building Docker images..."
docker-compose build --no-cache

print_status "Starting services..."
docker-compose up -d

# Wait for services to be healthy
print_status "Waiting for services to be healthy..."
sleep 10

# Check health
print_status "Checking service health..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        print_status "RAG Engine is healthy ✅"
        break
    fi
    
    if [ $i -eq 30 ]; then
        print_error "RAG Engine failed to start properly"
        docker-compose logs rag-engine
        exit 1
    fi
    
    print_warning "Waiting for RAG Engine to be ready... ($i/30)"
    sleep 2
done

# Show running services
print_status "Deployment completed! Services status:"
docker-compose ps

print_status "Service URLs:"
echo "  - RAG Engine API: http://localhost:8000"
echo "  - Health Check: http://localhost:8000/health"
echo "  - API Documentation: http://localhost:8000/docs"

if [ "$ENVIRONMENT" = "prod" ]; then
    print_warning "Production deployment notes:"
    echo "  1. Configure SSL certificates in ./ssl/ directory"
    echo "  2. Update nginx.conf with your domain name"
    echo "  3. Set up proper DNS records"
    echo "  4. Configure firewall rules"
    echo "  5. Set up monitoring and alerting"
    echo "  6. Configure automated backups"
fi

print_status "Deployment completed successfully! 🎉"