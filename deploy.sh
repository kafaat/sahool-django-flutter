#!/bin/bash

# GeoFarm Platform Deployment Script
# This script helps deploy the GeoFarm platform in different environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="development"
COMPOSE_FILE="docker-compose.yml"
SKIP_BUILD=false
SKIP_MIGRATIONS=false
VERBOSE=false

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
GeoFarm Platform Deployment Script

Usage: $0 [OPTIONS]

Options:
    -e, --environment    Set deployment environment (development/staging/production)
    -f, --compose-file   Docker compose file path (default: docker-compose.yml)
    -s, --skip-build     Skip building Docker images
    -m, --skip-migrations Skip database migrations
    -v, --verbose        Enable verbose output
    -h, --help           Show this help message

Examples:
    $0 --environment production
    $0 -e staging -f docker-compose.staging.yml
    $0 --skip-build --verbose

EOF
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            print_warning ".env file not found. Copying from .env.example"
            cp .env.example .env
            print_warning "Please update .env file with your configuration before continuing"
            exit 1
        else
            print_error ".env.example file not found. Please create .env file with required configuration."
            exit 1
        fi
    fi
    
    print_success "Prerequisites check completed"
}

# Function to load environment variables
load_environment() {
    print_status "Loading environment variables..."
    
    if [ -f .env ]; then
        export $(cat .env | grep -v '^#' | xargs)
        print_success "Environment variables loaded"
    else
        print_error ".env file not found"
        exit 1
    fi
}

# Function to build Docker images
build_images() {
    if [ "$SKIP_BUILD" = true ]; then
        print_warning "Skipping Docker image build"
        return
    fi
    
    print_status "Building Docker images..."
    
    if [ "$VERBOSE" = true ]; then
        docker-compose -f $COMPOSE_FILE build
    else
        docker-compose -f $COMPOSE_FILE build --quiet
    fi
    
    print_success "Docker images built successfully"
}

# Function to start infrastructure services
start_infrastructure() {
    print_status "Starting infrastructure services..."
    
    # Start database and cache services first
    if [ "$VERBOSE" = true ]; then
        docker-compose -f $COMPOSE_FILE up -d postgres redis influxdb
    else
        docker-compose -f $COMPOSE_FILE up -d postgres redis influxdb --quiet-pull
    fi
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    sleep 10
    
    # Check if database is ready
    if ! docker-compose -f $COMPOSE_FILE exec postgres pg_isready -U postgres &> /dev/null; then
        print_error "Database is not ready. Please check database logs."
        exit 1
    fi
    
    print_success "Infrastructure services started"
}

# Function to run database migrations
run_migrations() {
    if [ "$SKIP_MIGRATIONS" = true ]; then
        print_warning "Skipping database migrations"
        return
    fi
    
    print_status "Running database migrations..."
    
    # Create databases if they don't exist
    docker-compose -f $COMPOSE_FILE exec postgres psql -U postgres -c "
        CREATE DATABASE IF NOT EXISTS geofarm_users;
        CREATE DATABASE IF NOT EXISTS geofarm_notifications;
        CREATE DATABASE IF NOT EXISTS geofarm_weather;
        CREATE DATABASE IF NOT EXISTS geofarm_crops;
        CREATE DATABASE IF NOT EXISTS geofarm_recommendations;
        CREATE DATABASE IF NOT EXISTS geofarm_farms;
        CREATE DATABASE IF NOT EXISTS geofarm_iot;
        CREATE DATABASE IF NOT EXISTS geofarm_geochat;
    "
    
    # Run initialization script
    docker-compose -f $COMPOSE_FILE exec postgres psql -U postgres -d geofarm_main -f /docker-entrypoint-initdb.d/init-db.sql
    
    print_success "Database migrations completed"
}

# Function to start application services
start_services() {
    print_status "Starting application services..."
    
    # Start all services
    if [ "$VERBOSE" = true ]; then
        docker-compose -f $COMPOSE_FILE up -d
    else
        docker-compose -f $COMPOSE_FILE up -d --quiet-pull
    fi
    
    print_success "Application services started"
}

# Function to check service health
check_health() {
    print_status "Checking service health..."
    
    # Wait for services to start
    sleep 15
    
    # Check each service
    services=("api-gateway" "user-service" "notification-service" "weather-service" "crop-detection-service" "recommendation-service" "farm-service")
    
    for service in "${services[@]}"; do
        if docker-compose -f $COMPOSE_FILE ps $service | grep -q "Up"; then
            print_success "$service is running"
        else
            print_error "$service is not running"
            docker-compose -f $COMPOSE_FILE logs $service
        fi
    done
}

# Function to show service status
show_status() {
    print_status "Service Status:"
    docker-compose -f $COMPOSE_FILE ps
}

# Function to show logs
show_logs() {
    print_status "Showing logs..."
    docker-compose -f $COMPOSE_FILE logs -f
}

# Function to stop services
stop_services() {
    print_status "Stopping services..."
    docker-compose -f $COMPOSE_FILE down
    print_success "Services stopped"
}

# Function to clean up
cleanup() {
    print_status "Cleaning up..."
    docker-compose -f $COMPOSE_FILE down -v --remove-orphans
    docker system prune -f
    print_success "Cleanup completed"
}

# Function to backup data
backup_data() {
    print_status "Creating backup..."
    
    BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p $BACKUP_DIR
    
    # Backup database
    docker-compose -f $COMPOSE_FILE exec postgres pg_dump -U postgres geofarm_main > $BACKUP_DIR/database.sql
    
    # Backup uploads
    if [ -d ./uploads ]; then
        tar -czf $BACKUP_DIR/uploads.tar.gz ./uploads
    fi
    
    # Backup configuration
    cp .env $BACKUP_DIR/
    cp docker-compose.yml $BACKUP_DIR/
    
    print_success "Backup created at $BACKUP_DIR"
}

# Function to restore data
restore_data() {
    if [ -z "$1" ]; then
        print_error "Please provide backup directory path"
        exit 1
    fi
    
    BACKUP_DIR="$1"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        print_error "Backup directory not found"
        exit 1
    fi
    
    print_status "Restoring from backup..."
    
    # Stop services
    docker-compose -f $COMPOSE_FILE down
    
    # Restore database
    if [ -f "$BACKUP_DIR/database.sql" ]; then
        docker-compose -f $COMPOSE_FILE up -d postgres
        sleep 10
        docker-compose -f $COMPOSE_FILE exec -T postgres psql -U postgres -d geofarm_main < "$BACKUP_DIR/database.sql"
    fi
    
    # Restore uploads
    if [ -f "$BACKUP_DIR/uploads.tar.gz" ]; then
        tar -xzf "$BACKUP_DIR/uploads.tar.gz"
    fi
    
    # Restore configuration
    if [ -f "$BACKUP_DIR/.env" ]; then
        cp "$BACKUP_DIR/.env" .
    fi
    
    print_success "Restore completed"
}

# Function to update services
update_services() {
    print_status "Updating services..."
    
    # Pull latest images
    docker-compose -f $COMPOSE_FILE pull
    
    # Rebuild local images
    build_images
    
    # Restart services
    docker-compose -f $COMPOSE_FILE up -d
    
    print_success "Services updated"
}

# Function to monitor services
monitor_services() {
    print_status "Monitoring services (Press Ctrl+C to exit)..."
    
    while true; do
        clear
        echo "=== GeoFarm Platform Monitor ==="
        echo "Timestamp: $(date)"
        echo ""
        
        # Show service status
        docker-compose -f $COMPOSE_FILE ps
        
        # Show resource usage
        echo ""
        echo "=== Resource Usage ==="
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"
        
        # Show database size
        echo ""
        echo "=== Database Size ==="
        docker-compose -f $COMPOSE_FILE exec postgres psql -U postgres -c "
            SELECT datname, pg_size_pretty(pg_database_size(datname)) 
            FROM pg_database 
            WHERE datname LIKE 'geofarm_%';
        " 2>/dev/null || echo "Database not available"
        
        sleep 30
    done
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -f|--compose-file)
            COMPOSE_FILE="$2"
            shift 2
            ;;
        -s|--skip-build)
            SKIP_BUILD=true
            shift
            ;;
        -m|--skip-migrations)
            SKIP_MIGRATIONS=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        start)
            COMMAND="start"
            shift
            ;;
        stop)
            COMMAND="stop"
            shift
            ;;
        restart)
            COMMAND="restart"
            shift
            ;;
        status)
            COMMAND="status"
            shift
            ;;
        logs)
            COMMAND="logs"
            shift
            ;;
        backup)
            COMMAND="backup"
            shift
            ;;
        restore)
            COMMAND="restore"
            BACKUP_DIR="$2"
            shift 2
            ;;
        update)
            COMMAND="update"
            shift
            ;;
        monitor)
            COMMAND="monitor"
            shift
            ;;
        cleanup)
            COMMAND="cleanup"
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
case $COMMAND in
    start)
        check_prerequisites
        load_environment
        build_images
        start_infrastructure
        run_migrations
        start_services
        check_health
        show_status
        print_success "GeoFarm Platform started successfully!"
        print_status "API Gateway: http://localhost:3000"
        print_status "API Documentation: http://localhost:3000/api-docs"
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        sleep 5
        check_prerequisites
        load_environment
        start_services
        check_health
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    backup)
        backup_data
        ;;
    restore)
        restore_data "$BACKUP_DIR"
        ;;
    update)
        update_services
        ;;
    monitor)
        monitor_services
        ;;
    cleanup)
        cleanup
        ;;
    *)
        show_usage
        exit 1
        ;;
esac