# kubectl 命令速查

## 上下文

```bash
kubectl config get-contexts
kubectl config use-context <context>
kubectl cluster-info
```

## 资源查看

```bash
kubectl get pods|deploy|svc|ns [-A]
kubectl describe <resource> <name>
kubectl logs <pod> [-f]
kubectl exec -it <pod> -- /bin/sh
```

## 部署

```bash
kubectl apply -f <file|dir>
kubectl delete -f <file>
kubectl rollout status deployment/<name>
kubectl rollout undo deployment/<name>
```

## 调试

```bash
kubectl port-forward <pod> <local>:<remote>
kubectl top pods|nodes
kubectl get events --sort-by='.lastTimestamp'
```

## 命名空间

```bash
kubectl create namespace <name>
kubectl -n <ns> get pods
```
