# Deploying JaxStats Locally with Kubernetes (KinD)

This guide explains how to run the JaxStats FastAPI app locally using Kubernetes with KinD (Kubernetes in Docker).

---

## 1. Prerequisites

- **Docker Desktop** installed and running ([Download here](https://www.docker.com/products/docker-desktop/))
- **kubectl** installed ([Install guide](https://kubernetes.io/docs/tasks/tools/))
- **KinD** installed ([Install guide](https://kind.sigs.k8s.io/docs/user/quick-start/#installation))

Check installation:
```sh
docker --version
kubectl version --client
kind --version
```

---

## 2. Build the Docker Image

From the project root:
```sh
docker build -t jaxstats:local ./jaxstats
```

---

## 3. Create a KinD Cluster

```sh
kind create cluster --name jaxstats-local
```

---

## 4. Load the Docker Image into KinD

```sh
kind load docker-image jaxstats:local --name jaxstats-local
```

---

## 5. Set Up Your Riot API Key

Edit `jaxstats/k8s-secret.yaml` and replace `REPLACE_WITH_YOUR_API_KEY` with your actual Riot API key.

---

## 6. Deploy to Kubernetes

```sh
kubectl apply -f jaxstats/k8s-secret.yaml
kubectl apply -f jaxstats/k8s-deployment.yaml
```

---

## 7. Access the App

Open your browser to:  
[http://localhost:30080](http://localhost:30080)

---

## 8. Clean Up

To delete the cluster:
```sh
kind delete cluster --name jaxstats-local
```

---

## 9. Troubleshooting

- If you change your code, rebuild the Docker image and reload it into KinD.
- Check pod logs with:
  ```sh
  kubectl get pods
  kubectl logs <pod-name>
  ``` 