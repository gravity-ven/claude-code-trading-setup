#!/bin/bash

# Simple script to manage the Spartan Research Station (Native)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PID_FILE="spartan_app.pid"
LOG_FILE="spartan_app.log"
HOST="0.0.0.0"
PORT="8888"
WORKERS="4"

# Print colored message
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Start the application
start() {
    if [ -f "$PID_FILE" ]; then
        print_error "Application is already running (PID: $(cat $PID_FILE))."
        exit 1
    fi

    print_info "Starting Spartan Research Station..."
    
    # Start Gunicorn in the background
    gunicorn --workers $WORKERS --bind $HOST:$PORT app:app --daemon --pid $PID_FILE --access-logfile $LOG_FILE --error-logfile $LOG_FILE

    # Check if the process started successfully
    if [ -f "$PID_FILE" ]; then
        print_success "Application started successfully (PID: $(cat $PID_FILE))."
        echo -e "Web Interface:  http://localhost:$PORT"
        echo -e "Logs:           tail -f $LOG_FILE"
    else
        print_error "Failed to start the application. Check logs in '$LOG_FILE'."
    fi
}

# Stop the application
stop() {
    if [ ! -f "$PID_FILE" ]; then
        print_error "Application is not running."
        exit 1
    fi

    PID=$(cat $PID_FILE)
    print_info "Stopping application (PID: $PID)..."
    kill $PID

    # Wait for the process to stop
    sleep 2

    if ! ps -p $PID > /dev/null; then
        rm $PID_FILE
        print_success "Application stopped."
    else
        print_error "Failed to stop the application. Forcing quit..."
        kill -9 $PID
        rm $PID_FILE
        print_success "Application stopped forcefully."
    fi
}

# Restart the application
restart() {
    print_info "Restarting Spartan Research Station..."
    if [ -f "$PID_FILE" ]; then
        stop
    fi
    start
}

# Check application status
status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        if ps -p $PID > /dev/null; then
            print_success "Application is running (PID: $PID)."
        else
            print_error "PID file found, but process is not running. Cleaning up."
            rm $PID_FILE
        fi
    else
        print_info "Application is not running."
    fi
}


# Main script logic
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0
