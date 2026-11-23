#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
LOGS="$ROOT/artifacts/logs"
RESULTS="$ROOT/artifacts/results"
mkdir -p "$LOGS" "$RESULTS"

capture() {
  local name=$1
  shift
  { printf '$'; printf ' %q' "$@"; printf '\n'; "$@"; } >"$LOGS/$name" 2>&1
}

capture 00-cluster-info.log kubectl cluster-info
capture 01-nodes.log kubectl get nodes -o wide

kubectl apply -f "$ROOT/k8s/00-base.yaml" >"$LOGS/02-base-apply.log" 2>&1
kubectl apply -f "$ROOT/k8s/01-rustfs.yaml" >"$LOGS/03-rustfs-apply.log" 2>&1
kubectl -n lab5 rollout status statefulset/rustfs --timeout=240s >>"$LOGS/03-rustfs-apply.log" 2>&1

kubectl -n lab5 delete job upload-dataset --ignore-not-found >/dev/null
kubectl apply -f "$ROOT/k8s/02-upload-job.yaml" >"$LOGS/04-upload.log" 2>&1
kubectl -n lab5 wait --for=condition=complete job/upload-dataset --timeout=180s >>"$LOGS/04-upload.log" 2>&1
kubectl -n lab5 logs job/upload-dataset >>"$LOGS/04-upload.log" 2>&1

kubectl -n lab5 delete job pairs-baseline --ignore-not-found >/dev/null
kubectl apply -f "$ROOT/k8s/03-baseline-job.yaml" >"$LOGS/05-baseline.log" 2>&1
kubectl -n lab5 wait --for=condition=complete job/pairs-baseline --timeout=180s >>"$LOGS/05-baseline.log" 2>&1
kubectl -n lab5 logs job/pairs-baseline >>"$LOGS/05-baseline.log" 2>&1

kubectl -n lab5 delete job pairs-oom --ignore-not-found >/dev/null
kubectl apply -f "$ROOT/k8s/04-oom-job.yaml" >"$LOGS/06-oom.log" 2>&1
set +e
kubectl -n lab5 wait --for=condition=failed job/pairs-oom --timeout=120s >>"$LOGS/06-oom.log" 2>&1
set -e
kubectl -n lab5 get pod -l job-name=pairs-oom -o jsonpath='{range .items[*]}pod={.metadata.name}{"\n"}phase={.status.phase}{"\n"}reason={.status.containerStatuses[0].state.terminated.reason}{"\n"}exitCode={.status.containerStatuses[0].state.terminated.exitCode}{"\n"}{end}' >>"$LOGS/06-oom.log" 2>&1
kubectl -n lab5 describe pod -l job-name=pairs-oom >>"$LOGS/06-oom.log" 2>&1

kubectl -n lab5 delete job pairs-selected-limit --ignore-not-found >/dev/null
kubectl apply -f "$ROOT/k8s/05-selected-limit-job.yaml" >"$LOGS/07-selected-limit.log" 2>&1
kubectl -n lab5 wait --for=condition=complete job/pairs-selected-limit --timeout=180s >>"$LOGS/07-selected-limit.log" 2>&1
kubectl -n lab5 logs job/pairs-selected-limit >>"$LOGS/07-selected-limit.log" 2>&1

kubectl -n lab5 delete job pairs-map pairs-reduce --ignore-not-found >/dev/null
kubectl apply -f "$ROOT/k8s/06-parallel-job.yaml" >"$LOGS/08-parallel.log" 2>&1
kubectl -n lab5 wait --for=condition=complete job/pairs-map --timeout=240s >>"$LOGS/08-parallel.log" 2>&1
kubectl -n lab5 logs -l job-name=pairs-map --prefix=true >>"$LOGS/08-parallel.log" 2>&1
kubectl apply -f "$ROOT/k8s/07-reducer-job.yaml" >>"$LOGS/08-parallel.log" 2>&1
kubectl -n lab5 wait --for=condition=complete job/pairs-reduce --timeout=180s >>"$LOGS/08-parallel.log" 2>&1
kubectl -n lab5 logs job/pairs-reduce | tee -a "$LOGS/08-parallel.log" >"$RESULTS/parallel-top10.json"

for manifest in 08c-cpu-high.yaml 08b-cpu-pending.yaml 08a-cpu-fillers.yaml; do
  kubectl delete -f "$ROOT/k8s/$manifest" --ignore-not-found >/dev/null 2>&1 || true
done
kubectl apply -f "$ROOT/k8s/08-priorities.yaml" >"$LOGS/09-scheduling-preemption.log" 2>&1
kubectl apply -f "$ROOT/k8s/08a-cpu-fillers.yaml" >>"$LOGS/09-scheduling-preemption.log" 2>&1
sleep 12
printf '\n--- CPU saturation before pending pod ---\n' >>"$LOGS/09-scheduling-preemption.log"
kubectl -n lab5 get pods -l app=cpu-filler --no-headers | awk '{count[$3]++} END{for (s in count) print s, count[s]}' | sort >>"$LOGS/09-scheduling-preemption.log"
kubectl apply -f "$ROOT/k8s/08b-cpu-pending.yaml" >>"$LOGS/09-scheduling-preemption.log" 2>&1
sleep 5
printf '\n--- Pending because CPU requests do not fit ---\n' >>"$LOGS/09-scheduling-preemption.log"
kubectl -n lab5 get pod cpu-pending -o wide >>"$LOGS/09-scheduling-preemption.log" 2>&1
kubectl -n lab5 describe pod cpu-pending >>"$LOGS/09-scheduling-preemption.log" 2>&1
kubectl apply -f "$ROOT/k8s/08c-cpu-high.yaml" >>"$LOGS/09-scheduling-preemption.log" 2>&1
kubectl -n lab5 wait --for=condition=Ready pod/cpu-high --timeout=90s >>"$LOGS/09-scheduling-preemption.log" 2>&1
sleep 5
printf '\n--- High-priority pod and preemption evidence ---\n' >>"$LOGS/09-scheduling-preemption.log"
kubectl -n lab5 get pod cpu-high -o wide >>"$LOGS/09-scheduling-preemption.log" 2>&1
kubectl -n lab5 describe pod cpu-high >>"$LOGS/09-scheduling-preemption.log" 2>&1
HIGH_UID=$(kubectl -n lab5 get pod cpu-high -o jsonpath='{.metadata.uid}')
kubectl -n lab5 get events --sort-by=.metadata.creationTimestamp | grep -E "cpu-(high|pending)|$HIGH_UID" >>"$LOGS/09-scheduling-preemption.log" 2>&1 || true
for manifest in 08c-cpu-high.yaml 08b-cpu-pending.yaml 08a-cpu-fillers.yaml; do
  kubectl delete -f "$ROOT/k8s/$manifest" --ignore-not-found >/dev/null 2>&1 || true
done

kubectl delete namespace lab5-quota --ignore-not-found --wait=true >/dev/null 2>&1 || true
sed '/^---$/,$d' "$ROOT/k8s/09-quota.yaml" | kubectl apply -f - >"$LOGS/10-quota.log" 2>&1
awk 'BEGIN{n=0} /^---$/{n++;next} n==1{print}' "$ROOT/k8s/09-quota.yaml" | kubectl apply -f - >>"$LOGS/10-quota.log" 2>&1
awk 'BEGIN{n=0} /^---$/{n++;next} n==2{print}' "$ROOT/k8s/09-quota.yaml" | kubectl apply -f - >>"$LOGS/10-quota.log" 2>&1
set +e
awk 'BEGIN{n=0} /^---$/{n++;next} n==3{print}' "$ROOT/k8s/09-quota.yaml" | kubectl apply -f - >>"$LOGS/10-quota.log" 2>&1
set -e
kubectl -n lab5-quota describe resourcequota compute-quota >>"$LOGS/10-quota.log" 2>&1

python3 "$ROOT/scripts/verify_top10.py" | tee "$LOGS/11-verification.log"
