# Makefile gets instructions from cicd.yml.

# Ignore any files with this name on the disk and always run the commands associated with this target.
# By default, Make compares the timestamps (products vs dependencies) to determine if it needs to run the commands.
.PHONY: build test lint clean

# build: Packages the Python application into a Docker container.
# Why? This "freezes" the app with its dependencies so it never breaks due to system updates.
build:
	docker build -t council-connect-app ./app

# test: Runs the automated test suite using Pytest.
# Why? To prove the code works as expected before it is sent to the "production" branch.
test:
	pytest tests/ --cov=app --cov-report=term-missing

# lint: Scans the code for formatting errors or "bad smells" using Flake8.
# Why? It enforces professional coding standards (PEP8) automatically, ensuring readability.
lint:
	flake8 app/ scraper/ --count --select=E9,F63,F7,F82 --show-source --statistics

# clean: Housekeeping command to delete old Docker files.
# Why? To prevent the workstation or Codespace from running out of disk space during repeated builds.
clean:
	docker system prune -f