#!/bin/bash

set -e

CLUSTER_NAME="corium-cluster"
IMAGE_NAME="jaxstats:latest"
SERVICE_NAME="jaxstats"
NAMESPACE="default"
PORT=8000

# 1. Build Docker image
echo "1. Building Docker image..."
docker build -t $IMAGE_NAME .

# 2. Load image into Kind cluster
echo "2. Loading image into Kind cluster..."
kind load docker-image $IMAGE_NAME --name $CLUSTER_NAME

# 3. Apply Kubernetes manifests
echo "3. Applying Kubernetes manifests..."
kubectl apply -f k8s-deployment.yaml
kubectl apply -f k8s-secret.yaml

# 4. Wait for pod to be ready
echo "4. Waiting for pod to be ready..."
kubectl wait --for=condition=ready pod -l app=$SERVICE_NAME --timeout=120s

# 5. Port-forward service to localhost:8000
echo "5. Port-forwarding service to localhost:$PORT"
kubectl port-forward service/$SERVICE_NAME $PORT:$PORT 