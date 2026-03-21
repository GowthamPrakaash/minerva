SHELL := /bin/bash
# Minerva Infrastructure Management
# Usage: 
#   make setup AWS_ACCESS_KEY_ID=xxx AWS_SECRET_ACCESS_KEY=yyy PULUMI_CONFIG_PASSPHRASE=zzz

# Load environment variables from .env
ENV_FILE := ../.env
ifneq ("$(wildcard $(ENV_FILE))","")
include $(ENV_FILE)
export $(shell sed 's/=.*//' $(ENV_FILE))
endif

# --- Configuration ---
export AWS_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY
AWS_REGION ?= us-east-1
export AWS_REGION
export AWS_DEFAULT_REGION := $(AWS_REGION)
PULUMI_STATE_BUCKET ?= s3://minerva-infra-state
STACK ?= dev

# Deployment Environment for shell commands and recipes
DEPLOY_ENV := AWS_ACCESS_KEY_ID=$(AWS_ACCESS_KEY_ID) \
              AWS_SECRET_ACCESS_KEY=$(AWS_SECRET_ACCESS_KEY) \
              AWS_REGION=$(AWS_REGION) \
              AWS_DEFAULT_REGION=$(AWS_REGION) \
              PULUMI_CONFIG_PASSPHRASE=$(PULUMI_CONFIG_PASSPHRASE)

# --- Secrets (should be passed at runtime or as env vars) ---
# AWS_ACCESS_KEY_ID ?= 
# AWS_SECRET_ACCESS_KEY ?= 
# PULUMI_CONFIG_PASSPHRASE ?= 

# --- Targets ---

.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make aws-config - Configure AWS CLI"
	@echo "  make login      - Login to Pulumi S3 backend"
	@echo "  make init       - Initialize Pulumi stack"
	@echo "  make deploy     - Deploy the infrastructure (pulumi up)"
	@echo "  make setup      - Run all steps (config -> login -> init -> deploy)"

.PHONY: aws-config
aws-config:
	@echo "Setting up AWS configuration..."
	@$(DEPLOY_ENV) aws configure set aws_access_key_id $(AWS_ACCESS_KEY_ID)
	@$(DEPLOY_ENV) aws configure set aws_secret_access_key $(AWS_SECRET_ACCESS_KEY)
	@$(DEPLOY_ENV) aws configure set default.region $(AWS_REGION)

.PHONY: login
login:
	@echo "Logging into Pulumi backend: $(PULUMI_STATE_BUCKET)..."
	@$(DEPLOY_ENV) pulumi login $(PULUMI_STATE_BUCKET)

.PHONY: init
init: login
	@echo "Initializing stack: $(STACK)..."
	cd pulumi && ($(DEPLOY_ENV) pulumi stack init $(STACK) || echo "Stack already exists, proceeding...")

.PHONY: preview
preview: login
	@echo "Previewing infrastructure in stack: $(STACK)..."
	cd pulumi && $(DEPLOY_ENV) pulumi up --stack $(STACK)
	
.PHONY: deploy
deploy: login
	@echo "Deploying infrastructure to stack: $(STACK)..."
	cd pulumi && $(DEPLOY_ENV) pulumi up --yes --stack $(STACK)

.PHONY: setup
setup: aws-config init deploy
	@echo "Deployment complete."

.PHONY: destroy
destroy: login
	@echo "Destroying infrastructure for stack: $(STACK)..."
	cd pulumi && $(DEPLOY_ENV) pulumi destroy --yes --stack $(STACK)

.PHONY: delete-stack
delete-stack:
	@echo "Deleting stack: $(STACK)..."
	cd pulumi && $(DEPLOY_ENV) pulumi stack rm $(STACK) --yes

.PHONY: nuke-stack
nuke-stack: destroy delete-stack
	@echo "Nuking stack: $(STACK)..."

# --- Docker Push Commands ---

.PHONY: push-core
push-core: login
	@echo "Pushing Core Service to ECR..."
	$(eval CORE_REPO := $(shell cd pulumi && $(DEPLOY_ENV) pulumi stack output core_repo_url --stack $(STACK) 2>/dev/null))
	@if [ -z "$(CORE_REPO)" ]; then \
		echo "Error: core_repo_url not found in stack outputs. Have you run 'make deploy' yet?"; \
		exit 1; \
	fi
	@$(DEPLOY_ENV) aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(CORE_REPO) || \
		(echo "Error: AWS ECR login failed. Ensure your IAM user has 'ecr:GetAuthorizationToken' permissions."; exit 1)
	docker build -t $(CORE_REPO):latest -f docker/Dockerfile.core ..
	docker push $(CORE_REPO):latest

.PHONY: push-ingestion
push-ingestion: login
	@echo "Pushing Ingestion Worker to ECR..."
	$(eval INGESTION_REPO := $(shell cd pulumi && $(DEPLOY_ENV) pulumi stack output ingestion_repo_url --stack $(STACK) 2>/dev/null))
	@if [ -z "$(INGESTION_REPO)" ]; then \
		echo "Error: ingestion_repo_url not found in stack outputs. Have you run 'make deploy' yet?"; \
		exit 1; \
	fi
	@$(DEPLOY_ENV) aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(INGESTION_REPO) || \
		(echo "Error: AWS ECR login failed. Ensure your IAM user has 'ecr:GetAuthorizationToken' permissions."; exit 1)
	docker build -t $(INGESTION_REPO):latest -f docker/Dockerfile.ingestion ..
	docker push $(INGESTION_REPO):latest

.PHONY: push
push: push-core push-ingestion
	@echo "All services pushed to ECR."
