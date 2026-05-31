# Makefile gets instructions from pipeline.yml.

# Ignore any files with these names on the disk and always run the commands associated with the targets.
# By default, Make compares timestamps between source files and output products to determine if it needs to run.
# .PHONY forces Make to skip that checking process and treat these as executable task labels instead.
.PHONY: build-docker-backend build-docker-frontend test lint clean deploy-docker-backend deploy-docker-frontend

# build-docker-backend: Packages the FastAPI backend application engine into an isolated Docker container.
# -f specifies the location of the backend blueprint file, while "." instructs Docker to gather files and subdirectories from the current directory and send them to the Docker daemon.
build-docker-backend:
	docker build -t councilconnect-backend:local -f docker/backend.Dockerfile .

# build-docker-frontend: Packages the resident-facing Streamlit user interface layer into a separate container.
# -f specifies the location of the frontend blueprint file, while "." instructs Docker to gather files and subdirectories from the current directory and send them to the Docker daemon.
build-docker-frontend:
	docker build -t councilconnect-frontend:local -f docker/frontend.Dockerfile .

# test: Runs the automated verification suite using pytest to validate system logic and mathematical rules.
# "--cov=app" measures code execution coverage for modules contained exclusively inside the app package.
# "--cov-report=term-missing" appends a "Missing" column to the workspace free of dead cache files.
test:
	python -m pytest tests/ --cov=app --cov=scraper --cov-report=term-missing --cov-fail-under=80
	rm -f knowledge_base/processed/*.json

# lint: Scans the codebase for styling anomalies, formatting errors, or structural anti-patterns using Flake8.
# Both "app/" and "scraper/" modules are explicitly passed to prevent scraping utilities from skipping validation.
# "--count" totals up all stylistic transgressions, while "--select=E9,F63,F7,F82" filters the output to only include critical errors that could lead to runtime failures or logical bugs.
# "--show-source" prints the offending line of code to the screen, and "--statistics" summaries the issues by categories.
lint:
	flake8 app/ scraper/ --count --select=E9,F63,F7,F82 --show-source --statistics

# clean: Comprehensive housekeeping sequence designed to reset the environment and reclaim host disk storage.
# The leading hyphens (-) inform Make to keep executing subsequent steps even if the preceding step returns an error code.
# The active testing containers ("council-backend-test" and "council-frontend-test") are wiped first before their reference tags are dropped.
# "docker system prune -f" flushes out any lingering multi-stage container build artifacts or dangling cache segments.
clean:
	-docker rm -f council-backend-test council-frontend-test 2>/dev/null || true
	-docker rmi councilconnect-backend:local councilconnect-frontend:local 2>/dev/null || true
	docker system prune -f

# deploy-docker-backend: Interactive deployment automation script restricted to the FastAPI backend microservice layer.
# Prompts for runtime tags and routing configuration weights before rebuilding the engine and managing push tracking loops.
deploy-docker-backend:
	@echo "====================================================================="
	@echo "COUNCILCONNECT-AI INTERACTIVE LOCAL BACKEND DEPLOYMENT UTILITY"
	@echo "====================================================================="
	@# Prompt for the target backend repository deployment tag string and safely strip out carriage returns
	@read -p "Enter target BACKEND image release tag version (e.g., b1.0.0): " RAW_BACKEND_TAG; \
	BACKEND_TAG=$$(echo "$$RAW_BACKEND_TAG" | tr -d '\r ' | tr -d '\n'); \
	if [ -z "$$BACKEND_TAG" ]; then \
		echo "ERROR: Backend deployment tag variable validation failed. Operation aborted."; \
		exit 1; \
	fi; \
	\
	# Prompt for the container ingress routing percentage weights \
	read -p "Enter traffic weight percentage allocation for the LATEST backend revision (0-100): " RAW_BACKEND_WEIGHT; \
	BACKEND_LATEST_WEIGHT=$$(echo "$$RAW_BACKEND_WEIGHT" | tr -d '\r ' | tr -d '\n'); \
	if [ -z "$$BACKEND_LATEST_WEIGHT" ]; then \
		echo "ERROR: Ingress percentage parameters cannot be left unassigned. Operation aborted."; \
		exit 1; \
	fi; \
	\
	# Step 1: Rebuild backend container source node using direct string target invocation to bypass windows shell path spacing bugs \
	echo "--> Rebuilding backend container image layer..."; \
	make build-docker-backend; \
	\
	# Step 2: Restructure local references to match the cloud repository workspace boundaries \
	echo "--> Executing backend environment tag mapping adjustments for tag: $$BACKEND_TAG..."; \
	docker tag councilconnect-backend:local acrcouncilconnectai.azurecr.io/councilconnect-backend:$$BACKEND_TAG; \
	\
	# Step 3: Authenticate secure sessions linking local daemons with the remote Azure Container Registry cluster \
	echo "--> Requesting connection tokens from Azure Container Registry..."; \
	az acr login --name acrcouncilconnectai; \
	\
	# Step 4: Transmit the updated binary blob across network layers out to storage pools \
	echo "--> Uploading backend image structure to remote storage repository..."; \
	docker push acrcouncilconnectai.azurecr.io/councilconnect-backend:$$BACKEND_TAG; \
	\
	# Step 5: Provision service modifications targeting the active Azure Container App backend instance \
	echo "--> Synchronising target image configuration to Backend Container App instance..."; \
	az containerapp update \
		--name app-councilconnect-ai \
		--resource-group rg-councilconnect-ai \
		--image acrcouncilconnectai.azurecr.io/councilconnect-backend:$$BACKEND_TAG; \
	\
	# Step 6: Recalibrate network ingress load-balancer distributions across tracking configurations \
	echo "--> Adjusting live routing weight distributions for backend ingress pathways to latest=$$BACKEND_LATEST_WEIGHT..."; \
	az containerapp ingress traffic set \
		--name app-councilconnect-ai \
		--resource-group rg-councilconnect-ai \
		--revision-weight latest=$$BACKEND_LATEST_WEIGHT; \
	\
	echo "====================================================================="; \
	echo "Backend deployment successfully concluded for release version: $$BACKEND_TAG"; \
	echo "====================================================================="

# deploy-docker-frontend: Interactive deployment automation script restricted to the Streamlit UI presentation layer.
# Prompts for runtime tags and routing configuration weights before rebuilding the interface and managing push tracking loops.
deploy-docker-frontend:
	@echo "====================================================================="
	@echo "COUNCILCONNECT-AI INTERACTIVE LOCAL FRONTEND DEPLOYMENT UTILITY"
	@echo "====================================================================="
	@# Prompt for the target frontend repository deployment tag string and safely strip out carriage returns
	@read -p "Enter target FRONTEND image release tag version (e.g., f1.0.0): " RAW_FRONTEND_TAG; \
	FRONTEND_TAG=$$(echo "$$RAW_FRONTEND_TAG" | tr -d '\r ' | tr -d '\n'); \
	if [ -z "$$FRONTEND_TAG" ]; then \
		echo "ERROR: Frontend deployment tag variable validation failed. Operation aborted."; \
		exit 1; \
	fi; \
	\
	# Prompt for the container ingress routing percentage weights \
	read -p "Enter traffic weight percentage allocation for the LATEST frontend revision (0-100): " RAW_FRONTEND_WEIGHT; \
	FRONTEND_LATEST_WEIGHT=$$(echo "$$RAW_FRONTEND_WEIGHT" | tr -d '\r ' | tr -cd '[:digit:]'); \
	if [ -z "$$FRONTEND_LATEST_WEIGHT" ]; then \
		echo "ERROR: Ingress percentage parameters cannot be left unassigned. Operation aborted."; \
		exit 1; \
	fi; \
	\
	# Step 1: Rebuild frontend container source node using direct string target invocation to bypass windows shell path spacing bugs \
	echo "--> Rebuilding frontend container image layer..."; \
	make build-docker-frontend; \
	\
	# Step 2: Restructure local references to match the cloud repository workspace boundaries \
	echo "--> Executing frontend environment tag mapping adjustments for tag: $$FRONTEND_TAG..."; \
	docker tag councilconnect-frontend:local acrcouncilconnectai.azurecr.io/councilconnect-frontend:$$FRONTEND_TAG; \
	\
	# Step 3: Authenticate secure sessions linking local daemons with the remote Azure Container Registry cluster \
	echo "--> Requesting connection tokens from Azure Container Registry..."; \
	az acr login --name acrcouncilconnectai; \
	\
	# Step 4: Transmit the updated binary blob across network layers out to storage pools \
	echo "--> Uploading frontend image structure to remote storage repository..."; \
	docker push acrcouncilconnectai.azurecr.io/councilconnect-frontend:$$FRONTEND_TAG; \
	\
	# Step 5: Provision service modifications targeting the active Azure Container App frontend instance \
	echo "--> Synchronising target image configuration to Frontend Container App instance..."; \
	az containerapp update \
		--name ui-councilconnect-ai \
		--resource-group rg-councilconnect-ai \
		--image acrcouncilconnectai.azurecr.io/councilconnect-frontend:$$FRONTEND_TAG; \
	\
	# Step 6: Recalibrate network ingress load-balancer distributions across tracking configurations \
	echo "--> Adjusting live routing weight distributions for frontend ingress pathways to latest=$$FRONTEND_LATEST_WEIGHT..."; \
	az containerapp ingress traffic set \
		--name ui-councilconnect-ai \
		--resource-group rg-councilconnect-ai \
		--revision-weight latest=$$FRONTEND_LATEST_WEIGHT; \
	\
	echo "====================================================================="; \
	echo "Frontend deployment successfully concluded for release version: $$FRONTEND_TAG"; \
	echo "====================================================================="