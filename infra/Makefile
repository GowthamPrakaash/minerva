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
AWS_REGION ?= us-east-1
PULUMI_STATE_BUCKET ?= s3://minerva-infra-state
STACK ?= qa

# Secrets (should be passed at runtime or as env vars)
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
	@aws configure set aws_access_key_id $(AWS_ACCESS_KEY_ID)
	@aws configure set aws_secret_access_key $(AWS_SECRET_ACCESS_KEY)
	@aws configure set default.region $(AWS_REGION)

.PHONY: login
login:
	@echo "Logging into Pulumi backend: $(PULUMI_STATE_BUCKET)..."
	@pulumi login $(PULUMI_STATE_BUCKET)

.PHONY: init
init: login
	@echo "Initializing stack: $(STACK)..."
	@set -a; source .env; set +a;
	cd pulumi && (pulumi stack init $(STACK) || echo "Stack already exists, proceeding...")

.PHONY: preview
preview: login
	@echo "Previewing infrastructure in stack: $(STACK)..."
	@echo "Passphrase: $(PULUMI_CONFIG_PASSPHRASE)"
	@set -a; source .env; set +a;
	cd pulumi && pulumi up --stack $(STACK)
	
.PHONY: deploy
deploy: login
	@echo "Deploying infrastructure to stack: $(STACK)..."
	@set -a; source .env; set +a;
	cd pulumi && pulumi up --yes --stack $(STACK)

.PHONY: setup
setup: aws-config init deploy
	@echo "Deployment complete."

.PHONY: destroy
destroy: login
	@echo "Destroying infrastructure for stack: $(STACK)..."
	@set -a; source ../.env; set +a;
	cd pulumi && pulumi destroy --yes --stack $(STACK)

.PHONY: delete-stack
delete-stack:
	@echo "Deleting stack: $(STACK)..."
	@set -a; source ../.env; set +a;
	cd pulumi && pulumi stack rm $(STACK) --yes

.PHONY: nuke-stack
nuke-stack: destroy delete-stack
	@echo "Nuking stack: $(STACK)..."
	
