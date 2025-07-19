#!/bin/bash

# Production deployment script for SaaS LLM Web UI
# Usage: ./scripts/deploy.sh [environment]

set -e

ENVIRONMENT=${1:-production}
PROJECT_NAME="fastapi-llm-app"

echo "Deploying $PROJECT_NAME to $ENVIRONMENT environment"

# Check requirements
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed."; exit 1; }

# Set environment variables
export ENVIRONMENT=$ENVIRONMENT
export COMPOSE_PROJECT_NAME=$PROJECT_NAME

# Load environment file
if [ -f ".env.$ENVIRONMENT" ]; then
    export $(cat .env.$ENVIRONMENT | xargs)
    echo "✅ Loaded environment from .env.$ENVIRONMENT"
elif [ -f ".env" ]; then
    export $(cat .env | xargs)
    echo "✅ Loaded environment from .env"
else
    echo "❌ No environment file found"
    exit 1
fi

# Validate required environment variables
required_vars=("SECRET_KEY" "DATABASE_URL")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable $var is not set"
        exit 1
    fi
done

# Create necessary directories
mkdir -p data/faiss_index
mkdir -p uploads
mkdir -p logs

echo "Created necessary directories"

# Build and deploy
echo "Building Docker images..."
docker-compose build --no-cache

echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Health check
echo "Running health checks..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ Application is healthy"
        break
    else
        echo "⏳ Attempt $attempt/$max_attempts - waiting for application..."
        sleep 5
        ((attempt++))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ Application failed to start properly"
    docker-compose logs app
    exit 1
fi

# Setup Ollama models (if Ollama is enabled)
if docker-compose ps ollama | grep -q "Up"; then
    echo "Setting up Ollama models..."
    docker-compose exec ollama ollama pull llama3.1 || echo "⚠️  Could not pull Ollama model automatically"
fi

echo "Deployment completed successfully!"
echo "Application is available at: http://localhost:8000"
echo "Monitor logs with: docker-compose logs -f"
echo "Stop services with: docker-compose down"

# Show running services
echo "Running services:"
docker-compose ps
