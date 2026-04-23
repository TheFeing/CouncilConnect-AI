# Blueprint for building Docker images, triggered by build in Makefile.

# ==============================================================================
# STAGE 1: THE BUILDER
# Temp environment: Compile/install dependencies without bloating the final image
# Resolves FromAsCasing warning by standardising keywords to uppercase.
# ==============================================================================
FROM python:3.11-slim AS builder1

# Create a temporary directory for the build process
WORKDIR /build_temp

# Copy the requirements file into the current WORKDIR (/build_temp) from root context
COPY requirements.txt .

# --user: Installs into a specific directory that is easy to copy later
# --no-cache-dir: Saves space by not storing the downloaded installer files
RUN pip install --user --no-cache-dir -r requirements.txt

# ==============================================================================
# STAGE 2: THE RUNTIME (Production Image)
# This stage starts fresh. It is the one that actually runs on the server.
# ==============================================================================
FROM python:3.11-slim AS runner1
WORKDIR /app

# Pull only necessary artefacts from the builder stage
# Specifically copies the .local directory where --user dependencies are stored
COPY --from=builder1 /root/.local /root/.local

# Copy local app folder into internal container path /app/app
COPY ./app /app/app

# Prepend current path so it can find the 'uvicorn' executable just copied
ENV PATH="/root/.local/bin:${PATH}"

# Prevents writing .pyc files; ensures container remains clean
ENV PYTHONDONTWRITEBYTECODE=1
# Disables logging buffer; errors are printed to the console instantly
ENV PYTHONUNBUFFERED=1

# Uses port 8000 for the app (Standard for FastAPI/Azure Container Apps)
EXPOSE 8000

# Entry point:
# Look in the 'app' folder -> main.py -> find the FastAPI object 'app_instance'
# 0.0.0.0: Listens to all network interfaces (required for container access)
CMD ["uvicorn", "app.main:app_instance", "--host", "0.0.0.0", "--port", "8000"]