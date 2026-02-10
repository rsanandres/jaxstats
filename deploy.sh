#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo "Error: Docker is not running"
        exit 1
    fi
}

# Function to check if kubectl is installed
check_kubectl() {
    if ! command_exists kubectl; then
        echo "Error: kubectl is not installed"
        exit 1
    fi
}

# Function to build Docker images
build_images() {
    echo "Building Docker images..."
    docker build -t jaxstats-backend:latest .
    docker build -t jaxstats-frontend:latest ./frontend
}

# Function to deploy with Docker Compose
deploy_docker_compose() {
    echo "Deploying with Docker Compose..."
    docker-compose up --build -d
    echo "Application is running at:"
    echo "Frontend: http://localhost"
    echo "Backend API: http://localhost:8000"
}

# Function to deploy to Kubernetes
deploy_kubernetes() {
    echo "Deploying to Kubernetes..."
    
    # Create namespace if it doesn't exist
    kubectl create namespace jaxstats --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply Kubernetes manifests
    kubectl apply -f k8s/deployment.yaml -n jaxstats
    
    # Wait for deployments to be ready
    echo "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/jaxstats-backend -n jaxstats
    kubectl wait --for=condition=available --timeout=300s deployment/jaxstats-frontend -n jaxstats
    
    # Get the LoadBalancer IP
    echo "Getting service information..."
    kubectl get svc jaxstats-frontend -n jaxstats
}

# Main script
echo "JaxStats Deployment Script"
echo "-------------------------"

# Check prerequisites
check_docker

# Build images
build_images

# Ask for deployment method
echo "Choose deployment method:"
echo "1) Docker Compose"
echo "2) Kubernetes"
read -p "Enter your choice (1 or 2): " choice

case $choice in
    1)
        deploy_docker_compose
        ;;
    2)
        check_kubectl
        deploy_kubernetes
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo "Deployment completed!" 