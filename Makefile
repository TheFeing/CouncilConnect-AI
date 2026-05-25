# Makefile gets instructions from pipeline.yml.

# Ignore any files with these names (e.g., build-backend) on the disk and always run the commands associated with the targets.
# By default, Make compares timestamps between source files and output products to determine if it needs to run.
# .PHONY forces Make to skip that checking process and treat these as executable task labels instead.
.PHONY: build-backend build-frontend test lint clean

# build-backend: Packages the FastAPI backend application engine into an isolated Docker container.
# -f specifies the location of the backend blueprint file, while "." instructs Docker to gather files and subdirectories from the current directory and send them to the Docker daemon.
build-backend:
	docker build -t councilconnect-backend:local -f docker/backend.Dockerfile .

# build-frontend: Packages the resident-facing Streamlit user interface layer into a separate container.
# -f specifies the location of the frontend blueprint file, while "." instructs Docker to gather files and subdirectories from the current directory and send them to the Docker daemon.
build-frontend:
	docker build -t councilconnect-frontend:local -f docker/frontend.Dockerfile .

# test: Runs the automated verification suite using pytest to validate system logic and mathematical rules.
# "--cov=app" measures code execution coverage for modules contained exclusively inside the app package.
# "--cov-report=term-missing" appends a "Missing" column to the console screen to highlight precisely which source code lines lack testing coverage.
# "--cov-fail-under=80" enforces a mandatory quality gate that instantly fails the build if the code testing metrics fall beneath 80%.
# The final line cleans up transient JSON test data objects to keep the workspace free of dead cache files.
test:
	python -m pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80
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