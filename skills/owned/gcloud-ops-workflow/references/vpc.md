# VPC

## Read-Only Checks

```bash
gcloud compute networks list --project <project>
gcloud compute networks subnets list --project <project>
gcloud compute firewall-rules list --project <project>
gcloud compute routes list --project <project>
gcloud compute routers list --project <project> --regions <region>
gcloud compute routers nats list --router <router> --region <region> --project <project>
gcloud compute networks vpc-access connectors list --region <region> --project <project>
```

## What To Capture

- network and subnet names;
- region and CIDR ranges;
- firewall rule names, direction, target tags/service accounts, allowed ports;
- route names and next hops;
- NAT router names;
- Serverless VPC Access connector names.

## Common Diagnoses

- Cloud Run cannot reach private resource: check VPC connector, subnet, firewall, routes, Cloud SQL private IP.
- GKE egress fails: check NAT, routes, node service account, firewall egress.
- Cloud SQL private connection fails: check VPC peering/private services access and subnet routing.

Do not create, update, or delete firewall/NAT/route resources without a written plan and approval.

