#!/bin/bash

set -e

CLUSTER_NAME="corium-cluster"
IMAGE_NAME="jaxstats:latest"
SERVICE_NAME="jaxstats"
NAMESPACE="default"
PORT=8000

# Function to clean up old resources
cleanup() {
    echo "Cleaning up old resources..."
    kubectl delete -f $(dirname "$0")/k8s-deployment.yaml --ignore-not-found=true
    kubectl delete -f $(dirname "$0")/k8s-secret.yaml --ignore-not-found=true
    docker rmi $IMAGE_NAME --force 2>/dev/null || true
}

# Function to check pod status
check_pod_status() {
    echo "Checking pod status..."
    kubectl get pods -l app=$SERVICE_NAME
    echo "Pod events:"
    kubectl describe pod -l app=$SERVICE_NAME
}

# Clean up before starting
cleanup

# 1. Build Docker image with optimized layers
echo "1. Building Docker image..."
docker build --no-cache -t $IMAGE_NAME .

# 2. Load image into Kind cluster with retry logic
echo "2. Loading image into Kind cluster..."
MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if kind load docker-image $IMAGE_NAME --name $CLUSTER_NAME; then
        echo "Successfully loaded image into Kind cluster"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
            echo "Failed to load image after $MAX_RETRIES attempts"
            exit 1
        fi
        echo "Retrying image load (attempt $RETRY_COUNT of $MAX_RETRIES)..."
        sleep 5
    fi
done

# 3. Apply Kubernetes manifests
echo "3. Applying Kubernetes manifests..."
kubectl apply -f $(dirname "$0")/k8s-deployment.yaml
kubectl apply -f $(dirname "$0")/k8s-secret.yaml

# 4. Wait for pod to be ready with better error handling
echo "4. Waiting for pod to be ready..."
if ! kubectl wait --for=condition=ready pod -l app=$SERVICE_NAME --timeout=120s; then
    echo "Pod failed to become ready. Checking status..."
    check_pod_status
    
    # Check if it's an ImagePullBackOff issue
    if kubectl get pods -l app=$SERVICE_NAME | grep -q "ImagePullBackOff"; then
        echo "Detected ImagePullBackOff. Attempting to fix..."
        
        # Delete the pod to force a new pull
        kubectl delete pod -l app=$SERVICE_NAME
        
        # Wait again
        echo "Waiting for pod to be ready after retry..."
        if ! kubectl wait --for=condition=ready pod -l app=$SERVICE_NAME --timeout=120s; then
            echo "Pod still failed to become ready after retry."
            check_pod_status
            exit 1
        fi
    else
        exit 1
    fi
fi

# 5. Port-forward service to localhost:8000
echo "5. Port-forwarding service to localhost:$PORT"
kubectl port-forward service/$SERVICE_NAME $PORT:$PORT 