# Blueprint for building frontend user interface Docker images.
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging for DevOps visibility.
ENV PYTHONTONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies for networking checks.
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements matching project base standards.
RUN pip install --no-cache-dir streamlit requests

# Copy only the isolated frontend folder contents into the working path.
COPY ./frontend /app

# Streamlit default port aligned with infrastructure ingress definitions.
EXPOSE 8501

# Health check logic for Container App readiness.
# Verifies the internal Streamlit health endpoint.
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]