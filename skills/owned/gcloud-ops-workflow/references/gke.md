# GKE

## Cluster Context

```bash
gcloud container clusters list --project <project> --region <region>
gcloud container clusters get-credentials <cluster> --project <project> --region <region>
kubectl config current-context
```

Use `--zone <zone>` instead of `--region <region>` for zonal clusters.

## Namespace And Workload Checks

```bash
kubectl get ns
kubectl get deploy,sts,svc,ingress,hpa -n <namespace>
kubectl get pods -n <namespace> -o wide
kubectl describe deploy <deployment> -n <namespace>
kubectl describe pod <pod> -n <namespace>
kubectl logs <pod> -n <namespace> --tail=200
kubectl get events -n <namespace> --sort-by=.lastTimestamp
```

## KEDA And Autoscaling

```bash
kubectl get scaledobjects,kedahttp_scaledobjects -A
kubectl describe scaledobject <name> -n <namespace>
kubectl get hpa -n <namespace>
```

## What To Capture

- cluster, namespace, deployment, pod names;
- image tags and restart counts;
- service account names;
- events and failing pod reasons;
- mounted PVC/NFS names;
- KEDA/HPA status.

Do not store secret values from `Secret` objects. Listing secret names is acceptable when needed.

