# Makefile gets instructions from cicd.yml.

# Ignore any files with this name on the disk and always run the commands associated with this target.
# By default, Make compares the timestamps (products vs dependencies) to determine if it needs to run the commands.
.PHONY: build test lint clean

# build: Packages the Python application into a Docker container.
# Why? This "freezes" the app with its dependencies so it never breaks.
build:
	docker build -t council-connect-app .

# "PYTHONPATH=." is added to ensure app modules are discoverable by pytest as tests run from the project root.
# "--cov=app" measures code coverage for the app package only, ignoring tests and other files.
# "--cov-report=term-missing" adds column "Missing" to the terminal output, showing which lines of code are not covered by tests.
# "--cov-fail-under=80" enforces mandatory EPA quality gate.
test:
	PYTHONPATH=. pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80

# lint: Scans the code for formatting errors or "bad smells" using Flake8.
lint:
	flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics

# clean: Housekeeping command to delete old Docker files.
clean:
	-docker rm -f $$(docker ps -aq) 2>/dev/null || true
	-docker rmi council-connect-app 2>/dev/null || true
	docker system prune -f