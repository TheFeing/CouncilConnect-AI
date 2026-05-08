FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging for DevOps visibility
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies for networking checks
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
RUN pip install --no-cache-dir streamlit requests

# Copy source code
COPY . .

# Streamlit default port
EXPOSE 8501

# Health check logic for Container App readiness (K11)
# Verifies the internal Streamlit health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]