#!/bin/bash

# FillTheWord MVP Quick Start Script
# This script sets up and runs the complete FillTheWord application

set -e

echo "🚀 Starting FillTheWord MVP Setup..."
echo "=================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p audio/{en,pt,es}/{word,sentence}
mkdir -p tts_models

# Build and start services
echo "🐳 Building and starting Docker containers..."
docker-compose up -d --build

echo "⏳ Waiting for services to be ready..."
sleep 10

# Wait for database to be ready
echo "🗄️  Waiting for database..."
until docker-compose exec -T db pg_isready -U ftw_user -d filltheword; do
    echo "   Database not ready, waiting..."
    sleep 2
done

echo "✅ Database is ready!"

# Run database migrations (when available)
echo "🔄 Running database migrations..."
# docker-compose exec -T api alembic upgrade head || echo "   Migrations not available yet"

# Seed the database
echo "🌱 Seeding database with initial data..."
docker-compose exec -T api python /app/../scripts/seed_data.py

# Check service health
echo "🏥 Checking service health..."
echo "   API Health:"
docker-compose exec -T api curl -f http://localhost:8000/health || echo "   API not responding yet"

echo "   TTS Health:"
docker-compose exec -T tts curl -f http://localhost:8001/health || echo "   TTS not responding yet"

echo ""
echo "🎉 FillTheWord MVP is now running!"
echo "=================================="
echo "🌐 Frontend:    http://localhost:3000"
echo "📚 API Docs:    http://localhost:8000/docs"
echo "🔊 TTS API:     http://localhost:8001/health"
echo "🗄️  Database:   localhost:5432 (user: ftw_user, db: filltheword)"
echo ""
echo "💡 Quick Tips:"
echo "   - Use username 'demo' for testing"
echo "   - Press Ctrl+C to stop all services"
echo "   - Run 'docker-compose logs -f' to see logs"
echo "   - Run 'docker-compose down' to stop services"
echo ""
echo "🔧 Development:"
echo "   - Frontend code: ./frontend/src/"
echo "   - API code:     ./api/app/"
echo "   - TTS code:     ./tts/app/"
echo "   - Audio cache:  ./audio/"
echo ""
echo "Happy learning! 📖✨"
