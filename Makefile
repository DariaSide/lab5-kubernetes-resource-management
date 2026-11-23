SHELL := /bin/bash
KIND ?= .tools/kind
CLUSTER ?= lab5
IMAGE ?= skill-pairs:lab5

.PHONY: cluster image storage upload baseline oom selected parallel scheduling quota verify report clean

cluster:
	$(KIND) create cluster --name $(CLUSTER) --config kind-config.yaml

image:
	docker build -t $(IMAGE) .
	$(KIND) load docker-image $(IMAGE) --name $(CLUSTER)

storage:
	kubectl apply -f k8s/00-base.yaml
	kubectl apply -f k8s/01-rustfs.yaml
	kubectl -n lab5 rollout status statefulset/rustfs --timeout=240s

upload:
	-kubectl -n lab5 delete job upload-dataset --ignore-not-found
	kubectl apply -f k8s/02-upload-job.yaml
	kubectl -n lab5 wait --for=condition=complete job/upload-dataset --timeout=180s

baseline:
	-kubectl -n lab5 delete job pairs-baseline --ignore-not-found
	kubectl apply -f k8s/03-baseline-job.yaml
	kubectl -n lab5 wait --for=condition=complete job/pairs-baseline --timeout=180s

oom:
	-kubectl -n lab5 delete job pairs-oom --ignore-not-found
	kubectl apply -f k8s/04-oom-job.yaml
	! kubectl -n lab5 wait --for=condition=complete job/pairs-oom --timeout=90s

selected:
	-kubectl -n lab5 delete job pairs-selected-limit --ignore-not-found
	kubectl apply -f k8s/05-selected-limit-job.yaml
	kubectl -n lab5 wait --for=condition=complete job/pairs-selected-limit --timeout=180s

parallel:
	-kubectl -n lab5 delete job pairs-map pairs-reduce --ignore-not-found
	kubectl apply -f k8s/06-parallel-job.yaml
	kubectl -n lab5 wait --for=condition=complete job/pairs-map --timeout=240s
	kubectl apply -f k8s/07-reducer-job.yaml
	kubectl -n lab5 wait --for=condition=complete job/pairs-reduce --timeout=180s

verify:
	python3 scripts/verify_top10.py

report:
	python3 report/build_report.py

clean:
	-$(KIND) delete cluster --name $(CLUSTER)
