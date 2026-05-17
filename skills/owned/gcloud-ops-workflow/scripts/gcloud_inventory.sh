#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  gcloud_inventory.sh --project PROJECT [--region REGION] [--zone ZONE] [--cluster CLUSTER] [--namespace NAMESPACE] [--wiki-root PATH] [--output PATH]

Read-only Google Cloud inventory for Cloud Run, GKE, Cloud Storage, VPC, Cloud SQL, and recent logs.
When --wiki-root is provided, writes raw/gcloud_inventory/<timestamp>-inventory.md and appends wiki/log.md.
USAGE
}

PROJECT=""
REGION=""
ZONE=""
CLUSTER=""
NAMESPACE="default"
WIKI_ROOT=""
OUTPUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) PROJECT="${2:-}"; shift 2 ;;
    --region) REGION="${2:-}"; shift 2 ;;
    --zone) ZONE="${2:-}"; shift 2 ;;
    --cluster) CLUSTER="${2:-}"; shift 2 ;;
    --namespace) NAMESPACE="${2:-}"; shift 2 ;;
    --wiki-root) WIKI_ROOT="${2:-}"; shift 2 ;;
    --output) OUTPUT="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$PROJECT" ]]; then
  echo "--project is required. Do not rely on ambient gcloud defaults." >&2
  exit 2
fi

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud is not installed or not on PATH." >&2
  exit 127
fi

TS="$(date -u +%Y-%m-%dT%H%M%SZ)"
if [[ -n "$WIKI_ROOT" && -z "$OUTPUT" ]]; then
  mkdir -p "$WIKI_ROOT/raw/gcloud_inventory"
  OUTPUT="$WIKI_ROOT/raw/gcloud_inventory/${TS}-inventory.md"
elif [[ -z "$OUTPUT" ]]; then
  OUTPUT="-"
fi

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

run_section() {
  local title="$1"
  shift
  {
    echo
    echo "## ${title}"
    echo
    echo '```bash'
    printf '%q ' "$@"
    echo
    echo '```'
    echo
    echo '```text'
    "$@" 2>&1 || true
    echo '```'
  } >>"$tmp"
}

{
  echo "# Gcloud Inventory"
  echo
  echo "## Metadata"
  echo "- captured_at: \`${TS}\`"
  echo "- project: \`${PROJECT}\`"
  echo "- region: \`${REGION:-unknown}\`"
  echo "- zone: \`${ZONE:-unknown}\`"
  echo "- cluster: \`${CLUSTER:-unknown}\`"
  echo "- namespace: \`${NAMESPACE}\`"
  echo
  echo "## Safety"
  echo "- Read-only inventory only."
  echo "- Secret values are not intentionally collected."
} >"$tmp"

run_section "Active gcloud account" gcloud auth list --filter=status:ACTIVE --format='value(account)'
run_section "Cloud Run services" gcloud run services list --project "$PROJECT" ${REGION:+--region "$REGION"} --format='table(metadata.name,status.url,status.latestReadyRevisionName)'
run_section "Cloud SQL instances" gcloud sql instances list --project "$PROJECT" --format='table(name,region,databaseVersion,state,connectionName)'
run_section "Cloud Storage buckets" gcloud storage buckets list --project "$PROJECT" --format='table(name,location,storageClass,uniformBucketLevelAccess)'
run_section "VPC networks" gcloud compute networks list --project "$PROJECT" --format='table(name,subnet_mode,routingConfig.routingMode)'
run_section "VPC subnets" gcloud compute networks subnets list --project "$PROJECT" --format='table(name,region,network,ipCidrRange,privateIpGoogleAccess)'
run_section "Firewall rules" gcloud compute firewall-rules list --project "$PROJECT" --format='table(name,network,direction,priority,disabled,targetTags.list():label=TARGET_TAGS,allowed[].map().firewall_rule().list():label=ALLOW)'
run_section "Routes" gcloud compute routes list --project "$PROJECT" --format='table(name,network,destRange,nextHopGateway,nextHopIp,nextHopInstance)'

if [[ -n "$REGION" ]]; then
  run_section "Serverless VPC connectors" gcloud compute networks vpc-access connectors list --project "$PROJECT" --region "$REGION" --format='table(name,network,ipCidrRange,state)'
fi

if [[ -n "$CLUSTER" ]]; then
  if [[ -n "$REGION" ]]; then
    run_section "GKE get credentials" gcloud container clusters get-credentials "$CLUSTER" --project "$PROJECT" --region "$REGION"
  elif [[ -n "$ZONE" ]]; then
    run_section "GKE get credentials" gcloud container clusters get-credentials "$CLUSTER" --project "$PROJECT" --zone "$ZONE"
  fi
fi

if command -v kubectl >/dev/null 2>&1; then
  run_section "Kubernetes context" kubectl config current-context
  run_section "Kubernetes workloads" kubectl get deploy,sts,svc,hpa -n "$NAMESPACE"
  run_section "Kubernetes pods" kubectl get pods -n "$NAMESPACE" -o wide
  run_section "Kubernetes events" kubectl get events -n "$NAMESPACE" --sort-by=.lastTimestamp
fi

if [[ -n "$REGION" ]]; then
  run_section "Recent Cloud Run errors" gcloud logging read 'resource.type="cloud_run_revision" AND severity>=ERROR' --project "$PROJECT" --freshness 2h --limit 30 --format='table(timestamp,resource.labels.service_name,severity,textPayload)'
fi

if [[ "$OUTPUT" == "-" ]]; then
  cat "$tmp"
else
  mkdir -p "$(dirname "$OUTPUT")"
  cp "$tmp" "$OUTPUT"
  echo "$OUTPUT"
fi

if [[ -n "$WIKI_ROOT" ]]; then
  rel="${OUTPUT#"$WIKI_ROOT/"}"
  if [[ -f "$WIKI_ROOT/wiki/log.md" ]]; then
    {
      echo
      echo "- $(date -u +%Y-%m-%dT%H:%M:%SZ) GCLOUD_INVENTORY"
      echo "  - sources:"
      echo "    - gcloud project ${PROJECT}"
      echo "  - updated:"
      echo "    - ${rel}"
      echo "    - wiki/log.md"
      echo "  - notes: Captured read-only gcloud inventory for project ${PROJECT}."
    } >>"$WIKI_ROOT/wiki/log.md"
  fi
fi

